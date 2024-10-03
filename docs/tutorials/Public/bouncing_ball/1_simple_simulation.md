# Ball Bounce Simple Simulation

!!! danger "Required Repo"
    This tutorial will use the [Bouncing Ball Demo](https://lc.llnl.gov/gitlab/weave/weave_demos/-/tree/main/CZ/ball_bounce) which will have matching tutorial steps.

This tutorial will go over a simple workflow to introduce the user to couple of the WEAVE tools; specifically Maestro, Sina, and Kosh.

## Start Here Notebook

This notebook shows the user how to run a simple Ball Bounce simulation, visualize it, and post-process data.

### `ball_bounce.py`

The user can run a simple Ball Bounce simulation manually using the `ball_bounce.py` script. This script simulates a bouncing ball in a 3D space with simple physics and outputs `"time", "x_pos", "y_pos", "z_pos", "x_pos_final", "y_pos_final", "z_pos_final", "x_vel_final", "y_vel_final", "z_vel_final", "num_bounces"` which the user can manipulate as needed.

### `ball_bounce_simple.yaml`

However, Maestro allows the user to run ensembles of simulations without having to run each manually. This can be done by using the Maestro spec `ball_bounce_simple.yaml` which contains a couple of parameters and their values in the `global.parameters` key that a user can update as needed. The command to run this Maestro spec is `maestro run ball_bounce_simple.yaml`.

### `ball_bounce_suite.yaml`

A user can also pass in their own custom parameter generator instead of writing every single parameter variation and choice by hand. This is done by importing the Maestro Parameter Generator into a script and passing that script to the Maestro command line. First a user creates a script (usually named `pgen.py`) with `from maestrowf.datastructures.core import ParameterGenerator` and creates a dictionary with the parameters and their values. See `pgen.py` for details.

Sina or Kosh can then be used to create a database that contains all the data from the ensembles instead of the user reading each of the data files one by one. Here we use the `dsv_to_sina.py` script but there are many different ways of creating a database ([Sina](https://github.com/LLNL/Sina/tree/master/examples) and [Kosh](https://github.com/LLNL/kosh/tree/stable/examples)). These updated configurations can be seen in `ball_bounce_suite.yaml` with the added step `ingest-ball-bounce`. To run this updated Maestro spec with the parameter generator pass in `maestro run -p pgen.py ball_bounce_suite.yaml` to the command line.

### Kosh Post-Processing

The user can use Kosh to extract, manipulate, and post-process the data as necessary which is now conveniently located in a single location.

## Visualization Notebook

Kosh is built on top of Sina and therefore both can use the same database. Sina has built-in support for `matplotlib`` which can be leveraged by the user since it can directly plot the data in the database. Sina supports histograms, scatter plots, line plots, 3D plots, and a couple of others. This notebook also uses another WEAVE tool named PyDV to further analyze data.