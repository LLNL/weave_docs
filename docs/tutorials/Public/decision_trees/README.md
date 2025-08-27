# Decision Trees

This tutorial will use Machine Learning Decision Trees for classification [Heart Failure Prediction Dataset (Classification, Label: HeartDisease)](https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction) and regression [Medical Cost Personal Datasets (Regression, Label: charges)](https://www.kaggle.com/datasets/mirichoi0218/insurance). This will showcase the use of Kosh Ensembles for grouping datasets together and `.to_dataframe()` to extract data.

## Overview

Kosh is a powerful database tool that can be used to store, load, and modify different types of data such as scalar/string data, timeseries data, metadata, and different filetypes. We will use Kosh to store the classification and regression data. We will then export the data via `.to_dataframe()` for the machine learning models. We will use [SciKit Learn's](https://scikit-learn.org/stable/) machine learning algorithms for this tutorial.

## Visualization Decision Trees Kosh Notebook

This notebook allows the user to train a machine learning model and visualize its predictions. The notebook can be updated as needed to modify the machine learning model and post-process the prediction results. The notebook has more details on what training a machine learning model entails.

Below is the classification and regression decision trees of the machine learning model prediction which showcases its logic. This is where fine tuning the model becomes an "art" since adjusting these values could give a completely different prediction. What works for this set of data might not work for another. Note that due to the randomness of the data split, the predictions below will not be the same each time.

```
from sklearn import tree

# Classification
classification_tree = tree.DecisionTreeClassifier()

# Regression
regression_tree = tree.DecisionTreeRegressor()
```

### Classification Tree

![Machine Learning Model Prediction: Classification Tree](../../../assets/images/Public/decision_trees/classification_tree.png)

### Regression Tree

![Machine Learning Model Prediction: Regression Tree](../../../assets/images/Public/decision_trees/regression_tree.png)

## How to run

1. Run `setup.sh` in the top directory to create a virtual environment with all necessary dependencies and install the jupyter kernel.

2. Run `source weave_demos_venv/bin/activate` to enter the virtual environment (you can `deactivate` when you've finished the demo to exit it) and `cd` back into this directory.

3. Run `visualization_decision_trees_machine_learning_kosh.ipynb` as it contains all the necessary information.

## Content overview

### Starting files:

- `visualization_decision_trees_machine_learning_kosh.ipynb`: A Jupyter notebook to train the machine learning model.

### Files created by the demo:

- `*tree.png`: Decision trees for the machine learning model.
- `*confusion_matrix.png`: Confusion matrices of the Train, Validation, and Test datasets for the classification machine learning model.
- `*scatter_plot.png`: Confusion matrices of the Train, Validation, and Test datasets for the regression machine learning model.