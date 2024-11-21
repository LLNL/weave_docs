import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
import kosh
import os
from sklearn.preprocessing import MinMaxScaler as MMS
from sklearn.gaussian_process import GaussianProcessRegressor as GPR
from sklearn.model_selection import LeaveOneOut
import argparse

p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
p.add_argument("--store", help="path to kosh/Sina store")
p.add_argument("--name", help="name for the ensembe of datasets plotted", required=True)
p.add_argument("--run-type", default="sim", help="run type to search for")

args = p.parse_args()

rng = np.random.default_rng()

####################################################################

#################### Data Management with Kosh #####################

####################################################################

# After generating data with Maestro or Merlin we need to access the data in our Kosh/Sina store.
# After some data manipulation we can train a surrogate model to emulate the Pyranda physics
# calculations.

# The Kosh store gives us the convenience of saving all the variables and outputs with the
# associated metadata. Instead of saving variables like the Atwood number and velocity-magnitude
# in the file names we can save all the information we need in the metadata. Then it's convenient
# to find in our ensemble later.

store = kosh.connect(args.store)

# Create an ensemble or use an existing one
try:
    ensemble = next(store.find_ensembles(name=args.name))
except Exception:
    # does not exist yet
    ensemble = store.create_ensemble(name=args.name)

# Choosing times to evaluate mixing width

# We gathered a lot of data with the simulation runs. We're going to evaluate the model
# at time = 60.0 seconds.

sample_time = 60.0

# Gathering variables from each simulation run

# We can loop through the datasets in our Kosh store, and save the inputs and outputs
# of interest. Data of all different types can be associated together in our ensemble.

samples = []
N_cases = len(list(store.find(types="pyranda", run_type=args.run_type, ids_only=True)))
for i, case in enumerate(store.find(types="pyranda", run_type=args.run_type), start=1):
    # Let's add this dataset to our ensemble
    print("******************************")
    print("DS:", case.id)
    print("******************************")
    ensemble.add(case)

    # Le'ts retrieve variables of interest
    time  = case["variables/time"][:]
    width = case["variables/mixing width"][:]
    mixed = case["variables/mixedness"][:]
    if i == 0:
        print(f"time: {time}")
        print(f"width: {width}")
        print(f"mixed: {mixed}")
    # Atwood and velocity come from metadata
    atwood   = case.atwood_number
    velocity = case.velocity_magnitude
    # Plot the mix width during the simulation
    lbl = f"Vel: {velocity} - At: {atwood}"
    plt.figure(2)
    plt.plot( time, width, '-o', label=lbl)
    # We add a bar to show the time(s) of simulation where a surrogate model will be trained.
    plt.axvline(x=60.0, color='b', label=f"60 s")
    plt.xlabel("Time")
    plt.ylabel("Mix Width")
    plt.title("Rayleigh-Taylor Simulations")
    if i == N_cases:
        fnm = "all_mixing_width.png"
        plt.savefig(fnm)
        ensemble.associate(fnm, "png", metadata={"title":lbl}) 

    # Plotting to show the input sampling design
    plt.figure(1)
    plt.plot(atwood, velocity, 'ko')
    plt.xlabel("Atwood number")
    plt.ylabel("Velocity magnitude")
    plt.title("Latin Hypercube Space-Filling Design")
    if i == N_cases:
        fnm = "atwood_vs_vel.png"
        plt.savefig(fnm)
        ensemble.associate(fnm, "png", metadata={"title":'atwood vs velocity'}) 

    # For each time, qoi
    #  Sample = [atwood, velocity, width]
    sample_width = np.interp(sample_time, time, width)
    samples.append([atwood, velocity, sample_width])

samples = np.array(samples)
print(f"Created samples type: {type(samples)}")
print(samples)
# Save data for next step
header = "# 'atwood' 'velocity' "
header += " 'width-0' "
fnm = f"rt_{args.run_type}_data.csv"
np.savetxt(fnm, samples, delimiter=',', header=header)
#associate with ensemble
ensemble.associate(fnm, "pandas/csv", metadata={"gp_data":True})

################################################################

###################  Fitting GP Models #########################

################################################################

# We will fit a Gaussian process surrogate model for each time we chose from the
# simulation. This model will need to be able to predict mixing width very
# quickly and accurately. The Gaussian process model can return a prediction and a
# standard error estimate. the error should be very small for data points it was
# trained on, and larger when it has to interpolate between training points.

# Get inputs
xgp = samples[:, 0:2]
# Normalize the inputs for better model fit
scaler = MMS()
scaled_samples = scaler.fit_transform(xgp)

# Get inputs for 2D plots
atwoods    = np.linspace(.25,.75, 100)
velocities = np.linspace(.75, 1.25, 100)
at2d, vel2d = np.meshgrid(atwoods, velocities)
atwoods = at2d.flatten().reshape(-1,1)
velocities = vel2d.flatten().reshape(-1,1)
# Create 2D input array of (#samples, #features)
inputs = np.concatenate((atwoods, velocities), axis=1 )
# Use the scaler to normalize these inputs as well
scaled_inputs = scaler.transform(inputs)

# Fitting a GP model at time = 60.0 seconds
y = samples[:, 2]  # Get width at this time-slice
GP_model = GPR().fit(scaled_samples, y)

# See GP prediction in 2D
pred, std = GP_model.predict(scaled_inputs, return_std=True)

# Save a plot to show surrogate model interpolating and extrapolating
fig = plt.figure(3)
ax = fig.add_subplot(111, projection='3d')
pred2d = pred.reshape(at2d.shape)
std2d = std.reshape(at2d.shape)
mycol = cm.jet((std2d - std.min()) / (std.max() - std.min()))
cmap = plt.colormaps["jet"]
plot = ax.plot_surface(at2d, vel2d, pred2d, facecolors=mycol)
fig.colorbar(cm.ScalarMappable(norm=Normalize(0, 1),
                               cmap=cmap),
                               ax=ax,
                               label="Standard Error",
                               pad=0.15)
ax.set_xlabel('Atwood')
ax.set_ylabel('Velocity')
ax.set_zlabel('Width')
plt.title("GP Model at 60 s")
fnm = "GP_at_60.0_s.png"
ax.figure.savefig(fnm)
ensemble.associate(fnm, "png", metadata={"title":'2D GP'})

# Leave-one-out cross validation
loo = LeaveOneOut()

y = samples[:, 2:]

loo_pred = []
loo_bar = []
loo_sqerror = []
for i, (train_index, test_index) in enumerate(loo.split(scaled_samples)):
    gp_model = GPR().fit(scaled_samples[train_index, :], y[train_index])
    pred, std = gp_model.predict(scaled_samples[test_index, :], return_std=True)
    loo_pred.append(pred)
    loo_bar.append((pred + std * 1.96) - (pred - std * 1.96))
    loo_sqerror.append((y[test_index] - pred)**2)
plt.figure(4)
plt.errorbar(y.flatten(),
             np.array(loo_pred).flatten(),
             yerr=np.array(loo_bar).flatten(),
             fmt='o',
             label='GP')
plt.plot([2,9], [2,9], 'r-', label='Exact')
plt.xlabel("Actual Mix Width")
plt.ylabel("Predicted Mix Width")
plt.title(f"Leave-One_Out Cross Validation 60 s")
plt.legend()
fnm = f"LOO_at_60.0_s.png"
plt.savefig(fnm)
ensemble.associate(fnm, "png", metadata={"title":'LOO cross val'})
