import matplotlib.pyplot as plt
import glob
import os
import sys
import imageio
import numpy as np
import tensorflow as tf

# pip install tensorflow-rocm for amd gpus

# See if we have GPUs
gpus = tf.config.list_physical_devices('GPU')

if gpus:
    # Use all GPUs
    print("########## GPUs detected. Using MirroredStrategy. ##########")
    print(gpus)
    strategy = tf.distribute.MirroredStrategy()
else:
    # Use CPU
    print("########## No GPUs detected. Using CPU only. ##########")
    tf.config.set_visible_devices([], 'GPU')
    strategy = tf.distribute.get_strategy()  # Default strategy for single device


##################################
# Load Train and Validation Data #
##################################

base_dir = sys.argv[1]

npy_files = glob.glob(os.path.join(base_dir, 'ATWOOD*', '*.npy'))

print(npy_files)

window = 5
X = []  # features/input sequence/etc...
y = []  # label/output sequence/target/etc...
lengths = [0]

for npy_file in npy_files:
    print(npy_file)
    loaded_array = np.load(npy_file)  # Shape: (num_timesteps, ny, nx)
    print("\t", loaded_array.shape)
    if loaded_array.shape[0] != 100:  # Didn't finish simulation due to instabilities
        print('\tSIMULATION CRASHED.')
    if loaded_array.shape[0] > window:
        samples = loaded_array.shape[0] - window
        lengths.append(samples)
        print(f'\tENOUGH DATA TO CREATE {samples} SAMPLES')
        for i in range(samples):
            X.append(loaded_array[i:window+i, :, :])
            y.append(loaded_array[window+i, :, :])

X = np.stack(X, axis=0)  # Shape: (num_samples, num_timesteps, ny, nx) num_timesteps = window
y = np.stack(y, axis=0)  # Shape: (num_samples, ny, nx)

print(X.shape, y.shape)

# Need extra dimension 1 for grayscale for Tensorflow model to read properly
X = X[..., np.newaxis]  # Now shape is (num_samples, num_timesteps, ny, nx, 1)
y = y[..., np.newaxis]  # Now shape is (num_samples, ny, nx, 1)

print("\n\nFinal Samples:")
print("\tX(num_samples, num_timesteps, ny, nx, 1):", X.shape)
print("\ty(num_samples, ny, nx, 1):", y.shape)

#######################
# Deep Learning Model #
#######################
with strategy.scope():
    model = tf.keras.Sequential([

        # LSTM over time, with conv over space
        tf.keras.layers.ConvLSTM2D(
            filters=64,
            kernel_size=3,
            padding='same',
            return_sequences=False,    # only next 2d grid
            activation='relu',
            input_shape=(window, 64, 256, 1)
        ),

        # Small conv head to map hidden state to next grid
        tf.keras.layers.Conv2D(
            filters=32,  # how many feature maps
            kernel_size=3,
            padding='same',
            activation='relu'
        ),

        # Final conv layer to get final 2D Matrix prediction
        tf.keras.layers.Conv2D(
            filters=1,  # reduce feature maps from previous layer to 1 to get final image
            kernel_size=3,
            padding='same',
            activation='linear'  # final layer is linear since values can be negative
        )
    ])

    # Compile the model
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Create callbacks
callbacks = [
    tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),  # In case val loss is stagnant
    tf.keras.callbacks.BackupAndRestore(backup_dir='./backup'),  # In case it crashes saves more than just model and weights so we can resume training
    tf.keras.callbacks.ModelCheckpoint(filepath='./checkpoints/model_epoch_{epoch:02d}_val_loss_{val_loss:.2f}.keras'),  # Saves model and weights to load best model for model.predict()
    tf.keras.callbacks.TensorBoard(histogram_freq=1, write_images=True, write_steps_per_second=True, embeddings_freq=1)
]

logdir = "./logs/profile"
# tf.profiler.experimental.start(logdir)
# Train the model
history = model.fit(X, y,
                    epochs=10,
                    batch_size=4,
                    validation_split=0.2,
                    callbacks=callbacks)
# tf.profiler.experimental.stop()

model_path = os.path.join('my_model.keras')

# Save Model
model.save(model_path)

# Load Model
# model = tf.keras.models.load_model(model_path)

#############
# Inference #
#############
levels = 20


def predict_and_plot(X, y, out_dir, autoregressive=False,):

    os.makedirs(out_dir, exist_ok=True)

    mses = []
    frames = []

    for i in range(X.shape[0]):  # cycle through samples
        print(f"Predicting Sample {i+1} of {X.shape[0]}")

        if autoregressive and i != 0:
            new_sequence = np.concatenate(
                [new_sequence[:, 1:, ...], predicted_frame[:, np.newaxis, ...]],
                axis=1
            )
        else:
            new_sequence = np.expand_dims(X[i], 0)  # Shape: (1, 5, 64, 256, 1)

        predicted_frame = model.predict(new_sequence)  # Shape: (1, 64, 256, 1)
        predicted_image = predicted_frame[0, ..., 0]  # Shape: (64, 256)

        pred = predicted_image
        obs = y[i][..., 0]
        diff = obs - pred
        mse = np.mean(np.ravel(diff ** 2))
        mses.append(mse)

        # Common scale for predicted and observed
        vmin_main = np.min([pred.min(), obs.min()])
        vmax_main = np.max([pred.max(), obs.max()])

        # Symmetric scale for difference
        max_abs_diff = np.max(np.abs(diff))

        fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(10, 9))
        fig.suptitle(f"Predicting Sample {i+1} of {X.shape[0]}")

        # Observed
        contour0 = ax[0].contourf(obs, levels=levels, cmap='viridis',
                                  vmin=vmin_main, vmax=vmax_main)
        ax[0].set_title('Observed Frame')
        ax[0].axis('off')

        # Predicted
        contour1 = ax[1].contourf(pred, levels=levels, cmap='viridis',
                                  vmin=vmin_main, vmax=vmax_main)
        ax[1].set_title('Predicted Frame')
        ax[1].axis('off')

        # Difference
        contour2 = ax[2].contourf(diff, levels=levels, cmap='seismic',
                                  vmin=-max_abs_diff, vmax=max_abs_diff)
        ax[2].set_title(f'Difference (Observed - Predicted): MSE = {mse:.3e}')
        ax[2].axis('off')

        # Colorbars
        cbar_main = fig.colorbar(contour0, ax=ax[:2], orientation='vertical')
        cbar_main.ax.set_ylabel('Value')

        cbar_diff = fig.colorbar(contour2, ax=[ax[2]], orientation='vertical')
        cbar_diff.ax.set_ylabel('Difference')

        # plt.tight_layout()

        png_file = f"{out_dir}/predict_{i}.png"
        fig.savefig(png_file)

        frames.append(imageio.imread(png_file))

    imageio.mimsave(f"{out_dir}/0_prediction_sequence.gif", frames, duration=1/30)  # 30 fps

    fig, ax = plt.subplots()

    ax.plot(range(X.shape[0]), mses)
    ax.set_title("Prediction MSE")
    ax.set_xlabel("Sample")
    ax.set_ylabel("MSE")
    fig.savefig(f"{out_dir}/mses.png")


#
# Predicting one at a time
#
predict_and_plot(X, y, out_dir='pngs')

#
# Predicting with predictions
#
for k, j in enumerate(lengths[1:]):
    start_idx = sum(lengths[:k+1])
    sample_indices = range(start_idx, start_idx + j)
    out_dir = f'pngs/pngs_sample_set_{k}'
    print(f"########## {out_dir} ##########")
    predict_and_plot(
        X[sum(lengths[:k+1]):start_idx + j], y[sum(lengths[:k+1]):start_idx + j], out_dir, autoregressive=True
    )
