# WEAVE

WEAVE stands for **W**orkflow **E**nablement and **A**d**V**anced **E**nvironment. This project brings together a set of open-source tools that create a workflow for any high-performance computing (HPC) application. These tools can be used in combination or separately. WEAVE enhances user productivity and scientific quality through this common infrastructure and tool integration.

## Background and Philosophy

Developed at LLNL, the WEAVE project began as workflow support for the Strategic Deterrence organization's Weapon Simulation and Computing ([WSC](https://sd.llnl.gov/about-us/organizations#weapon-simulation-computing)) and Weapon Physics and Design ([WPD](https://sd.llnl.gov/about-us/organizations#weapon-physics-design)) program areas. The users in WSC and WPD help ensure national security by evaluating and modernizing the nation's nuclear stockpile without nuclear testing. This stewardship mission requires rigorous simulation of complex physical phenomena on massively parallel HPC systems like LLNL's petascale [Sierra supercomputer](https://hpc.llnl.gov/hardware/compute-platforms/sierra).

As the Department of Energy and national labs enter the exascale computing era, where multiphysics simulations can reveal physical processes in 3D and at higher resolution and longer timescales than ever before, scientific application teams must be able to rely on a sophisticated, flexible HPC workflow.

Building off our success with WSC and WPD, we are releasing the WEAVE project as open source to support both general (any interested team) and dedicated (via interaction with shareholders) users. Our core values are pride in our work, respect for users, and constant and constructive dialogue. We welcome contributions and new feature ideas.

## Workflow Support

WEAVE supports users' workflows via these open-source software tools, which are tested together to ensure compatibility, flexibility, and efficiency. See [WEAVE Tools](tools.md) for more information on each.

* **Orchestration**
    * [Maestro](https://github.com/LLNL/maestrowf): automate workflows that script tasks to layer on parameterization, task dependencies, and output
    * [Merlin](https://github.com/LLNL/merlin): extension of Maestro that builds, runs, and processes large-scale machine learning–based workflows
* **Simulations and their data management**
    * [Sina](https://github.com/LLNL/Sina): store, query, and visualize simulation data through a Python API
    * [Kosh](https://github.com/LLNL/kosh): built on top of Sina to consistently access and process data, and move it to another location for collaboration
* **Simulation evaluation**
    * [Trata](https://github.com/LLNL/trata): Bayesian sampling package that generates sampling points and patterns for composite studies
    * [IBIS](https://github.com/LLNL/ibis): Interactive Bayesian Inference and Sensitivity; used with Trata to generate statistical model of simulations and predict future runs
    * [PyDV](https://github.com/LLNL/PyDV): Python Data Visualizer; 1D graphics and data analysis tool

Our goal is to disseminate:

* Highly reliable software (via CI)
* Readily available versioned tools (via CD)
* Easy-to-use and variate documentation
    * WEAVE-wide
    * Software-level
* Broad support
    * Tutorials
    * FAQs
    * Forums
    * Direct engagement/embedding with users' teams (when possible)

WEAVE also aims to smooth links to [Livermore Computing technologies](https://hpc.llnl.gov/software) (e.g., Slurm, Flux, containers). Ultimately, users do not need to know the intricacies of these disparate tools. WEAVE handles the workflow, saving time for users and their applications' solutions. Contact us at <weave-support@llnl.gov>.
