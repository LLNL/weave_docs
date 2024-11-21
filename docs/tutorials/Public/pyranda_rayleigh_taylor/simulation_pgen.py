import numpy as np
from trata.sampler import LatinHyperCubeSampler as LHS
from maestrowf.datastructures.core import ParameterGenerator

def get_custom_generator(env, **kwargs):

    # Settings for the Latinhypercube sampler
    Nruns = int(kwargs.get("N_RUNS", env.find("N_RUNS").value))
    test_box = [[0.3, 0.65], [0.85, 1.15]]
    seed = 7

    # Get space-filling samples for the multi-dimensional feature space
    lhs_values = LHS.sample_points(box=test_box, num_points=Nruns, seed=seed)

    # Separate and round the variables
    atwood   = np.round(np.array(list(lhs_values[:, 0]), dtype=float),3).tolist()
    velocity = np.round(np.array(list(lhs_values[:, 1]), dtype=float),3).tolist()
    try:
        env.find("SAMPLE_BOUNDS").value
        merlin = True
    except:
        merlin = False
    if not merlin:
        seeds = np.random.randint(0, 1000, size=(len(velocity))) 


    p_gen = ParameterGenerator()

    params = {"ATWOOD": {"values": atwood,
                                "label": "ATWOOD.%%"},

              "VELOCITY_MAGNITUDE": {"values": velocity,
                                "label": "VEL.%%"},
             }
    if not merlin:
        params["SEED"] = {"values":seeds, "label":"SEED.%%"}

    for key, value in params.items():
        p_gen.add_parameter(key, value["values"], value["label"])

    return p_gen
