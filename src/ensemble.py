# -*- coding: utf-8 -*-
"""Ensemble.ipynb

Automatically generated by Colaboratory.

I started this competition investigating neural networks with this kernel https://www.kaggle.com/mulargui/keras-nn
Now switching to using ensembles in this new kernel. As of today V6 is the most performant version.
You can find all my notes and versions at https://github.com/mulargui/kaggle-Classify-forest-types
"""

# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in 

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

#load data
dftrain=pd.read_csv('/kaggle/input/learn-together/train.csv')
dftest=pd.read_csv('/kaggle/input/learn-together/test.csv')

####### DATA PREPARATION #####
#split train data in features and labels
y = dftrain.Cover_Type
x = dftrain.drop(['Id','Cover_Type'], axis=1)

# split test data in features and Ids
Ids = dftest.Id
x_predict = dftest.drop('Id', axis=1)

# one data set with all features
X = pd.concat([x,x_predict],keys=[0,1])

###### FEATURE ENGINEERING #####
#https://www.kaggle.com/mancy7/simple-eda
#Soil_Type7, Soil_Type15 are non-existent in the training set, nothing to learn
#I have problems with np.where if I do this, postponed
#X.drop(["Soil_Type7", "Soil_Type15"], axis = 1, inplace=True)

#https://www.kaggle.com/evimarp/top-6-roosevelt-national-forest-competition
from itertools import combinations
from bisect import bisect
X['Euclidean_distance_to_hydro'] = (X.Vertical_Distance_To_Hydrology**2 
                                         + X.Horizontal_Distance_To_Hydrology**2)**.5

cols = [
        'Horizontal_Distance_To_Roadways',
        'Horizontal_Distance_To_Fire_Points',
        'Horizontal_Distance_To_Hydrology',
]
X['distance_mean'] = X[cols].mean(axis=1)
X['distance_sum'] = X[cols].sum(axis=1)
X['distance_road_fire'] = X[cols[:2]].mean(axis=1)
X['distance_hydro_fire'] = X[cols[1:]].mean(axis=1)
X['distance_road_hydro'] = X[[cols[0], cols[2]]].mean(axis=1)
    
X['distance_sum_road_fire'] = X[cols[:2]].sum(axis=1)
X['distance_sum_hydro_fire'] = X[cols[1:]].sum(axis=1)
X['distance_sum_road_hydro'] = X[[cols[0], cols[2]]].sum(axis=1)
    
X['distance_dif_road_fire'] = X[cols[0]] - X[cols[1]]
X['distance_dif_hydro_road'] = X[cols[2]] - X[cols[0]]
X['distance_dif_hydro_fire'] = X[cols[2]] - X[cols[1]]
    
# Vertical distances measures
colv = ['Elevation', 'Vertical_Distance_To_Hydrology']
X['Vertical_dif'] = X[colv[0]] - X[colv[1]]
X['Vertical_sum'] = X[colv].sum(axis=1)
    
SHADES = ['Hillshade_9am', 'Hillshade_Noon', 'Hillshade_3pm']
    
X['shade_noon_diff'] = X['Hillshade_9am'] - X['Hillshade_Noon']
X['shade_3pm_diff'] = X['Hillshade_Noon'] - X['Hillshade_3pm']
X['shade_all_diff'] = X['Hillshade_9am'] - X['Hillshade_3pm']
X['shade_sum'] = X[SHADES].sum(axis=1)
X['shade_mean'] = X[SHADES].mean(axis=1)
  
X['ElevationHydro'] = X['Elevation'] - 0.25 * X['Euclidean_distance_to_hydro']
X['ElevationV'] = X['Elevation'] - X['Vertical_Distance_To_Hydrology']
X['ElevationH'] = X['Elevation'] - 0.19 * X['Horizontal_Distance_To_Hydrology']

X['Elevation2'] = X['Elevation']**2
X['ElevationLog'] = np.log1p(X['Elevation'])

X['Aspect_cos'] = np.cos(np.radians(X.Aspect))
X['Aspect_sin'] = np.sin(np.radians(X.Aspect))
#df['Slope_sin'] = np.sin(np.radians(df.Slope))
X['Aspectcos_Slope'] = X.Slope * X.Aspect_cos
#df['Aspectsin_Slope'] = df.Slope * df.Aspect_sin
    
cardinals = [i for i in range(45, 361, 90)]
points = ['N', 'E', 'S', 'W']
X['Cardinal'] = X.Aspect.apply(lambda x: points[bisect(cardinals, x) % 4])
d = {'N': 0, 'E': 1, 'S': 0, 'W':-1}
X['Cardinal'] = X.Cardinal.apply(lambda x: d[x])

#https://www.kaggle.com/jakelj/basic-ensemble-model
X['Avg_shade'] = ((X['Hillshade_9am'] + X['Hillshade_Noon'] + X['Hillshade_3pm']) / 3)
X['Morn_noon_int'] = ((X['Hillshade_9am'] + X['Hillshade_Noon']) / 2)
X['noon_eve_int'] = ((X['Hillshade_3pm'] + X['Hillshade_Noon']) / 2)

#adding features based on https://douglas-fraser.com/forest_cover_management.pdf pages 21,22
#note: not all climatic and geologic codes have a soil type
columns=['Soil_Type1', 'Soil_Type2', 'Soil_Type3', 'Soil_Type4', 'Soil_Type5', 'Soil_Type6']
X['Climatic2'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type7', 'Soil_Type8']
X['Climatic3'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type9', 'Soil_Type10', 'Soil_Type11', 'Soil_Type12', 'Soil_Type13']
X['Climatic4'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type14', 'Soil_Type15']
X['Climatic5'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type16', 'Soil_Type17', 'Soil_Type18']
X['Climatic6'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type19', 'Soil_Type20', 'Soil_Type21', 'Soil_Type22', 'Soil_Type23', 'Soil_Type24',
    'Soil_Type25', 'Soil_Type26', 'Soil_Type27', 'Soil_Type28', 'Soil_Type29', 'Soil_Type30',
    'Soil_Type31', 'Soil_Type32', 'Soil_Type33', 'Soil_Type34']
X['Climatic7'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type35', 'Soil_Type36', 'Soil_Type37', 'Soil_Type38', 'Soil_Type39', 'Soil_Type40']
X['Climatic8'] = np.select([X[columns].sum(1).gt(0)], [1])

columns=['Soil_Type14', 'Soil_Type15', 'Soil_Type16', 'Soil_Type17', 'Soil_Type19', 'Soil_Type20',
    'Soil_Type21']
X['Geologic1'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type9', 'Soil_Type22', 'Soil_Type23']
X['Geologic2'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type7', 'Soil_Type8']
X['Geologic5'] = np.select([X[columns].sum(1).gt(0)], [1])
columns=['Soil_Type1', 'Soil_Type2', 'Soil_Type3', 'Soil_Type4', 'Soil_Type5', 'Soil_Type6',
    'Soil_Type10', 'Soil_Type11', 'Soil_Type12', 'Soil_Type13', 'Soil_Type18', 'Soil_Type24',
    'Soil_Type25', 'Soil_Type26', 'Soil_Type27', 'Soil_Type28', 'Soil_Type29', 'Soil_Type30',
    'Soil_Type31', 'Soil_Type32', 'Soil_Type33', 'Soil_Type34', 'Soil_Type35', 'Soil_Type36', 
    'Soil_Type37', 'Soil_Type38', 'Soil_Type39', 'Soil_Type40']
X['Geologic7'] = np.select([X[columns].sum(1).gt(0)], [1])

#Reversing One-Hot-Encoding to Categorical attributes, several articles recommend it for decision tree algorithms
#Doing it for Soil_Type, Wilderness_Area, Geologic and Climatic
X['Soil_Type']=np.where(X.loc[:, 'Soil_Type1':'Soil_Type40'])[1] +1
X.drop(X.loc[:,'Soil_Type1':'Soil_Type40'].columns, axis=1, inplace=True)

X['Wilderness_Area']=np.where(X.loc[:, 'Wilderness_Area1':'Wilderness_Area4'])[1] +1
X.drop(X.loc[:,'Wilderness_Area1':'Wilderness_Area4'].columns, axis=1, inplace=True)

X['Climatic']=np.where(X.loc[:, 'Climatic2':'Climatic8'])[1] +1
X.drop(X.loc[:,'Climatic2':'Climatic8'].columns, axis=1, inplace=True)

X['Geologic']=np.where(X.loc[:, 'Geologic1':'Geologic7'])[1] +1
X.drop(X.loc[:,'Geologic1':'Geologic7'].columns, axis=1, inplace=True)

from sklearn.preprocessing import StandardScaler
StandardScaler(copy=False).fit_transform(X)

# Adding Gaussian Mixture features to perform some unsupervised learning hints from the full data
#https://www.kaggle.com/arateris/2-layer-k-fold-learning-forest-cover 
#https://www.kaggle.com/stevegreenau/stacking-multiple-classifiers-clustering
from sklearn.mixture import GaussianMixture
X['GM'] = GaussianMixture(n_components=15).fit_predict(X)

#https://www.kaggle.com/arateris/2-layer-k-fold-learning-forest-cover 
# Add PCA features
from sklearn.decomposition import PCA
pca = PCA(n_components=0.99).fit(X)
trans = pca.transform(X)

for i in range(trans.shape[1]):
    col_name= 'pca'+str(i+1)
    X[col_name] = trans[:,i]

#https://www.kaggle.com/kwabenantim/forest-cover-stacking-multiple-classifiers
# Scale and bin features
from sklearn.preprocessing import MinMaxScaler
MinMaxScaler((0, 100),copy=False).fit_transform(X)
#X = np.floor(X).astype('int8')

print("Completed feature engineering!")

#break it down again in train and test
x,x_predict = X.xs(0),X.xs(1)

# Commented out IPython magic to ensure Python compatibility.
###### THIS IS THE ENSEMBLE MODEL SECTION ######
#https://www.kaggle.com/kwabenantim/forest-cover-stacking-multiple-classifiers
import random
randomstate = 1
random.seed(randomstate)
np.random.seed(randomstate)

from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
ab_clf = AdaBoostClassifier(n_estimators=200,
                            base_estimator=DecisionTreeClassifier(
                                min_samples_leaf=2,
                                random_state=randomstate),
                            random_state=randomstate)

#max_features = min(30, x.columns.size)
max_features = 30
from sklearn.ensemble import ExtraTreesClassifier
et_clf = ExtraTreesClassifier(n_estimators=300,
                              min_samples_leaf=2,
                              min_samples_split=2,
                              max_depth=50,
                              max_features=max_features,
                              random_state=randomstate,
                              n_jobs=1)

from lightgbm import LGBMClassifier
lg_clf = LGBMClassifier(n_estimators=300,
                        num_leaves=128,
                        verbose=-1,
                        random_state=randomstate,
                        n_jobs=1)

from sklearn.ensemble import RandomForestClassifier
rf_clf = RandomForestClassifier(n_estimators=300,
                                random_state=randomstate,
                                n_jobs=1)

#Added a KNN classifier to the ensemble
#https://www.kaggle.com/edumunozsala/feature-eng-and-a-simple-stacked-model
from sklearn.neighbors import KNeighborsClassifier
knn_clf = KNeighborsClassifier(n_neighbors=y.nunique(), n_jobs=1)

#added several more classifiers at once
#https://www.kaggle.com/edumunozsala/feature-eng-and-a-simple-stacked-model
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
bag_clf = BaggingClassifier(base_estimator=DecisionTreeClassifier(criterion = 'entropy', max_depth=None, 
                                                    min_samples_split=2, min_samples_leaf=1,max_leaf_nodes=None,
                                                    max_features='auto',
                                                    random_state = randomstate),
                    n_estimators=500,max_features=0.75, max_samples=1.0, random_state=randomstate,n_jobs=1,verbose=0)

from sklearn.linear_model import LogisticRegression
lr_clf = LogisticRegression(max_iter=1000,
                       n_jobs=1,
                       solver= 'lbfgs',
                       multi_class = 'multinomial',
                       random_state=randomstate,
                       verbose=0)

#https://www.kaggle.com/bustam/6-models-for-forest-classification
from catboost import CatBoostClassifier
cat_clf = CatBoostClassifier(n_estimators =300, 
                        eval_metric='Accuracy',
                        metric_period=200,
                        max_depth = None, 
                        random_state=randomstate,
                        verbose=0)

#https://www.kaggle.com/jakelj/basic-ensemble-model
from sklearn.experimental import enable_hist_gradient_boosting
from sklearn.ensemble import HistGradientBoostingClassifier
hbc_clf = HistGradientBoostingClassifier(max_iter = 500, max_depth =25, random_state = randomstate)

ensemble = [('AdaBoostClassifier', ab_clf),
            ('ExtraTreesClassifier', et_clf),
            ('LGBMClassifier', lg_clf),
            #('KNNClassifier', knn_clf),
            ('BaggingClassifier', bag_clf),
            #('LogRegressionClassifier', lr_clf),
            #('CatBoostClassifier', cat_clf),
            #('HBCClassifier', hbc_clf),
            ('RandomForestClassifier', rf_clf)
]

#Cross-validating classifiers
from sklearn.model_selection import cross_val_score
for label, clf in ensemble:
    score = cross_val_score(clf, x, y,
                            cv=10,
                            scoring='accuracy',
                            verbose=0,
                            n_jobs=-1)
    print("Accuracy: %0.2f (+/- %0.2f) [%s]" 
#         % (score.mean(), score.std(), label))

# Fitting stack
from mlxtend.classifier import StackingCVClassifier
stack = StackingCVClassifier(classifiers=[ab_clf, et_clf, lg_clf, 
                                          bag_clf,
                                          rf_clf],
                             meta_classifier=rf_clf,
                             cv=10,
                             stratify=True,
                             shuffle=True,
                             use_probas=True,
                             use_features_in_secondary=True,
                             verbose=0,
                             random_state=randomstate)
stack = stack.fit(x, y)

print("Completed modeling!")

#make predictions
y_predict = stack.predict(x_predict)
y_predict = pd.Series(y_predict, index=x_predict.index, dtype=y.dtype)

print("Completed predictions!")

# Save predictions to a file for submission
output = pd.DataFrame({'Id': Ids,
                       'Cover_Type': y_predict})
output.to_csv('submission.csv', index=False)

#create a link to download the file    
from IPython.display import FileLink
FileLink(r'submission.csv')