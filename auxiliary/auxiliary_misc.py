"""This module contains various additional auxiliary functions that do not belong in plots/tables/predictions which are used in the main notebook."""

import matplotlib as plt
import pandas as pd
import numpy as np
import statsmodels as sm

from auxiliary.auxiliary_predictions import *
from auxiliary.auxiliary_plots import *
from auxiliary.auxiliary_tables import *
from auxiliary.auxiliary_misc import *

def pvalue_5percent_red(val):
    """
    Formatting Function: Takes a scalar and returns a string with the css property `'color: red'` 
    for values below 0.05, black otherwise.
    """
    color = 'red' if val < 0.05 else 'black'
    return 'color: %s' % color


def calculate_bin_frequency(data, bins):
    """
    Calculates the frequency of differnt bins in a dataframe.
    Args:
    data(pd.DataFrame): Dataframe that contains the raw data.
    bins(column): Name of column that contains the variable that should be assessed.
    
    Returns:
    bin_frequency(pd.DataFrame): Dataframe that contains the frequency of each bin in data and and a constant.
    """
    bin_frequency = pd.DataFrame(data[bins].value_counts())
    bin_frequency.reset_index(level=0, inplace=True)
    bin_frequency.rename(columns={"index": "bins", bins: "freq"}, inplace=True)
    bin_frequency = bin_frequency.sort_values(by=['bins'])
    bin_frequency['const'] = 1
    
    return bin_frequency


def create_groups_dict(data, keys, columns):
    """
    Function creates a dictionary containing different subsets of a dataset. Subsets are created using dummies. 
    
    Args:
    data(pd.DataFrame): Dataset that should be split into subsets.
    keys(list): List of keys that should be used in the dataframe.
    columns(list): List of dummy variables in dataset that are used for creating subsets.
    
    Returns:
    groups_dict(dictionary)
    """
    groups_dict = {}
    
    for i in range(len(keys)):
        groups_dict[keys[i]]=data[data[columns[i]] == 1]
            
    return groups_dict

def gen_placebo_data(data, cutoff_deviation):
    
    placebo_data = data.copy()
    placebo_data.loc[:,'dist_from_cut'] = placebo_data.loc[:,'dist_from_cut'] - cutoff_deviation

    for i in range(0,len(placebo_data)):
        if placebo_data.loc[i,'dist_from_cut'] < 0:
            placebo_data.loc[i,'gpalscutoff'] = 1
            placebo_data.loc[i,'gpagrcutoff'] = 0

        else:
            placebo_data.loc[i,'gpalscutoff'] = 0
            placebo_data.loc[i,'gpagrcutoff'] = 1

    placebo_data['gpaXgpalscutoff'] = placebo_data['dist_from_cut']*placebo_data['gpalscutoff']
    placebo_data['gpaXgpagrcutoff'] = placebo_data['dist_from_cut']*placebo_data['gpagrcutoff']  
    
    return placebo_data  


def prepare_data(data):
    # Add constant to data to use in regressions later.
    data.loc[:, 'const'] = 1
    
    # Add dummy for being above the cutoff
    data['nextGPA_above_cutoff'] = np.NaN
    data.loc[data.nextGPA >= 0, 'nextGPA_above_cutoff'] = 1
    data.loc[data.nextGPA < 0, 'nextGPA_above_cutoff'] = 0
    
    data['total_credits_year2'] = data['totcredits_year2']
    data.loc[np.isnan(data.nextGPA)==True, 'total_credits_year2'] = np.NaN
    data.loc[data.suspended_summer1 == 1, 'total_credits_year2'] = np.NaN
    
    return data

def create_placebo_subdata(placebo_data):
    placebo_data12 = placebo_data[abs(placebo_data['dist_from_cut']) < 1.2].copy()
    # Bin data according to new distances from cutoff
    bins_labels = np.arange(-1.15, 1.25, 0.1)
    placebo_data12['dist_from_cut_med10'] = pd.cut(x=placebo_data12['dist_from_cut'], 
                                                    bins=24, 
                                                    labels=bins_labels, 
                                                    right=False
                                                   )
    placebo_data06 = placebo_data12[abs(placebo_data12['dist_from_cut']) < 0.6].copy()
    
    return [placebo_data12, placebo_data06]



def bandwidth_sensitivity_summary(data, outcome, groups_dict_keys, groups_dict_columns, regressors):
    bandwidths = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.1,1.2]
    arrays = [np.array([0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4, 0.5, 0.5, 
                        0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 1, 1, 1.1, 1.1, 1.2, 1.2]),
              np.array(['probation', 'p-value']*12)]

    summary = pd.DataFrame(index=arrays, columns= groups_dict_keys)


    for val in bandwidths:   
        sample = data[abs(data['dist_from_cut']) < val]
        groups_dict = create_groups_dict(sample, groups_dict_keys, groups_dict_columns)
        table = estimate_RDD_multiple_datasets(groups_dict, groups_dict_keys, outcome, regressors)
        summary.loc[(val,'probation'), :] = table['GPA below cutoff (1)']
        summary.loc[(val,'p-value'), :] = table['P-Value (1)']

        for i in summary.columns:
            if (summary.loc[(val,'p-value'), i] < 0.1) == False:
                summary.loc[(val,'p-value'), i] = '.'
                summary.loc[(val,'probation'), i] = 'x'

    return summary