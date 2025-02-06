# Ball Bounce Simple Simulation

This tutorial will go over a simple workflow to introduce the user to couple of the WEAVE tools; specifically Maestro, Merlin, Sina, and Kosh.

The simulation used here is `ball_bounce.py`, a (very) basic simulation of a "ball" (point) bouncing around in a 3D box. Maestro is used to generate sets of runs that share a (randomly chosen) gravity and starting position, but which differ by initial velocity.

By default, each simulation runs for 20 seconds, or 400 ticks.

To emulate a "non-Sina-native" code, results are output as DSV and then ingested into Sina. Writing directly to Sina is possible (as well as faster and easier!)

Visualizations are provided in the included Jupyter notebook.

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

## How to run

1. Run [setup.sh](../setup.sh) in the [Public](..) directory to create a virtual environment with all necessary dependencies and install the jupyter kernel. 

2. Activate the environment according to the instructions given at the end of the [setup.sh](../setup.sh) script.

3. Run `maestro run ball_bounce_suite.yaml --pgen pgen.py` to generate the studies, then y to launch. By default, this will run 10 simulations and ingest them all into the database. Once it completes, re-run the maestro command as many times as you like to continue adding runs. It should take around 2 minutes to finish each.

4. Run `jupyter notebook` (or go your local Jupyter server), and open `start_here.ipynb` and `visualization.ipynb` in the resulting browser window to access the visualizations. Make sure you are using the `weave-demos` kernel.

## Content overview

### Starting files:

- `ball_bounce.py`: The "simulation" script, containing all the logic for bouncing the ball
- `dsv_to_sina.py`: A bare-bones ingester that finds dsv files and inserts them into a Sina datastore
- `ball_bounce_suite.yaml`: The Maestro workflow description, containing all the information to run a set of ball bouncing simulations. Each set shares a starting position and gravity but differs on the initial velocities.
- `pgen.py`: A custom parameter generator for Maestro, which will generate random starting conditions for each suite
- `start_here.ipynb`: Simple introduction Jupyter notebook to start off with.
- `visualization.ipynb`: A Jupyter notebook containing visualizations

### Files created by the demo:

- `output.sqlite`: A Sina datastore (here expressed as sqlite) containing all the results from all the suites run
- `output/`: The Maestro output location, containing all the files it generates
