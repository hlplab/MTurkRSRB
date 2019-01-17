#!/usr/bin/env python3

"""
Takes the XLSX output of dempgraphic_report.py and makes it REDCap import ready
"""

import argparse
from datetime import date
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser(
    description='Convert XLSX demographic report into REDCap ready CSV file')
parser.add_argument('-f', '--file', required=True,
                    help='(required) XLSX demographic report file')
parser.add_argument('-i', '--startindex',
                    action='store',
                    help='Integer index to start with (broken; do not use yet)')
args = parser.parse_args()

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

# Assumes sheet hasn't been renamed
df = pd.read_excel(args.file, 'Demographic Data')

# Assumes file retains name that demographic_repory.py gave it
protocol = args.file[:args.file.index('_')]

# Convert all the text into the numbers REDCap stores them as
df['mturk_sex'] = df['Sex'].apply(lambda x: sex_map[x])
df['mturk_race'] = df['Race'].apply(lambda y: race_map[y])
df['mturk_ethnicity'] = df['Ethnicity'].apply(lambda z: eth_map[z])

# Just select the columns we care about into a new data frame
core_cols = ('workerid', 'mturk_sex', 'mturk_race', 'mturk_ethnicity')
out_df = df.loc[:, core_cols]

# FIXME: Something goes wrong with creating record_id if this is used
# If you, e.g. set args.startindex to 10, then the first record is mt20
# and the final 10 records get NaN as their record_id. After splitting
# record_id creating into steps I can tell you the list from `map` is fine
# but it gets mangled at the `pd.Series` step. But no clue why.
if args.startindex:
    out_df.index += int(args.startindex)

# Each record needs a unique 'record_id'
out_df['record_id'] = pd.Series(map(lambda x: f'mt{x:04}', out_df.index.values))

# Age is pretty useless and mostly not capture so just set it to nothing
out_df['mturk_age'] = np.nan

out_df['mturk_demography_form_complete'] = 1  # This actually maps to "Unverified", but that's fine.

# REDCap expects a different name
out_df.rename(columns={'workerid': 'mturk_workerid'}, inplace=True)

# REDCap expects the columns in this order
out_columns = ('record_id', 'mturk_workerid', 'mturk_age', 'mturk_sex', 'mturk_race', 'mturk_ethnicity', 'mturk_demography_form_complete')
out_df = out_df.reindex(columns=out_columns)

out_df.to_csv(f'{protocol}-redcap-{date.today().isoformat()}.csv', index=False)
