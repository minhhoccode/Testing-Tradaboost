# coding: UTF-8
import numpy as np
import copy
from sklearn.tree import DecisionTreeRegressor
import keras

# =============================================================================
# Public estimators
# =============================================================================

def AdaBoost_R2_T(trans_S, response_S, test, weights,frozen_N, N = 20):
    """Boosting for Regression Transfer.

    Please feel free to open issues in the Github : https://github.com/Bin-Cao/TrAdaboost
    or 
    contact Bin Cao (bcao@shu.edu.cn)
    in case of any problems/comments/suggestions in using the code. 

    Parameters
    ----------
    trans_S : feature matrix 

    response_S : response of training data, real values 

    test : feature matrix of test data

    weights : initial data weights  

    frozen_N : int, the weights of first [frozen_N] instances in trans_S  are never modified 

    N : int, default=20, the number of weak estimators

    Examples
    --------
    import pandas as pd
    # training data
    tarin_data = pd.read_csv('Sdata.csv')
    # test data
    test_data = pd.read_csv('Tdata.csv')

    trans_S = tarin_data.iloc[:,:-1]
    response_S = tarin_data.iloc[:, -1]
    test = test_data.iloc[:,:-1]
    N = 10

    AdaBoost_R2_T(trans_S, response_S, test, weights, frozen_N, N)

    References
    ----------
    .. [1] Algorithm 3 
    Pardoe, D., & Stone, P. (2010, June). 
    Boosting for regression transfer. 
    In Proceedings of the 27th International Conference 
    on International Conference on Machine Learning (pp. 863-870).
    """


    trans_data =  copy.deepcopy(trans_S)
    trans_response =  copy.deepcopy(response_S)

    row_S = trans_S.shape[0]
    row_T = test.shape[0]


    test_data = np.concatenate((trans_data, test), axis=0)

    print("SHape", test_data.shape)
    # initilize data weights
    _weights = weights / sum(weights)

    # Save prediction responses and bata_t
    bata_T = np.zeros(N)
    result_response = np.ones([row_S + row_T, N])

    # Save the prediction responses of test data 
    predict = np.zeros(row_T)

    trans_data = np.asarray(trans_data, order='C')
    trans_response = np.asarray(trans_response, order='C')
    test_data = np.asarray(test_data, order='C')

    for i in range(N):
        _weights = calculate_P(_weights, frozen_N)
        result_response[:, i] = train_reg(trans_data, trans_response, test_data, _weights)
        error_rate = calculate_error_rate(response_S, result_response[0: row_S, i],_weights)
        if error_rate > 0.5 or error_rate <= 1e-10: break

        bata_T[i] = error_rate / (1 - error_rate)

        # Changing the data weights of unfrozen training data
        D_t = np.abs(result_response[frozen_N:row_S, i] - response_S[frozen_N:row_S]).max()
        for j in range(row_S - frozen_N):
            weights[frozen_N + j] = weights[frozen_N + j] * np.power(bata_T[i], (1-np.abs(result_response[frozen_N + j, i] - response_S[frozen_N+j])/D_t))
    
    
    Cal_res = result_response[row_S:,:]
    # Sort the predictions
    sorted_idx = np.argsort(Cal_res, axis=1)

    # Find index of median prediction for each sample
    weight_cdf = np.cumsum(bata_T[sorted_idx], axis=1)
    # return True - False
    median_or_above = weight_cdf >= 0.5 * weight_cdf[:, -1][:, np.newaxis]
    median_idx = median_or_above.argmax(axis=1)

    median_estimators = sorted_idx[np.arange(row_T), median_idx]
    for j in range(row_T):
        predict[j] = Cal_res[j,median_estimators[j]]
    return predict

def calculate_P(weights,frozen_N):
    total = np.sum(weights[-frozen_N:])
    weights[-frozen_N:] / total
    return np.asarray(weights, order='C')

def train_reg(trans_data, trans_response, test_data, weights):
    print(trans_data.shape)
    # weight resampling 
    cdf = np.cumsum(weights)
    cdf_ = cdf / cdf[-1]
    uniform_samples = np.random.random_sample(len(trans_data))
    bootstrap_idx = cdf_.searchsorted(uniform_samples, side='right')
    # searchsorted returns a scalar
    bootstrap_idx = np.array(bootstrap_idx, copy=False)
    # reg = DecisionTreeRegressor(max_depth=2,splitter='random',max_features="log2",random_state=0)
    # change reg to keras LSTM
    reg = keras.models.Sequential()
    reg.add(keras.layers.LSTM(32, input_shape=(1, 10)))
    reg.add(keras.layers.Dense(1))
    reg.compile(loss='mean_squared_error', optimizer='adam')
    # reg.fit(trans_data[bootstrap_idx], trans_response[bootstrap_idx])
    reg.fit(trans_data[bootstrap_idx], trans_response[bootstrap_idx], epochs=20, batch_size=32, verbose=2)
    return reg.predict(test_data)

def calculate_error_rate(response_R, response_H, weight):
    total = np.abs(response_R - response_H).max()
    return np.sum(weight[:] * np.abs(response_R - response_H) / total)