# WEAVE Workflow

This tutorial will show you how to use the various WEAVE tools to run a set of simulations from start (set up) to finish (analysis). This will be a high level overview which you can then deepdive by heading over to each of the tools' specific repos and documentation. The workflow steps can become very complicated very quickly but this tutorial will keep it simple as this is an introduction to WEAVE.

A core concept of this WEAVE tutorial is Verification, Validation, and Uncertainty Quantification (VVUQ). The definition for VVUQ can be seen below which is taken from [ASME Verification, Validation and Uncertainty Quantification (VVUQ)](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty). We use these concepts to understand how closely our simulation ensembles match our experiments since running experiments is very expensive and time consuming.

> * Verification is performed to determine if the computational model fits the mathematical description. 
* Validation is implemented to determine if the model accurately represents the real world application. 
* Uncertainty quantification is conducted to determine how variations in the numerical and physical parameters affect simulation outcomes.

## Workflow Steps

The WEAVE workflow at a high level can be broken down to the following steps:

1. Determine baseline simulation
    * Create a small parametric study to compare simulation results to validation data
    * Baseline simulation will be the parameters that gave the minimum Root Mean Squared Error (RMSE) averaged accross all the QoIs
2. Determine uncertainty bounds for parameters
    * Material properties, Boundary Conditions, etc...
    * Through literature, engineering expertise, etc...
3. Use orchestration tool to run ensemble of simulations
    * Determine which WEAVE orchestration tool best fits your needs
    * Set up workflow to submit simualtions, check statuses, gather data, etc...
4. Manage and consolidate data from all the different simulation runs
    * Determine which WEAVE data management tool best fits your needs
    * Gather all data types from various locations into one source
5. Post-process and visualize data
    * Extract necessary information, manipulate data, and save post-processed data
    * Create plots, charts, tables, etc... for reports and presentations
6. Create surrogate model
    * Use simulation ensemble data to create a surrogate model
    * Can be used instead of computationally expensive high fidelity simulation


## Tools available diagram

The steps discussed above along with each of the WEAVE tools can be seen below. Some of these tools can span multiple steps of the worklow or just a single step. Maestro and Merlin can also be used in step 1 and 2 as they are worklow managers but since those steps are more about space/concept exploration, Maestro and Merlin only cover steps 3 trough 6.

``` mermaid
sequenceDiagram
    participant 1. Baseline Simulation
    participant 2. Uncertainty Bounds
    participant 3. Simulation Ensembles
    participant 4. Consolidate Data
    participant 5. Post Process Data
    participant 6. Surrogate Model
    Note over 2. Uncertainty Bounds: Trata
    Note over 3. Simulation Ensembles,6. Surrogate Model: Maestro and Merlin
    Note over 3. Simulation Ensembles: Themis
    Note over 4. Consolidate Data,5. Post Process Data: Kosh
    Note over 4. Consolidate Data,5. Post Process Data: Sina
    Note over 5. Post Process Data: PyDv
    Note over 6. Surrogate Model: IBIS
```


