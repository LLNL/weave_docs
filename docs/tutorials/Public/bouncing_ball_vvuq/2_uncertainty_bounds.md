# 2. Uncertainty Bounds

The uncertainty bounds for the simulation parameters need to be gathered once the baseline simulation has been determined. Running simulation ensembles need parameters that can be varied with realistic values. Running a simulation with parameter values that won't be encountered for the specific study will provide results that won't be seen and will waste computer resources. In application, conditions of physical systems are constantly changing leading to uncertainty in the true, or exact, values of design parameters. Hence design parameter spaces are used to capture the range of possible values that contain the true value.

## Simulation Parameters

The first step is to determine which simulation parameters you believe should have uncertainty. These parameters are never 100% known and the world isn't perfect so there is bound to always be some uncertainty. Some parameters that could have uncertainty are the initial conditions (how accurate is the test apparatus), boundary conditions (how accurate is the test apparatus), material properties (how accurate is the material manufacturer), etc...

### Bouncing Ball

The Bouncing Ball Demo parameters were `x_pos_initial`, `y_pos_initial`, `z_pos_initial`, `x_vel_initial`, `y_vel_initial`, and `z_vel_initial`. These are all the parameters in the Python script `ball_bounce.py` but say we had other parameters such as `x_vel_ang_initial`, `y_vel_ang_initial`, and `z_vel_ang_initial` we wanted to study as well.

## Uncertainty Values

The next step is to decide on the uncertainty ranges and their distributions. Both of these can be gathered from literature, engineering expertise, and experiments. An example is a uniform distribution bounded between 5 and 10. Uniform distributions make it so all values are as likely to be chosen as another compared to a normal distribution with its concentration around its mean. This makes a uniform distribution the most conservative and is recommended unless otherwise known.

Typically, the Monte Carlo method is used to perform UQ (but there are many other methods) by assigning probability distributions to uncertain input variables. The probability distributions are then used to draw samples in sets in order to calculate corresponding output values using a [6. Surrogate Model](./6_surrogate_model.md). Based on the ensemble of output results, the output distribution should statistically describe the output's uncertainty.

### Bouncing Ball

Let's say for our Bouncing Ball Demo, the uncertainty values can be confirmed by looking at the machine specification or by running multiple setups on the machine if it is a in-house machine. After looking at the specification, or running a bunch of setup experiments, you find that the positional parameters `x_pos_initial`, `y_pos_initial`, and `z_pos_initial` have a normal distribution with a mean of your choice and a standard deviation of $\sigma = 0.5$. Now, doing the same study as above except for with the velocity parameters `x_vel_initial`, `y_vel_initial`, and `z_vel_initial`, you find that they have uniform distribution with a mean of your choice and a range of $\pm 0.15$. So with all this, now you have your uncertainty bounds and distribution for the parameters.

## Generate Parameters

!!! note
    If you're using Merlin you can follow the exact same steps in this section. Merlin extends Maestro so Maestro's Parameter Generator (pgen) will also work with Merlin.

Now that all the parameters with their uncertainty ranges and distributions are known, we can create parameter ensembles for our simulation ensembles. The WEAVE tool to use is [TRATA](/tools.md#data-analysis) as this has multiple methods for choosing parameters. However, the WEAVE tool [Maestro](/tools.md#workflow-orchestration) needs a specific file format to intake the parameters which can be generated using [Maestro’s Parameter Generator (pgen)](https://maestrowf.readthedocs.io/en/latest/parameters.html#pgen-section). This pgen functionality can be used in conjuction with TRATA as pgen only generates the format for Maestro but not the actual parameters. 

Below is a simple example of creating ten parameter sets (`NUM_STUDIES = 10`) with a normal distribution with mean of `mu = 50` and standard deviation of `sigma = 0.5` for three different variables (`VAR_1`, `VAR_2`, `VAR_3`). We import our favorite number generator libraries and then the `ParameterGenerator` library from Maestro to create the format needed. The variable assignment is in the function `get_custom_generator()` where we create an instance of `p_gen = ParameterGenerator()` class and pass it in the `params` dictonary. The `params` dictonary has the parameters as the high level keys and then each parameter has two keys: `values` are the actual parameter values and `label` is the parameter name with `.%%` which captures the value in the Maestro label.

PGEN Example Script:

```python
from maestrowf.datastructures.core import ParameterGenerator
import numpy as np


mu = 50
sigma = 0.5
NUM_STUDIES = 10

def get_custom_generator(env, **kwargs):

    p_gen = ParameterGenerator()

    params = {

        "VAR_1": {

            "values": np.random.normal(mu, sigma, NUM_STUDIES),

            "label": "VAR_1.%%"

        },

        "VAR_2": {

            "values": np.random.normal(mu, sigma, NUM_STUDIES),

            "label": "VAR_2.%%"

        },

        "VAR_3": {

            "values": np.random.normal(mu, sigma, NUM_STUDIES),

            "label": "VAR_3.%%"

        },

    }


    for key, value in params.items():

        p_gen.add_parameter(key, value["values"], value["label"])


    return p_gen
```

### Bouncing Ball

Below is the table of parameters with their values, distributions, and bounds we acquired in the previous step and section. As we start introducing more variables and increasing the number of simulations, creating the various parameter-simulation pairs becomes a very tedious process which is where WEAVE's workflow tools come into play in the next section. Imagine having to create 1024 simulations and their parameters using the method in the previous step [01 Baseline Simulation](./1_baseline_simulation.md#bouncing-ball_2).

Parameters:

| rec.id | x_pos_initial | y_pos_initial | z_pos_initial | x_vel_initial | y_vel_initial | z_vel_initial |
| --- | --- | --- | --- | --- | --- | --- |
| 47bcda_3 | 49.0 | 50.0 | 51.0 | 5.25 | 4.9 | 5.0 |
| Distribution: | Normal | Normal | Normal | Uniform | Uniform | Uniform |
| Bounds: | $\sigma = 0.5$ | $\sigma = 0.5$ | $\sigma = 0.5$ | $\pm 0.15$ | $\pm 0.15$ | $\pm 0.15$ |

Trata can solve that problem for you by creating samples for you using one of a number of Bayesian sampling methods, or using a probability density function you've defined. One very common Bayesian sampling method is the Latin Hypercube Sampling (LHS) method, which is used when you want to significantly reduce the number of runs necessary to acheive a reasonably accurate result. 

LHS aims to spread the random sample points more evenly across all possible parameter values. It partitions each input distribution into N intervals of equal probability, and selects one sample from each interval. It shuffles the sample for each input so that there is no correlation between the inputs (unless you want a correlation). 

Other methods that rely on pure randomness can be inefficient. You might end up with some points clustered closely, while other intervals within the space get no samples. 

### Maestro and Merlin 

pgen Ensemble Script :

``` python title="02_uncertainty_bounds/pgen_ensembles.py"
"""Prepare a custom generator that will start a collection of balls in the same spot with differing velocities."""

import random
import uuid
import numpy as np
from trata import sampler
from maestrowf.datastructures.core import ParameterGenerator

seed = 1777
BOX_SIDE_LENGTH = 100
GRAVITY = 9.81
coordinates = ["X", "Y", "Z"]
positions = ["{}_POS_INITIAL".format(coord) for coord in coordinates]
velocities = ["{}_VEL_INITIAL".format(coord) for coord in coordinates]
NUM_STUDIES = 1024

def get_custom_generator(env, **kwargs):

    p_gen = ParameterGenerator()
    LHCsampler = sampler.LatinHyperCubeSampler()

    # All balls in a single run share gravity, box side length, and group ID
    params = {"GRAVITY": {"values": [GRAVITY]*NUM_STUDIES,
                          "label": "GRAVITY.%%"},

              "BOX_SIDE_LENGTH": {"values": [BOX_SIDE_LENGTH]*NUM_STUDIES,
                                  "label": "BOX_SIDE_LENGTH.%%"},

              "GROUP_ID": {"values": ['47bcda']*NUM_STUDIES,
                           "label": "GROUP_ID.%%"},

              "RUN_ID": {"values": list(range(1, NUM_STUDIES+1)),
                         "label": "RUN_ID.%%"},

              "X_POS_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[47.5, 50.5]], seed=seed) for item in sublist],
                                "label": "X_POS_INITIAL.%%"},

              "Y_POS_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[48.5, 51.5]], seed=seed) for item in sublist],
                                "label": "Y_POS_INITIAL.%%"},

              "Z_POS_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[49.5, 52.5]], seed=seed) for item in sublist],
                                "label": "Z_POS_INITIAL.%%"},

              "X_VEL_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[5.10, 5.40]], seed=seed) for item in sublist],
                                "label": "X_VEL_INITIAL.%%"},

              "Y_VEL_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[4.75, 5.05]], seed=seed) for item in sublist],
                                "label": "Y_VEL_INITIAL.%%"},

              "Z_VEL_INITIAL": {"values":  [np.round(item, 4) for sublist in LHCsampler.sample_points(num_points=NUM_STUDIES, box=[[4.85, 5.15]], seed=seed) for item in sublist],
                                "label": "Z_VEL_INITIAL.%%"}
             }

    for key, value in params.items():
        p_gen.add_parameter(key, value["values"], value["label"])

    print("Preparing study set {} with gravity {}, starting position {}."
          .format(params["GROUP_ID"]["values"][0],
                  params["GRAVITY"]["values"][0],
                  tuple(params[x]["values"][0] for x in positions)))
    return p_gen
```