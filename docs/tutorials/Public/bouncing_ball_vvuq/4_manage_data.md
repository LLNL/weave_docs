# 4. Manage Data

There is a lot of data to consolidate after all the simuluations are finished. WEAVE has a couple of tools that can do that for you: Sina and Kosh.

## Workflow

The worklow files for the different orchestration tools can be seen below. The Sina team has worked with some modeling and simulation tools to output a `sina.json` file that is already in the Sina format. If you would like to have your modeling and simulation code output a `sina.json` file for ease of use, contact [siboka@llnl.gov](mailto:siboka@llnl.gov). If your code doesn't output that format, Sina can still be used with a variety of file types such as (...) and the `dsv_to_sina.py` script is an example on how to format your data into the Sina json format. Since Kosh is built on top of Sina, the `sina.json` file can also be used seamlessly. We now add a couple of more lines to our specs to manage data from all the simulation runs.

### Maestro & Merlin

In order to add data management to our spec file, we'll need to modify the `env` and `study` blocks.

To modify the `env` block we'll add two new variables: `PROCESS_SCRIPT_PATH` and `OUTPUT_DS_PATH`. The `PROCESS_SCRIPT_PATH` variable defines the python script `dsv_to_sina.py` that will process our simulation data. The `OUTPUT_DS_PATH` variable provides a location to store the datastore output which, in this case, will be `04_manage_data/data/ensembles_output.sqlite` which can be used by both Sina and Kosh.

In the `study` block we need to add a new step `ingest-ball-bounce` to be completed after our simulations have finished. This step adds a script which uses Sina to ingest all the data from the different runs into a single `sqlite` datastore. It also adds an important key `depends` which tells `ingest-ball-bounce` to wait for all the `run-ball-bounce_*` steps (note the asterisk meaning multiple steps for the multiple simulations) to complete before consolidating the data.

From here, the specs start to differ slightly. If you're using Maestro read the [Maestro Specification](./4_manage_data.md#maestro-specification) section and if you're using Merlin see the [Merlin Specification](./4_manage_data.md#merlin-specification) section.

#### Maestro Specification

We can now run the Maestro spec with the bash command below. The data that's generated will be located in `03_simulation_ensembles/data` for the simulation ensembles and `04_manage_data/data` for the sqlite database.

Bash Command:

``` bash 
maestro run 04_manage_data/ball_bounce_suite_maestro_data_management.yaml --pgen 02_uncertainty_bounds/pgen_ensembles.py
```

Meastro Spec:

``` yaml title="04_manage_data/ball_bounce_suite_maestro_data_management.yaml"
description:
    name: ball-bounce 
    description: A workflow that simulates a ball bouncing in a box over several input sets.

env:
    variables:
        OUTPUT_PATH: ./03_simulation_ensembles/data
        SIM_SCRIPT_PATH: ../ball_bounce.py
        PROCESS_SCRIPT_PATH: ../dsv_to_sina.py
        OUTPUT_DS_PATH: ./data/ensembles_output.sqlite

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
```

#### Merlin Specification

!!! warning
    If you try to run the Maestro spec above using Merlin, you will run into issues where nothing is added to the `sqlite` datastore. To fix this, use `$(run-ball-bounce.workspace)` instead of `$(OUTPUT_PATH)` in the `cmd` for the `ingest-ball-bounce` step. 
    
This example is showing how to run simulation ensembles and ingest the data from them using Merlin.

##### Adding Data Management to the Merlin Spec

This isn't required for the Merlin spec to work, but to showcase Merlin's features we'll add a new worker `other_worker` to the `merlin` block. This worker will handle any steps we add that aren't running simulation ensembles. We change the `concurrency` flag to be 1 here since we're writing to a file and don't want to create any race conditions by having multiple child processes write to the same location. We'll only have one task to fetch in this step so we can also modify the `prefetch-multiplier` to be 1.

Merlin Spec:

``` yaml title="04_manage_data/ball_bounce_suite_merlin_data_management.yaml"
description:
    name: ball-bounce 
    description: A workflow that simulates a ball bouncing in a box over several input sets.

env:
    variables:
        OUTPUT_PATH: ./03_simulation_ensembles/data
        SIM_SCRIPT_PATH: ../ball_bounce.py
        PROCESS_SCRIPT_PATH: ../dsv_to_sina.py
        OUTPUT_DS_PATH: ./data/ensembles_output.sqlite

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
                steps: [ingest-ball-bounce]
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
merlin run 04_manage_data/ball_bounce_suite_merlin_data_management.yaml --pgen 02_uncertainty_bounds/pgen_ensembles.py
```

Launching the workers:

``` bash
merlin run-workers 04_manage_data/ball_bounce_suite_merlin_data_management.yaml
```

Once both of the steps have completed the data will be located in `03_simulation_ensembles/data` for the simulation ensembles and `04_manage_data/data` for the sqlite database. We can now stop the workers.

Stopping the workers:

``` bash
merlin stop-workers
```
