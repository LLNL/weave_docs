import os
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
import kosh
import scipy.stats as sts
from sklearn.preprocessing import MinMaxScaler as MMS
from sklearn.gaussian_process import GaussianProcessRegressor as GPR
from ibis import mcmc
import argparse

p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
p.add_argument("--store", help="path to kosh/Sina store")
p.add_argument("--name", help="name for the ensemble of datasets to load", required=True)
p.add_argument("--specroot", help="the specroot")

args = p.parse_args()

########################################################

#####   Reading in and transforming the data   ########

########################################################

# We can connect to our Kosh store and ensemble to conveniently have access to all the
# data we need. We're going to need both the simulation data and experimental data for 
# MCMC sampling.

# Connect to the Kosh store and read in datasets
store = kosh.connect(args.store)

# The experimental data was saved to the ensemble in our Kosh store
experiments_ensemble = next(store.find_ensembles(name="experiments"))
exp_uri = next(experiments_ensemble.find(mime_type="pandas/csv")).uri
exp_uri = os.path.join(args.specroot, exp_uri)

# The simulation data was just generated with the workflow manager (Maestro or Merlin)
# and ingested by the Sina database. 
sim_ensemble = next(store.find_ensembles(name=args.name))
sim_uri = next(sim_ensemble.find(mime_type="pandas/csv")).uri

# Use the URI to read in datasets
rt_exp_data = np.genfromtxt(exp_uri, delimiter=',')
rt_sim_data = np.genfromtxt(sim_uri, delimiter=',')

# Separate inputs and outputs for experimental and simulation data
xexp = rt_exp_data[:, :2]
yexp = rt_exp_data[:, -1]  # The last element is for time 60.0 sec.
xsim = rt_sim_data[:, :2]
ysim = rt_sim_data[:, 2:]

msg = f"\nSimulation data inputs: {xsim.shape}, min: {xsim.min(axis=0)}, "
msg += f"max: {xsim.max(axis=0)}, mean: {xsim.mean(axis=0)}"
msg += f"\nSimulation data outputs: {ysim.shape}, min: {ysim.min(axis=0)}, "
msg += f"max: {ysim.max(axis=0)}, mean: {ysim.mean(axis=0)}"
msg += f"\nExperimental data inputs: {xexp.shape}, min: {xexp.min(axis=0)}, "
msg += f"max: {xexp.max(axis=0)}, mean: {xexp.mean(axis=0)}"
msg += f"\nExperimental data output: {yexp.shape}, min: {yexp.min()},"
msg += f"max: {yexp.max()}, mean: {yexp.mean(axis=0)}"
print(msg)

#########################################################

############# Train the surrogate model #################

#########################################################

# The GP model and MCMC sampling perform better when inputs are scaled
# Using a min-max scaler from scikit-learn
scaler = MMS()
scaled_xsim = scaler.fit_transform(xsim)

# Build the GP surrogate for time 60.0 sec
surrogate = GPR().fit(scaled_xsim, ysim)

# Also scale experimental data in the same way
scaled_xexp = scaler.transform(xexp)

print(f"Surrogate model {surrogate}")

########################################################

#####    Defining the MCMC sampling function   ########

########################################################

# We need to provide a lot of information for the MCMC sampling function.
# We'll start by defining information for the inputs.

# Create the IBIS MCMC object
default_mcmc = mcmc.DefaultMCMC()

############# Input Section ####################

input_names = ['atwood_num', 'vel_mag']

# Calculate standard deviation for simulation input features
sim_std = np.std(scaled_xsim, axis=0)
print(f"Input std estimate: {sim_std}")

ranges = [[.3, .8], [.7, 1.3]]

# Defining each input
# Scaled ranges are from 0.0 to 1.0 with
# We're using uninformative priors for both inputs
for i, name in enumerate(input_names):
    default_mcmc.add_input(name, 0.0, 1.0, sim_std[i], sts.uniform().pdf,
                           unscaled_low=ranges[i][0], unscaled_high=ranges[i][1], scaling='lin')

############## Output Section ##################

# Next we define information for the outputs.

output_name = f'mix_width-60s'

# Create names for experimental data
expNames = [f"exp{i}" for i in range(len(yexp))]

# Find standard deviation estimate
exp_std = yexp.std()
print(f"Output std estimate: {exp_std}")

# Add outputs
for i, expName in enumerate(expNames):
        default_mcmc.add_output(expName, output_name, surrogate, yexp[i], exp_std, input_names)

################################################

############# Run MCMC Sampling ################

################################################

# We will define the rest of the information and run the chains for sampling the posterior distribution.

# total:      We are going to run chains of "total" in length. That's the total number of samples, but
#             we will need to check the trace plot to see how the sampling looks.
# start:      Start means a starting value for each input. Here we are starting with .5 for both Atwood
#             number and velocity. These are not likely to be the values that produce the highest probability
#             for the posterior distribution. So the sampling may explore different local maximums until it
#             finds the global maximum.
# burn:       We will want to only keep the samples that are exploring around the global maximum. The initial
#             samples may wander, and we will drop them from the samples we keep. This is called the "burn-in"
#             period. In this case we will drop the first 200 samples.
# every:      There is some correlation between the samples in the chain. The closer the samples are together
#             in the chain, the more correlated they are. If we keep every 2 samples in this case it reduces
#             the correlation between the samples.
# n_chains:   We can run multiple independent sampling chains in parallel.
# prior_only: Whether to run the chains on just the prior distribution.
# seed:       The random seed for the Metropolis-Hastings algorithm that chooses the next sample for the chain. 

# Run the MCMC chains to get samples approximating the posterior distribution
default_mcmc.run_chain(total=5000,
                       burn=200,
                       every=2,
                       start={name: .5 for name in input_names},
                       prior_only=False,
                       seed=15)

chains = default_mcmc.get_chains(flattened=False, scaled=True)

#####################################################

################ MCMC Sampling Plots ################

#####################################################

# We'll start by looking at the trace plots. We want to see a good sampling of the space,
# and since we already removed the "burn-in" samples, the center of the mixing should stay
# in one place.

for input_n in input_names:
    plot = default_mcmc.trace_plot(input_name=input_n)

# Next we will view the histogram showing us a rough approximation of the posterior
# distribution for the mixing width.

outvar = list(default_mcmc.outputs.keys())[0]
post_pp = default_mcmc.posterior_predictive_plot(outvar, bins=10)

# Now we can see the more informed distributions for our uncertain parameters.

for input_n in input_names:
    hist_plot = default_mcmc.histogram_plot(input_name=input_n, bins=25, density=True, alpha=.5)

# In the future we could use these distributions for Atwood number and density to make better predictions
# with error estimates.
