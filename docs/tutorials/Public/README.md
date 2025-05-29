# Overview

This is a repository for tutorials of WEAVE functionality.

In this directory you will find tutorials for various WEAVE tools, usually integrated together. For tutorials for a specific tool we recommend you go to that tool's documentation.

## Setting up a WEAVE environment

Run [setup.sh](../setup.sh)

## [Ball Bounce](bouncing_ball)

A demonstration of Sina and Maestro being used together to perform and analyze runs of a toy code that simulates a ball bouncing around in a 3D box. Maestro is used to launch suites of runs, each sharing a ball starting position but having a randomized velocity vector. The toy code outputs DSV, which is converted to Sina's format, ingested, and can then be explored in the included Jupyter notebooks.

## [Ball Bounce VVUQ](bouncing_ball_vvuq)

An extension of the Ball Bounce demo that generates ensembles of runs in order to perform Verification, Validation, and Uncertainty & Quantification. Trata also samples parameter points that are used by IBIS to infer parameter uncertainties in the bouncing ball simulations using IBIS' default Markov chain Monte Carlo (MCMC) method.

## [Ball Bounce LSTM](bouncing_ball_lstm)

An extension of the Ball Bounce demo that generates ensembles of runs in order to train a Long Short-Term Memory (LSTM) Recurrent Neural Network (RNN) to predict the transient path of the bouncing ball. It uses the Kosh threadsafe methods to safely call the Kosh store in parallel so that the parallel writes to the Kosh store don't block one another.

## [Ball Bounce Transformer](bouncing_ball_transformer)

An extension of the Ball Bounce demo that generates ensembles of runs in order to train a Transformer to predict the transient path of the bouncing ball. It uses the Kosh threadsafe methods to safely call the Kosh store in parallel so that the parallel writes to the Kosh store don't block one another.

## [Ball Bounce Metadata Machine Learning](bouncing_ball_metadata_machine_learning)

An extension of the Ball Bounce demo that generates ensembles of runs in order to train a machine learning model on the metadata of each run to predict the final x position of the bouncing ball. It uses the Kosh threadsafe methods to safely call the Kosh store in parallel so that the parallel writes to the Kosh store don't block one another. It uses the Kosh `store.to_dataframe()` method to extract all the metadata from all the runs into a Pandas DataFrame.

## [Pyranda Rayleigh-Taylor](pyranda_rayleigh_taylor)

Originally an Amazon Web Services demo, this tutorial shows how to run an ensemble of Rayleigh-Taylor simulations for a physics code (Pyranda). It shows how to run the ensembles, keep track of what was ran and run some UQ post-processing.

## [Digit Classification Machine Learning](digit_classification)

This tutorial will use Machine Learning to classify handwritten digits from the following dataset: [Optical Recognition of Handwritten Digits](https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits). This will showcase the use of Kosh Loaders which can read any type of data.
