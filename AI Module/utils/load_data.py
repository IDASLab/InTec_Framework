import dask.dataframe as dd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

import pandas as pd
import numpy as np


random_seed = 666

__all__ = ["custome_read_data"]

column_names = {
    0: "acc_ch_x",
    1: "acc_ch_y",
    2: "acc_ch_z",
    3: "elec_signal_lead1",
    4: "elec_signal_lead2",
    5: "acc_la_x",
    6: "acc_la_y",
    7: "acc_la_z",
    8: "gyr_la_x",
    9: "gyr_la_y",
    10: "gyr_la_z",
    11: "mag_la_x",
    12: "mag_la_y",
    13: "mag_la_z",
    14: "acc_rw_x",
    15: "acc_rw_y",
    16: "acc_rw_z",
    17: "gyr_rw_x",
    18: "gyr_rw_y",
    19: "gyr_rw_z",
    20: "mag_rw_x",
    21: "mag_rw_y",
    22: "mag_rw_z",
    23: "activity",
}

def _apply_outlier_detection(X_train, y_train, X_test, y_test, outlier_algo='IsolationForest'):
    
        if outlier_algo not in ["IsolationForest", "LocalOutlierFactor"]:
            raise ValueError(
                "{0} is not valid option".format(
                    outlier_algo
                )
            )
        
        if outlier_algo == "IsolationForest":
            fitted_outlier = IsolationForest().fit(X_train, y_train)
        else:
            fitted_outlier = LocalOutlierFactor().fit(X_train, y_train)
            
        
        predicted_outliers = pd.DataFrame(fitted_outlier.predict(X_train))
        predicted_outliers_test  = pd.DataFrame(fitted_outlier.predict(X_test))
        
   
        ## Finding outliers indexes in dataframe
        predicted_outliers = predicted_outliers.index[predicted_outliers[0] == -1].tolist()
        ## Finding outliers indexes in test dataframe
        predicted_outliers_test = predicted_outliers_test.index[predicted_outliers_test[0] == -1].tolist()
        
        ## Removing outliers from dataframe
        print("Number of outliers: ", len(predicted_outliers))
        X_train = pd.DataFrame(X_train)

        X_train.drop(X_train.index[predicted_outliers],inplace=True)
        y_train.drop(y_train.index[predicted_outliers], inplace=True)

        ## Removing outliers from test dataframe
        X_test = pd.DataFrame(X_test)

        X_test.drop(X_test.index[predicted_outliers_test],inplace=True)
        y_test.drop(y_test.index[predicted_outliers_test], inplace=True)

        return fitted_outlier, X_train, y_train, X_test, y_test
               
def _apply_normalization(X_train, X_test):
    
    fitted_scaler = StandardScaler().fit(X_train)
    X_train_scaled = fitted_scaler.transform(X_train)
    X_test_scaled = fitted_scaler.transform(X_test)
    
    return fitted_scaler, X_train_scaled, X_test_scaled

def _apply_PCA(X_train, X_test, n_components=0.6):
    
    pca = PCA(n_components=n_components)

    fitted_pca = pca.fit(X_train)
    X_train_pca = pd.DataFrame(fitted_pca.transform(X_train))
    X_test_pca = pd.DataFrame(fitted_pca.transform(X_test))
    
    return fitted_pca, X_train_pca, X_test_pca


def custome_read_data(path_to_train_files='../data/mHealth_subject*.log',
                      path_to_test_files='../data/mHealth_subject_test*.log',
                      dim_reduction=None,
                      outlier_detection="IsolationForest",
                      just_load=False):
    """
    This function read multiple .log files and merge them into one
    dask dataframe.
    Resample activity 0 (null class) to 30720 observations per EDA phase.
    
    It applies outlier detection and dimensionality reduction on data.
    
    Args:
        path (str): . Defaults to "../../data/mHealth_subject*.log".
        dim_reduction (str): dimensionality reduction algorithms including PCA.
        outlier_detection (str): outlierdetection algorithms including LocalOutlierFactor and IsolationForest.
    
    Return:
    data frame, the fitted model of dim-reduction and outlier detection.
    
    """

    mhealth_data_train = dd.read_csv(urlpath=path_to_train_files, sep="\t", header=None).rename(
        columns=column_names
        )

    mhealth_data_test = dd.read_csv(urlpath=path_to_test_files, sep="\t", header=None).rename(
        columns=column_names
        )
      
    mhealth_data_train_zero_label = mhealth_data_train[mhealth_data_train["activity"] == 0]
    mhealth_data_train_non_zero_label = mhealth_data_train[mhealth_data_train["activity"] != 0]
    
    mhealth_data_test_zero_label = mhealth_data_test[mhealth_data_test["activity"] == 0]
    mhealth_data_test_non_zero_label = mhealth_data_test[mhealth_data_test["activity"] != 0]
    

    mhealth_data_train_zero_label = mhealth_data_train_zero_label.sample(
        frac=0.03520715145, random_state=random_seed
    )
    
    mhealth_data_test_zero_label = mhealth_data_test_zero_label.sample(
        frac=0.03520715145, random_state=random_seed
    )
    
    mhealth_data_train = dd.concat([mhealth_data_train_zero_label, mhealth_data_train_non_zero_label]).compute()
    mhealth_data_test = dd.concat([mhealth_data_test_zero_label, mhealth_data_test_non_zero_label]).compute()
    
    
    # Split data between predictors and output variable
    X_train = mhealth_data_train.drop(['activity'], axis=1)
    X_train.reset_index(inplace=True)
    X_train.drop(['index'], axis=1, inplace=True)

    y_train = pd.DataFrame(mhealth_data_train['activity'])
    y_train.reset_index(inplace=True)
    y_train.drop(['index'], axis=1, inplace=True)

    X_test = mhealth_data_test.drop(['activity'], axis=1)
    X_test.reset_index(inplace=True)
    X_test.drop(['index'], axis=1, inplace=True)

    y_test = pd.DataFrame(mhealth_data_test['activity'])
    y_test.reset_index(inplace=True)
    y_test.drop(['index'], axis=1, inplace=True)
    
    if just_load:
        return X_train, y_train, X_test, y_test

    else:
        
        fitted_scaler, X_train_scaled, X_test_scaled = _apply_normalization(X_train, X_test)
    
        fitted_outlier, X_train_removed, y_train, X_test_removed, y_test = _apply_outlier_detection(X_train_scaled, y_train, X_test_scaled, y_test, outlier_algo=outlier_detection)
    
        fitted_pca, X_train_pca, X_test_pca = _apply_PCA(X_train_removed, X_test_removed)
    
        return fitted_scaler, fitted_outlier, fitted_pca, X_train_pca, y_train, X_test_pca, y_test
        #return fitted_scaler, fitted_outlier, X_train_removed, y_train, X_test_removed, y_test