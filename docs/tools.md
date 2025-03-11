# WEAVE Tools

WEAVE provides a collections of tools to help you through your workflow:

* **Orchestration:** split your workflow into separate and parametrizable steps
* **Data Management:** catalog, search, and access your data
* **Data Analysis:** evaluate sampling, uncertainty quantification (UQ), surrogate models, and more
* **Data Visualization:** display, scale, and combine data

Multiple WEAVE tools under the same workflow categories can be used to achieve your purpose, and it can be a bit perplexing for a new user to decide which tool to use for their needs. Each tool's description includes its uses and strengths to help you determine the suitability of a particular tool.

## Workflow Orchestration

<img src=./assets/images/maestro_logo.png width="100" alt="Maestro Logo"> | [Public GitHub](https://github.com/LLNL/maestrowf/) | [Documentation](https://maestrowf.readthedocs.io/en/latest/) | [Quick Start Guide](https://maestrowf.readthedocs.io/en/latest/#getting-started-is-quick-and-easy)

* Maestro is an open-source HPC software tool that defines a YAML-based study specification for multi-step workflows and automates execution of software flows on HPC resources. The core design tenets of Maestro focus on encouraging clear workflow communication and documentation while making consistent execution easier, allowing users to focus on science.

* Maestro’s study specification helps users think about complex workflows in a step-wise, intent-oriented manner that encourages modularity and tool reuse. Maestro’s user-centric design leverages software design practices such as abstract interfacing and utilizing design patterns, forming the foundation for enabling a layered workflow architecture.

* These principles are becoming increasingly important as computational science is continuously more present in scientific fields and as users perform increasingly complex workflow processes across HPC platforms.

* Maestro is WEAVE's de-facto orchestration tool and should cover most of your needs. It is the underlying orchestration engine used by Codepy.

<img src=./assets/images/merlin_logo.png width="100" alt="Merlin Logo">  | [Public GitHub](https://github.com/LLNL/merlin) | [Documentation](https://merlin.readthedocs.io/en/latest/) | [Tutorial](https://merlin.readthedocs.io/en/latest/tutorial.html)

* Merlin is a tool for running machine learning based workflows. The goal of Merlin is to make it easy to build, run, and process the kinds of large scale HPC workflows needed for cognitive simulation.

* At its heart, Merlin is a distributed task queuing system, designed to allow complex HPC workflows to scale to large numbers of simulations (we've done 100 million on the Sierra supercomputer). Merlin effectively lets you become your own Big Data generator.

* Data sets of this size can be large enough to train deep neural networks that can mimic your HPC application, to be used for design optimization, UQ, and statistical experimental inference. Merlin has been used to study inertial confinement fusion, extreme ultraviolet light generation, structural mechanics, and atomic physics, and more.

* Merlin* is built on top of Maestro and is geared toward workflows that require 100,000s to 1,000,000s of simulations. It relies on a client/server model.

## Data Management

**Sina** | [Public GitHub](https://github.com/LLNL/Sina)

* Sina allows codes to store, query, and visualize their data through an easy-to-use Python API. Data that fits the recognized schema can be ingested into one or more supported backends. (See below for a summary of Sina's data visualization capabilities.)

* Sina's API is independent of backend and gives users the benefits of a database without requiring knowledge of one, allowing queries to be expressed in pure Python. Visualizations are also provided through Python; see the [examples folder](https://github.com/LLNL/Sina/tree/master/examples) for demo Jupyter notebooks.

* Sina is intended especially for use with run metadata, allowing users to easily and efficiently find simulation runs that match desired criteria.

* Sina's code comes in two parts. The `cpp` component is an API for use in C++ codes that allows them to write data in Sina's recognized format. The remainder of Sina is found in the `python` directory, and includes all the functionality for handling and ingesting data, visualizing it through Jupyter, and so on.

* Sina allows for integration with codes and outputs metadata, files produced, and curves into a common output format. These files can later be ingested into a catalog. Once in a catalog, Sina provides powerful tools to query the content.

<img src=./assets/images/kosh_logo.png width="100" alt="Kosh Logo">  | [Public GitHub](https://github.com/LLNL/kosh) | [Documentation](https://kosh.readthedocs.io/en/latest)

* Kosh allows codes to store, query, share data via an easy-to-use Python API. Kosh lies on top of Sina and can use any database backend supported by Sina.

* Kosh allows the user to access and process data stored within or outside of the Sina catalog without worrying about format or location. The data remains where it was generated in the format it was generated. Via `loaders` Kosh renders location- and format-independent access to the data. In addition Kosh provides `transformers` and `operators` to further process and manipulate data from one or multiple, and possibly heterogenous, sources. Kosh also provides tools to move the data around while preserving the store's integrity.

* *Kosh* is a Hindi word that means *treasury*, which is derived from *Kosha*, a Sanskrit word that means *container* in either a direct or metaphorical sense. A fairly good translation would be *repository*.

## Data Analysis

<img src=./assets/images/trata_logo.png width="100" alt="Trata Logo">  | [Public Github](https://github.com/llnl/trata) | [Documentation](https://llnl-trata.readthedocs.io/en/latest)

* Trata is a sampling package designed to allow users to explore a parameter space by generating sample points, and are easy to utilize in Maestro and Merlin to generate ensembles of simulations. 

* Trata provides a common interface to multiple sampling methods including space-filling designs like Latin hypercube or a cartesian cross sampling. Users can also choose statistical model-based designs such as a multi-normal sampler or probability density function sampler which samples from any of scipy's statistical distributions. These space-filling and model-based designs are available in the `sampler` module. Many of these samplers are used by IBIS for sensitivity analysis and uncertainty quantification.

* Users can also generate samples sequentially with the `adaptive_sampler` module. After generating an initial set of points, candidate points are ranked according to similarity, model uncertainty, or both. Kosh operators have been provided in the `kosh_sampler` module to conveniently allow users to sequentially sample with data from a Sina catalog. 

<img src=./assets/images/ibis_logo.png width="80" alt="IBIS Logo">  **IBIS** | [Public Github](https://github.com/llnl/ibis) | [Documentation](https://llnl-ibis.readthedocs.io/en/latest)

* Interactive Bayesian Inference and Sensitivity, or IBIS, provides tools for sensitivity analysis and uncertainty quantification (UQ). 

* IBIS's `sensitivity` module provides users a variety of methods to better understand the global sensitivity for an output. Each input can be compared and their influence on the output can be conveniently shown in a score plot, rank plot, or network plot.

* Uncertainty quantification can be done with IBIS's `mcmc` module. The default MCMC sampler uses Bayesian inference to incorporate knowledge from experiments to better understand input parameters, and provide estimates of uncertainty to model predictions. A discrepancy MCMC sampler allows users to estimate model discrepancy. 

* IBIS also provides Kosh operators to conveniently allow users to perform sensitivity analysis or use MCMC sampling with data saved in a Kosh store.

## Data Visualization.

**PyDV** | [Public GitHub](https://github.com/LLNL/pydv) | [Documentation](https://pydv.readthedocs.io/en/latest/) | [Quick Start Guide](https://pydv.readthedocs.io/en/latest/getting_started.html)

* The Python Data Visualizer (PyDV) is a replacement for ULTRA written in Python. PyDV allows the presentation, manipulation, and analysis of 1D data sets, i.e., (x,y) pairs. Presentation refers to the capability to display and make hard copies of data plots. Manipulation refers to the capability to excerpt, shift, and scale data sets. Analysis refers to the capability to combine data sets in various ways to create new data sets.

* The principal object with which PyDV works is the curve. A curve is an object which consists of an array of x values, an array of y values, a number of points (the length of the x and y arrays), and an ASCII label. One of PyDV's major assets is its capability to work with curves with different time discretization.

**Sina** (see links above) offers a visualizer that creates matplotlib visualizations directly from Sina datastores. It includes an interactive mode for live configuration of data. Currently the available visualizer plots are scatter plots, line plots, histograms, and surface plots.

# Which WEAVE Tool Should I Use?

As seen above, there can be multiple tools under the same workflow categories that can be used to achieve your purpose. It can be a bit perplexing for a new user to decide which tool to use for their needs. Below is a short description of each tools' uses and strengths to help a user determine the suitability of using a particular WEAVE tool.

## Workflow Orchestration

### Maestro

Maestro is WEAVE's de-facto orchestration tool and should cover most of your needs.

### Merlin

Merlin is built on top of Maestro and is geared toward workflows that require 100,000s to 1,000,000s of simulations. It relies on a client/server model.

## Data Management

### Sina

Sina allows for integration with the simulation codes and can collect metadata, settings, files produced, curves, etc. in a common output format. These files can later be ingested into a catalog, allowing simple, performant, and powerful access via a Python API, and/or handled with a suite of postprocessing utilities. Sina additionally provides rapid and lightweight exploration of data (including interactive visualization) stored in these catalogs or the common output format.

### Kosh

Kosh is a Python tool built on top of Sina. It allows the user to access and process data stored within or outside of the Sina catalog without worrying about their format or location. The data stays where it was generated in the format it was generated. But via `loaders` Kosh renders the access to the data location- and format-independent. In addition Kosh provides `transformers` and `operators` to further process and manipulate data from one or mutliple, possibly heterogenous, sources.
Kosh also provides tools to move the data around while preserving the store's integrity.

## Data Analysis

### TRATA

Trata is a sampling package designed to allow users to explore a parameter space by generating sample points, and are easy to utilize in Maestro and Merlin to generate ensembles of simulations.  These can be generated with space-filling or model-informed methods, or sequentially with adaptive sampling. 

### IBIS

The Interactive Bayesian Inference and Sensitivity (IBIS) tool is designed to allow users to generate statistical models after physics simulations have run to completion. These models can be used to estimate uncertainty in future simulation runs for UQ analyses, or to perform sensitivity analyses.

## Data Visualization

There is only one WEAVE tool that falls exclusively under the Data Visualization category: PyDV. However, Sina has a growing set of visualization capabilities.


### PyDV
The Python Data Visualizer (PyDV) is a replacement for ULTRA written in python. PyDV allows the presentation, manipulation, and analysis of 1D data sets, i.e. (x,y) pairs. Presentation refers to the capability to display, and make hard copies of data plots. Manipulation refers to the capability to excerpt, shift, and scale data sets. Analysis refers to the capability to combine data sets in various ways to create new data sets. The principal object with which PyDV works is the curve. A curve is an object which consists of an array of x values, an array of y values, a number of points (the length of the x and y arrays), and an ASCII label. PyDV operates on curves.

### Sina

Sina offers a visualizer that creates matplotlib visualizations directly from Sina datastores. It includes an interactive mode for live configuration of data. At the moment the visualizer plots are: scatter plots, line plots, histograms, and surface plots.
