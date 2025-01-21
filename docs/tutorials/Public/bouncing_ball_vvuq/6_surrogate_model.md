# 6. Surrogate Model

One can create a surrogate model with all the data from the simulation ensembles. This surrogate model can be used in lieu of running a large amount of simulations in the future which is useful if the simulations take a long time to execute or are resource-intensive.

## Workflow

The worklow files for the different orchestration tools can be seen below. This is where you can use IBIS to create the surrogate model and extract Sobol Indices. However, you might have noticed that we ran the orchestration spec in the manage data step. This is because (like the post-process data step) we need to do some data exploration to understand how our data is structured and what sorts of plots we would like. After we have written our scripts to create our surrogate model and extract our Sobol Indices we can include them in our orchestration spec to further automate future simulation ensembles.

### Maestro & Merlin

In order to add a surrogate model and sensitivity analysis to our spec file, we'll need to modify the `env` and `study` blocks.

We'll add one variables `SURROGATE_SCRIPT_PATH`, and modify the `POST_PROCESS_SCRIPT_PATH` variable in the `env` block. The `SURROGATE_SCRIPT_PATH` variable will define the script `visualization_surrogate_model.py` that will be used for creating the surrogate model and running our sensitivity analysis via Sobol indices based off the simulation data. Also, now that we're running a different spec file that's located in a separate directory, we need to modify the path of the `POST_PROCESS_SCRIPT_PATH` variable to be `../05_post-process_data/visualization_ensembles_sina.py`.

In the `study` block we need to add one new step `create-surrogate-ball-bounce` to be run after the post-processing step is complete. These steps will use IBIS to create a surrogate model and extract Sobol indices for sensitivity analysis from our simulation data. The `create-surrogate-ball-bounce` step depends on `post_process-ball-bounce`.

From here, the specs start to differ slightly. If you're using Maestro read the [Maestro Specification](./6_surrogate_model.md#maestro-specification) section and if you're using Merlin see the [Merlin Specification](./6_surrogate_model.md#merlin-specification) section.

#### Maestro Specification

Bash Command:

``` bash 
maestro run 06_surrogate_model/ball_bounce_suite_maestro_surrogate_model.yaml --pgen 02_uncertainty_bounds/pgen_ensembles.py
```

Meastro Spec:

``` yaml title="06_surrogate_model/ball_bounce_suite_maestro_surrogate_model.yaml"
description:
    name: ball-bounce 
    description: A workflow that simulates a ball bouncing in a box over several input sets.

env:
    variables:
        OUTPUT_PATH: ./03_simulation_ensembles/data
        SIM_SCRIPT_PATH: ../ball_bounce.py
        PROCESS_SCRIPT_PATH: ../dsv_to_sina.py
        OUTPUT_DS_PATH: ../04_manage_data/data/ensembles_output.sqlite
        POST_PROCESS_SCRIPT_PATH: ../05_post-process_data/visualization_ensembles_sina.py
        SURROGATE_SCRIPT_PATH: ./visualization_surrogate_model.py

study:
    - name: run-ball-bounce
      description: Run a family of simulations of a ball in a box. 
      run:
          cmd: |
            python $(SPECROOT)/$(SIM_SCRIPT_PATH) output.dsv $(X_POS_INITIAL) $(Y_POS_INITIAL) $(Z_POS_INITIAL) $(X_VEL_INITIAL) $(Y_VEL_INITIAL) $(Z_VEL_INITIAL) $(GRAVITY) $(BOX_SIDE_LENGTH) $(GROUP_ID) $(RUN_ID)
    
    - name: ingest-ball-bounce
      description: Ingest the outputs from the previous step
      run:
          cmd: |
            python $(SPECROOT)/$(PROCESS_SCRIPT_PATH) $(OUTPUT_PATH) $(SPECROOT)/$(OUTPUT_DS_PATH)
          depends: [run-ball-bounce_*]
      
    - name: post_process-ball-bounce
      description: Post-process the simulation data
      run:
          cmd: |
              python $(SPECROOT)/$(POST_PROCESS_SCRIPT_PATH) $(SPECROOT)
          depends: [ingest-ball-bounce]

    - name: create-surrogate-ball-bounce
      description: Post-process the simulation data
      run:
          cmd: |
              python $(SPECROOT)/$(SURROGATE_SCRIPT_PATH) $(SPECROOT)
          depends: [post_process-ball-bounce]

```


#### Merlin Specification

!!! warning
    If you try to run the Maestro spec above using Merlin, you will run into issues where nothing is added to the `sqlite` datastore. To fix this, use `$(run-ball-bounce.workspace)` instead of `$(OUTPUT_PATH)` in the `cmd` for the `ingest-ball-bounce` step.

This example is showing how to run the simulation ensembles, ingest the data from them, post-process the ingested data, create a surrogate model of the data, and run sensitivity analysis with Sobol indices using Merlin.

##### Adding a Surrogate Model & Sensitivity Analysis to the Merlin Spec

In our `merlin` block, we need to tell `other_worker` to work on our two new steps `create-surrogate-ball-bounce` and `extract-sobol-ball-bounce` in addition to `ingest-ball-bounce` and `post_process-ball-bounce`. Since we've already created the `other_worker`, all we need to do is add `create-surrogate-ball-bounce` and `extract-sobol-ball-bounce` to the list of steps that this worker will handle.

Merlin Spec:

``` yaml title="06_surrogate_model/ball_bounce_suite_merlin_surrogate_model.yaml"
description:
    name: ball-bounce 
    description: A workflow that simulates a ball bouncing in a box over several input sets.

env:
    variables:
        OUTPUT_PATH: ./03_simulation_ensembles/data
        SIM_SCRIPT_PATH: ../ball_bounce.py
        PROCESS_SCRIPT_PATH: ../dsv_to_sina.py
        OUTPUT_DS_PATH: ../04_manage_data/data/ensembles_output.sqlite
        POST_PROCESS_SCRIPT_PATH: ../05_post-process_data/visualization_ensembles_sina.py
        SURROGATE_SCRIPT_PATH: ./visualization_surrogate_model.py

user:
    study:
        run:
            run_ball_bounce: &run_ball_bounce
                cmd: |
                  python $(SPECROOT)/$(SIM_SCRIPT_PATH) output.dsv $(X_POS_INITIAL) $(Y_POS_INITIAL) $(Z_POS_INITIAL) $(X_VEL_INITIAL) $(Y_VEL_INITIAL) $(Z_VEL_INITIAL) $(GRAVITY) $(BOX_SIDE_LENGTH) $(GROUP_ID) $(RUN_ID)
                max_retries: 1

study:
    - name: run-ball-bounce
      description: Run a family of simulations of a ball in a box. 
      run:
          <<: *run_ball_bounce

    - name: ingest-ball-bounce
      description: Ingest the outputs from the previous step
      run:
          cmd: |
            python $(SPECROOT)/$(PROCESS_SCRIPT_PATH) $(run-ball-bounce.workspace) $(SPECROOT)/$(OUTPUT_DS_PATH)
          depends: [run-ball-bounce_*]

    - name: post_process-ball-bounce
      description: Post process the simulation data
      run:
          cmd: |
            python $(SPECROOT)/$(POST_PROCESS_SCRIPT_PATH) $(SPECROOT)
          depends: [ingest-ball-bounce]

    - name: create-surrogate-ball-bounce
      description: Create the surrogate model from the simulation data
      run:
          cmd: |
              python $(SPECROOT)/$(SURROGATE_SCRIPT_PATH) $(SPECROOT)
          depends: [post_process-ball-bounce]


merlin:
    resources:
        task_server: celery
        overlap: False
        workers:
            ball_bounce_worker:
                args: -l INFO --concurrency 4 --prefetch-multiplier 2 -O fair
                steps: [run-ball-bounce]
            other_worker:
                args: -l INFO --concurrency 1 --prefetch-multiplier 1 -O fair
                steps: [ingest-ball-bounce, post_process-ball-bounce, create-surrogate-ball-bounce]
```

##### Running the Merlin Spec

!!! important
    To be able to use Merlin in a distributed environment (not locally), you first need to make sure you've set up your merlin config file (`app.yaml`). See [Merlin's confluence page](https://lc.llnl.gov/confluence/display/MERLIN) and the [Merlin configuration docs](https://merlin.readthedocs.io/en/latest/merlin_config.html) for more information.

Running a Merlin study can be broken down into 3 distinct steps:

1. Launching the tasks
2. Launching the workers
3. Stopping the workers

See [here](./3_simulation_ensembles.md#running-the-merlin-spec) for more information on why this is necessary.

Launching the tasks:

``` bash
merlin run 06_surrogate_model/ball_bounce_suite_merlin_surrogate_model.yaml --pgen 02_uncertainty_bounds/pgen_ensembles.py
```

Launching the workers:

``` bash
merlin run-workers 06_surrogate_model/ball_bounce_suite_merlin_surrogate_model.yaml
```

Once all the steps have completed the data will be located in `03_simulation_ensembles/data` for the simulation ensembles, `04_manage_data/data` for the sqlite database, `05_post-process_data/images` for the post-processing plots, and **insert new locations for step 6 here**. We can now stop the workers.

Stopping the workers:

``` bash
merlin stop-workers
```

## Creating and Using a Surrogate Model

### The Scikit-learn Library

Scikit-learn is one of the most popular open source machine learning (ML) libraries available for Python programmers. It is considered the gold standard for ML in both industry and academia as it provides a plethora of supervised and unsupervised machine learning algorithms. In the context of surrogate models, we will focus on the supervised ML algorithms scikit-learn makes available to us, paying particular attention to the Gaussian Process Regressor.

Gaussian Processes (GPs) are a generic supervised learning method designed to solve regression and probabilistic classification problems.

The advantages of GPs are:

- The prediction interpolates the observations (at least for regular kernels).

- The prediction is probabilistic (Gaussian) so that one can compute empirical confidence intervals and decide based on those if one should refit (online fitting, adaptive fitting) the prediction in some region of interest.

The disadvantages of GPs include:

- They are not sparse, i.e., they use the whole samples/features information to perform the prediction.

- They lose efficiency in high dimensional spaces – namely when the number of features exceeds a few dozens.

GPs are well-known for provided calibrated uncertainty estimates and thus is our selected surrogate model type. In addition to standard scikit-learn estimator, GaussianProcessRegressor (GPR):

- allows prediction without prior fitting (based on the GP prior)

- provides an additional method sample_y(X), which evaluates samples drawn from the GPR (prior or posterior) at given inputs

- exposes a method log_marginal_likelihood(theta), which can be used externally for other ways of selecting hyperparameters, e.g., via Markov chain Monte Carlo (MCMC).

We can import and instantiate the GPR estimator and easily fit it to our bouncing ball simulation data, as shown below.

```python
from sklearn.gaussian_process import GaussianProcessRegressor
import pandas as pd

database = os.path.join(spec_root, '../04_manage_data/data/ensembles_output.sqlite')
datastore = create_datastore(database)
recs = datastore.records

groups = set(x["group_id"]["value"] for x in recs.get_data(["group_id"]).values())

# instantiating the MCMC object
vanilla_exp = mc.DefaultMCMC()

# accessing and sampling the data for our surrogate model
# we need to allocate training data from our previously run simulations to train a machine learning surrogate model
# we will be training our model on x_pos_final from our simulation data as well as position and velocity samples

x_pos_final_train, x_pos_train, y_pos_train, z_pos_train, x_vel_train, y_vel_train, z_vel_train = [], [], [], [], [], [], []

for group in groups:
    id_pool = list(recs.find_with_data(group_id=group))
    for _, rec_id in enumerate(id_pool):
        rec = recs.get(rec_id)
        data = rec.data_values
        
        # our feature training data
        x_pos_train.append(data["x_pos_initial"])
        y_pos_train.append(data["y_pos_initial"])
        z_pos_train.append(data["z_pos_initial"])
        x_vel_train.append(data["x_vel_initial"])
        y_vel_train.append(data["y_vel_initial"])
        z_vel_train.append(data["z_vel_initial"])

        # our target training data
        x_pos_final_train.append(data["x_pos_final"])


# our sampled feature training data
features_train = pd.DataFrame([x_pos_train, y_pos_train, z_pos_train, x_vel_train, y_vel_train, z_vel_train])
features_train = features_train.transpose()
print(features_train)

x_pos_final_train = pd.Series(x_pos_final_train)
print(x_pos_final_train)

# we have opted to use a Guassian Process Regressor as our surrogate model for this problem
surrogate_model = GaussianProcessRegressor()

# fitting the surrogate model using our parameter samples and the x position final simulated for those parameters
surrogate_model.fit(features_train, x_pos_final_train)        

# adding the target testing data and our fitted model as output to the MCMC for each observed x_pos_final
for _ in x_pos_final_test:
    vanilla_exp.add_output('output', 'x_pos_final', surrogate_model, _, xf_std, 
            ['x_pos_initial', 'y_pos_initial','z_pos_initial','x_vel_initial','y_vel_initial','z_vel_initial'])

```

### Markov chain Monte Carlo

Markov chain Monte Carlo (MCMC) methods are commonly used in UQ to assign probability distributions to uncertain design parameters. Polynomial chaos expansion (PCE) models are an alternative to MCMC and provide the statistical characteristics of results with greatly reduced computational cost.

Spectral methods like polynomial chaos expansion provide an elegant formulation to obtain output statistical indices, which are much faster than the traditional Monte Carlo method. In addition, screening analyses (e.g. Morris screening) can inform users which sources are non-influential and can be ignored completely from UQ workflows.

After generating samples from the bouncing ball simulations, one can use IBIS to set up and run Markov Chain Monte Carlo on a set of unobserved inputs (the ball's initial position and velocity for example) and observed outputs (the final x position of the ball) with the surrogate model mapping inputs to outputs. Users are required to define a proposal distribution standard deviation; a normal distribution with a mean of the current point is often used for the proposal distribution. 

```python
# adding the input data to our MCMC
vanilla_exp.add_input('x_pos_initial', min(x_pos), max(x_pos), sig_x)
vanilla_exp.add_input('y_pos_initial', min(y_pos), max(y_pos), sig_y)
vanilla_exp.add_input('z_pos_initial', min(z_pos), max(z_pos), sig_z)
vanilla_exp.add_input('x_vel_initial', min(x_vel), max(x_vel), sig_vx)
vanilla_exp.add_input('y_vel_initial', min(y_vel), max(y_vel), sig_vy)
vanilla_exp.add_input('z_vel_initial', min(z_vel), max(z_vel), sig_vz)

# running MCMC chain 
vanilla_exp.run_chain(total=1000, burn=1000, every=2, n_chains=16, prior_only=True)
```

IBIS also provides important diagnostic metrics that evaluate the MCMC model. These tools can be used to check whether the quality of a sample generated with an MCMC algorithm is sufficient to provide an accurate approximation of the target distribution. In particular, MCMC diagnostics are used to check whether a large portion of the MCMC sample has been drawn from distributions that are significantly different from the target distribution and whether the size of the generated sample is too small.

```python
vanilla_mcmc.diagnostics_string()
```
The function above outputs the following diagnostic metrics:

* ``rhat``: measures convergence of chains 
* ``n_eff``: measures the effective sample size 
* ``var_hat``: estimates the variance of the samples 
* ``mean``: the mean of the samples
* ``mode``: the mode of the samples
* ``std``: the standard deviation of the samples

Output:
```
x_pos_initial:
  r_hat:1.0031
  n_eff:5425.1361
  var_hat:0.3293
  mean:49.9844
  std:0.5738
  mode:50.3300
y_pos_initial:
  r_hat:1.0020
  n_eff:6315.0264
  var_hat:0.1388
  mean:49.3571
  std:0.3726
  mode:48.9228
z_pos_initial:
  r_hat:1.0037
  n_eff:6400.0682
  var_hat:0.1304
  mean:50.6119
  std:0.3611
  mode:50.3437
x_vel_initial:
  r_hat:1.0027
  n_eff:4972.9100
  var_hat:0.0207
  mean:5.2534
  std:0.1440
  mode:5.4924
y_vel_initial:
  r_hat:1.0041
  n_eff:5075.3370
  var_hat:0.0023
  mean:4.9147
  std:0.0487
  mode:4.9940
z_vel_initial:
  r_hat:1.0017
  n_eff:6086.9134
  var_hat:0.0014
  mean:5.0659
  std:0.0375
  mode:5.0864
```

### Bespoke Surrogate Models

Although IBIS enables a user to create surrogate models using piped machine learning methods from scikit-learn's library, it also allows a user to define their own surrogate models. The only thing IBIS requires is that those models have fit/predict functions similar to scikit-learns "fit-predict" paradigm.

## Sobol Indices

After estimating the performance of the surrogate model caused by all the sources of uncertainty, an understanding of which uncertainty sources contribute the most to the variance of simulation results, or which uncertainty sources drive the simulation results to go beyond thresholds, is necessary. This ranking of uncertainty sources is also known as global sensitivity analysis. Global sensitivity analysis apportions the total variance of the simulation output to different uncertainty sources and their interactions. 

IBIS provides a range of sensitivty measures and plots, mutual information rank plots being one. Mutual information rankings order the measured amount of information obtained about one random variable by observing another. Recall a high mutual information indicates a large reduction in uncertainty; low mutual information indicates a small reduction; and zero mutual information between two random variables means the variables are independent. The function below will output a plot ranking the y-position of the bouncing ball to the y-velocity and highlight which parameter the number of bounces is most sensitive to. 

The outcome of this sensitivity analysis is usually summarized in the form of Sobol indices. Parameters with larger Sobol index values contribute more to the variation of the simulation output, while parameters with smaller Sobol index values basically play no role. One of the types of plots recommended in the previous section was the correlation plots. This plot can tell you how of a relationship there is between the varied parameter and the QoI. This is very useful to determine which parameters affect the QoI the most in order to run further studies concentrating and/or reducing the uncertainty of that parameter. This is pretty straightforward if the correlation is linear but if it's not, then Sobol' Indices should be used.

## Potential Plots
Below is a list of plots that one can create using IBIS:

* Variance network plots
* Rank plots
* Score plots
* F score plots
* Lasso path plots
* PCE score plots
* Mutual information rank plots
* Likelihood plots
* Slice plots
* Contour plots
* Scatter plots
* Box plots
* Spaghetti plots
