#!/usr/bin/env python3

"""
Takes the XLSX output of dempgraphic_report.py and makes it REDCap import ready
"""


import pandas as pd
import numpy as np

sex_map = {
    'Female': 0,
    'Male': 1,
    'Unknown or Not Reported': 2,
}

race_map = {
    'American Indian / Alaska Native': 0,
    'Asian': 1,
    'Native Hawaiian or Other Pacific Islander': 2,
    'Black or African American': 3,
    'White': 4,
    'More Than One Race': 5,
    'Unknown or Not Reported': 6, 
    'Other': 6,
}

eth_map = {
    'Hisp': 0,
    'NonHisp': 1,
    'Unknown or Not Reported': 2
}

df = pd.read_excel('crosslinguistic_report-2018-11-07.xlsx')

# Convert all the text into the numbers REDCap stores them as
df['mturk_sex'] = df['Sex'].apply(lambda x: sex_map[x])
df['mturk_race'] = df['Race'].apply(lambda y: race_map[y])
df['mturk_ethnicity'] = df['Ethnicity'].apply(lambda z: eth_map[z])

# Just select the columns we care about into a new data frame
core_cols = ('workerid', 'mturk_sex', 'mturk_race', 'mturk_ethnicity')
out_df = df.loc[:, core_cols]

# Each record needs a unique 'record_id'
out_df['record_id'] = pd.Series(map(lambda x: f'mt{x}', out_df.index.values))

# Age is pretty useless and mostly not capture so just set it to nothing
out_df['mturk_age'] = np.nan

out_df['mturk_demography_form_complete'] = 1  # This actually maps to "Unverified", but that's fine.

# REDCap expects a different name
out_df.rename(columns={'workerid': 'mturk_workerid'}, inplace=True)

# REDCap expects the columns in this order
out_columns = ('record_id', 'mturk_workerid', 'mturk_age', 'mturk_sex', 'mturk_race', 'mturk_ethnicity', 'mturk_demography_form_complete')
out_df = out_df.reindex(columns=out_columns)

out_df.to_csv('crossling.csv', index=False)
