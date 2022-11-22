#!/usr/bin/env python3

import sys
import argparse
from epanet import toolkit as en
import dcritsim
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
from sklearn.manifold import MDS
import matplotlib.patches as mpatches
from matplotlib.legend_handler import HandlerLine2D
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
import random
import xlwt
from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasRegressor
import keras.backend as K
from sklearn.model_selection import GridSearchCV
#from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.metrics import make_scorer
from sklearn import metrics



def ANN_regression (optimizer='adam'): 

    # create ANN model
    model = Sequential()
 
    # Defining the Input layer and FIRST hidden layer, both are same!
    model.add(Dense(units=25, input_dim=3, kernel_initializer='normal', activation='relu'))
 
    # Defining the Second layer of the model
    # after the first layer we don't have to specify input_dim as keras configure it automatically
    model.add(Dense(units=12, kernel_initializer='normal', activation='sigmoid'))
    model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
    model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
    model.add(Dense(units=2, kernel_initializer='normal', activation='sigmoid'))
 
    # The output neuron is a single fully connected node 
    # Since we will be predicting a single number
    model.add(Dense(1, kernel_initializer='normal', activation='linear'))
    

 
    # Compiling the model
    # mse: mean sequare error
    # mae: mean absolute error
    # mape: mean absolute percentage error
    # cosine: cosine_proximity
    model.compile(loss='mean_squared_error', optimizer=optimizer,metrics=['mae','accuracy'] )
    
    #model.compile(loss='mse', optimizer='adam',metrics=['mae','mse','accuracy'] )

    model.summary()
    return model

def FunctionFindBestParams(X_train, y_train, X_test, y_test):    
        # Defining the list of hyper parameters to try
        #batch_size_list=[5, 10, 15, 20,30,40]
        batch_size_list=[40]
        epoch_list  =   [500]
        SearchResultsData=pd.DataFrame(columns=['TrialNumber', 'Parameters', 'Accuracy'])
        # initializing the trials
        TrialNumber=0
        for batch_size_trial in batch_size_list:
            for epochs_trial in epoch_list:
                TrialNumber+=1
                # create ANN model
                model = Sequential()
                # Defining the Input layer and FIRST hidden layer, both are same!
                model.add(Dense(units=25, input_dim=3, kernel_initializer='normal', activation='sigmoid'))
 
                # Defining the Second layer of the model
                # after the first layer we don't have to specify input_dim as keras configure it automatically
                model.add(Dense(units=25, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=12, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=5, kernel_initializer='normal', activation='sigmoid'))
                model.add(Dense(units=2, kernel_initializer='normal', activation='sigmoid'))
 
                # The output neuron is a single fully connected node 
                # Since we will be predicting a single number
                model.add(Dense(1, kernel_initializer='normal', activation='linear'))

 
                # Compiling the model
                model.compile(loss='mean_squared_error', optimizer='adam')
 
                # Fitting the ANN to the Training set
                model.fit(X_train, y_train ,batch_size = batch_size_trial, epochs = epochs_trial, verbose=0)
 
                MAPE = np.mean(100 * (np.abs(y_test-model.predict(X_test))/y_test))
            
                # printing the results of the current iteration
                print(TrialNumber, 'Parameters:','batch_size:', batch_size_trial,'-', 'epochs:',epochs_trial, 'Accuracy:', 100-MAPE)
            
                SearchResultsData=SearchResultsData.append(pd.DataFrame(data=[[TrialNumber, batch_size_trial,epochs_trial, 100-MAPE]],
                                                                    columns=['TrialNumber', 'batch_size_trial','epochs_trial', 'Accuracy'] ))
        return(SearchResultsData)

    

def loss_plot_training(loss,val_loss):
    epoches = range (1, len(loss)+1)
    plt.plot(epoches,loss,'b',label='Training loss')
    plt.plot(epoches,val_loss,'r',label='Validation loss')
    plt.title('Training and Validation loss')
    plt.xlabel('Epoches')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    return 0


def acc_plot(acc,val_acc):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    epoches = range (1, len(loss)+1)
    plt.plot(epoches,acc,'y',label='Training MAE')
    plt.plot(epoches,val_acc,'r',label='Validation MAE')
    plt.title('Training and Validation MAE')
    plt.xlabel('Epoches')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()
    return 0

def headdiff_length (head_diff,Length_,Length_pred):
    plt.plot(head_diff,Length_,'r',label=' length')
    plt.plot(head_diff,Length_pred,'b',label='predected length',linestyle='--')
    plt.title('Head difference VS Length')
    plt.xlabel('Head diff')
    plt.ylabel('Length')
    plt.legend()
    plt.show()

def headdiff_lengthdiff (head_diff,length_diff):
    plt.plot(head_diff,length_diff,'r',label='length')
    plt.title('Accuracy VS length')
    plt.xlabel('Head diff')
    plt.ylabel('length')
    plt.legend()
    plt.show()

def get_column(col1):
        col = col1
        data_ = []
        for i in range(len(col)):
            y= float(col[i])
            data_.append(y)
        return data_




def main():

    data = pd.read_excel('Training_data.xls', header=None)
    print (data)
    length = []
    for i in range(1,1001):
        length.append(int(i-1))
    df = pd.DataFrame(length)
    
    df.set_axis(["Length"], axis=1,inplace=True)
    print ('df=',df)
        
    data = pd.read_excel('Training_data.xls', index_col=0)
    result = pd.concat([data, df], axis=1)
    result_new = result.drop(result.index[0])
 
    print ('result_new =')
    print (result_new)
    print ('')

    # shuffel data
    result_new = result_new.sample(frac = 1)        
    print ('result_new=',result_new)
    print ('')
    print ('len(result_new)',len(result_new))
    print ('')

    # create ANN model
    TargetVariable=['Length']
    Predictors=['Node1_pressure_c_5', 'Node2_pressure_c_5','Link1_flow_c_5',]

 
    X=result_new[Predictors].values
    y=result_new[TargetVariable].values

    print ('')
    print ('X_innan =',X)
    print ('')
    print ('y_innan =',y)
    ## Sandardization of data ###
    PredictorScaler=StandardScaler()
    TargetVarScaler=StandardScaler()
 
    # Storing the fit object for later reference
    PredictorScalerFit=PredictorScaler.fit(X)
    TargetVarScalerFit=TargetVarScaler.fit(y)

    print ('PredictorScalerFit=',PredictorScalerFit)
 
    # Generating the standardized values of X and y
    X=PredictorScalerFit.transform(X)
    y=TargetVarScalerFit.transform(y)
    
    # Split the data into training and testing set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=20)

    # Quick sanity check with the shapes of Training and testing datasets
    print(X_train.shape)
    print(y_train.shape)
    print(X_test.shape)
    print(y_test.shape)
    print(y_test)

    X_train_scaled = X_train
    X_test_scaled = X_test
    print (X_test_scaled)
    #####################################################################################################
    print ('')
    print ('#'*100)

    ResultsData=FunctionFindBestParams(X_train_scaled, y_train, X_test_scaled, y_test)

    print ('ResultsData=',ResultsData)

    NET1 = get_column(list(ResultsData.Accuracy))
    NET2 = get_column(list(ResultsData.epochs_trial))
    NET3 = get_column(list(ResultsData.batch_size_trial))
    #print ('NET1=',NET1)
    #print ('NET2=',NET2)
    #print ('NET3=',NET3)
    print ('')
    

    def myMax(list1,list2,list3):
        # Assume first number in list is largest
        # initially and assign it to variable "max"        
        max = list1[0]
        max_2 = list2[0]
        max_3 = list3[0]
        # Now traverse through the list and compare
        # each number with "max" value. Whichever is
        # largest assign that value to "max'.
        i = 0
        for x in list1:            
            if x > max :
                max = x
                max_2 = list2[i]
                max_3 = list3[i]
            i +=1
      
        # after complete traversing the list 
        # return the "max" value
        return max,max_2,max_3
    acc,epo,bach = myMax(NET1,NET2,NET3)

    print("Largest element is:", myMax(NET1,NET2,NET3))    
    # Fitting the ANN to the Training set
    model = ANN_regression()
    history = model.fit(X_train, y_train ,batch_size = int(bach), epochs =int(epo), verbose=2,validation_split=0.2)
    

    #ANN_regression (result_new)
    #model = ANN_regression()
    # Fitting the ANN to the Training set
    #history = model.fit(X_train_scaled,y_train,validation_split=0.2,epochs=100)
    #history = model.fit(X_train_scaled, y_train, epochs=300, batch_size=20, verbose=2,validation_split=0.2)
    
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    loss_plot_training(loss,val_loss)
    
    # Generating Predictions on training data
    Predictions=model.predict(X_train)
    # Scaling the predicted Price data back to original price scale
    Predictions=TargetVarScalerFit.inverse_transform(Predictions)
    # Scaling the y_test Price data back to original price scale
    y_train_orig=TargetVarScalerFit.inverse_transform(y_train)
    # Scaling the test data back to original scale
    Train_Data=PredictorScalerFit.inverse_transform(X_train)
    Train_Data=pd.DataFrame(data=Train_Data, columns=Predictors)
    Train_Data['Length']=y_train_orig
    Train_Data['PredictedLength']=Predictions
    Train_Data.head()
    #print ('y_train_orig=',y_train_orig)
    print ('')
    print (Train_Data)
    # Computing the absolute percent error
    APE=100*(abs(Train_Data['Length']-Train_Data['PredictedLength'])/Train_Data['Length'])
    Train_Data['APE']=APE 
    print('The Accuracy of ANN model is:', 100-np.mean(APE))
    Train_Data.sort_values(by=['Length'], inplace=True)
    print ('Train_Data=')
    print (Train_Data)
    Length_ = get_column(list(Train_Data.Length))
    Length_pred = get_column(list(Train_Data.PredictedLength))
    Node1_pressure = get_column(list(Train_Data.Node1_pressure_c_5))
    Node2_pressure = get_column(list(Train_Data.Node2_pressure_c_5))       
    head_diff = []
    for i in range(len(Node1_pressure)):
        diff = Node2_pressure[i] - Node1_pressure[i]
        head_diff.append(diff)
    length_diff = []
    for i in range(len(Node1_pressure)):
        diff = Length_[i] - Length_pred[i]
        length_diff.append(diff)
    headdiff_length (head_diff,Length_,Length_pred)
    #headdiff_lengthdiff (head_diff,length_diff)

# Generating Predictions on test data
    Predictions=model.predict(X_test)
    # Scaling the predicted Price data back to original price scale
    Predictions=TargetVarScalerFit.inverse_transform(Predictions)
    # Scaling the y_test Price data back to original price scale
    y_test_orig=TargetVarScalerFit.inverse_transform(y_test)
    # Scaling the test data back to original scale
    Test_Data=PredictorScalerFit.inverse_transform(X_test)
    Test_Data=pd.DataFrame(data=Test_Data, columns=Predictors)
    Test_Data['Length']=y_test_orig
    Test_Data['PredictedLength']=Predictions
    Test_Data.head()
    #print ('y_train_orig=',y_train_orig)
    print ('')
    print (Test_Data)
    # Computing the absolute percent error
    APE=100*(abs(Test_Data['Length']-Test_Data['PredictedLength'])/Test_Data['Length'])
    Test_Data['APE']=APE
    print ('#'*100)
    print('The Accuracy of test ANN model is:', 100-np.mean(APE))
    print ('#'*100)
    Test_Data.sort_values(by=['Length'], inplace=True)
    print ('Test_Data=')
    print (Test_Data)
    Length_ = get_column(list(Test_Data.Length))
    Length_pred = get_column(list(Test_Data.PredictedLength))
    Node1_pressure = get_column(list(Test_Data.Node1_pressure_c_5))
    Node2_pressure = get_column(list(Test_Data.Node2_pressure_c_5))

    
    head_diff = []
    for i in range(len(Node1_pressure)):
        diff = Node2_pressure[i] - Node1_pressure[i]
        head_diff.append(diff)
    length_diff = []
    for i in range(len(Node1_pressure)):
        diff = Length_[i] - Length_pred[i]
        length_diff.append(diff)
    headdiff_length (head_diff,Length_,Length_pred)
    #headdiff_lengthdiff (head_diff,length_diff)
        #Model Evaluation

    print ('y_test_orig=',y_test_orig)
    print ('')
    print ('Predictions=',Predictions)
    print ('')


  
    meanAbErr = metrics.mean_absolute_error(y_test_orig, Predictions)
    meanSqErr = metrics.mean_squared_error(y_test_orig, Predictions)
    rootMeanSqErr = np.sqrt(metrics.mean_squared_error(y_test_orig, Predictions))
    #print('R squared: {:.2f}'.format(mlr.score(Predictors,TargetVariable)*100))
    print('Mean Absolute Error:', meanAbErr)
    print('Mean Square Error:', meanSqErr)
    print('Root Mean Square Error:', rootMeanSqErr)



    
 

    return 0


if __name__ == "__main__":
    sys.exit(main())
