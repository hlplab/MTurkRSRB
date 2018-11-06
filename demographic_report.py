#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Read in Mechanical Turk results files to calculate demographic information
for various funding and regulatory agencies. Outputs an xlsx file with columns
of interest that is easy to do pivot tables for getting the necessary counts
"""
import argparse
from datetime import date, datetime
# import sqlite3
from typing import Union

from dateutil.parser import parse
from dateutil.tz import gettz, tzutc

import numpy as np

import pandas as pd

from ruamel.yaml import CLoader as Loader
from ruamel.yaml import load

CSI = '\x1B['
reset = CSI+'m'

# tzinfos = {'EDT': -14400, 'EST': -18000}

# For some reason dateutil doesn't know PDT and PST?
pactz = {'PDT': gettz('America/Los_Angeles'),
         'PST': gettz('America/Los_Angeles')}

parser = argparse.ArgumentParser(
    description='Load one or more MTurk results files and extract the NIH '
                'mandated demographic info')
parser.add_argument('-r', '--resultsfilelist', required=True,
                    help='(required) YAML file with list of results files to use')
parser.add_argument('-s', '--rawsubjects',
                    action='store_true',
                    help='Dump a raw file of all assignments without removing duplicate workers')
# parser.add_argument('-p', '--protocol', required=True,
#                     help='Specifiy the IRB protocol name')
args = parser.parse_args()


with open(args.resultsfilelist, 'r') as rfile:
    expdata = load(rfile, Loader=Loader)

abort = False
for k in ('resultsfiles', 'protocol', 'datebreaks'):
    if k not in expdata:
        print(f'{k} is a required key in HIT file!')
        abort = True
if abort:
    print('At least one required key missing; aborting HIT load')
    import sys
    sys.exit()

resfiles = expdata['resultsfiles']
protocol = expdata['protocol']
datebreaks = expdata['datebreaks']


columns_of_interest = {
    'hitid', 'HitId',
    # Some web UI downloaded files are missing 'HITTypeId' or 'hittypeid'
    'hittypeid', 'HITTypeId',
    'title', 'Title', 'HitTitle',
    'description', 'Description',
    'keywords', 'Keywords',
    'reward', 'Reward',
    'creationtime', 'CreationTime',
    'assignments', 'MaxAssignments',
    'numavailable', 'NumberofAssignmentsAvailable',
    'numpending', 'NumberofAssignmentsPending',
    'numcomplete', 'NumberofAssignmentsCompleted',
    'hitstatus', 'HITStatus',
    'reviewstatus', 'HITReviewStatus',
    'annotation', 'RequesterAnnotation'
    'assignmentduration', 'AssignmentDurationInSeconds',
    'autoapprovaltime', 'AutoApprovalTime',
    'autoapprovedelay', 'AutoApprovalDelayInSeconds',
    'hitlifetime', 'LifetimeInSeconds',
    'viewhit',
    'assignmentid', 'AssignmentId',
    'workerid', 'WorkerId',
    'assignmentstatus', 'AssignmentStatus',
    'assignmentaccepttime', 'AcceptTime',
    'assignmentsubmittime', 'SubmitTime',
    'assignmentapprovaltime', 'ApprovalTime',
    'assignmentrejecttime', 'RejectionTime',
    'deadline',
    'feedback',
    'reject',
    'Answer.experiment', 'Answer.Experiment', 'Experiment',
    'Experimenter',
    'Answer.list', 'Answer.List',
    'Answer.browser', 'Answer.browserid', 'Answer.Browser', 'Answer.userAgent',
    'Answer.rsrb.raceother',
    'Answer.rsrb.ethnicity',
    'Answer.rsrb.sex',
    'Answer.rsrb.age',
    # Ilker has a column for each race, others just have "Answer.rsrb.race"
    'Answer.rsrb.race.amerind',
    'Answer.rsrb.race.asian',
    'Answer.rsrb.race.black',
    'Answer.rsrb.race.other',
    'Answer.rsrb.race.pacif',
    'Answer.rsrb.race.unknown',
    'Answer.rsrb.race.white',
    'Answer.rsrb.race'
}

name_map = {'HITId': 'hitid', 'HitId': 'hitid',
            'HITTypeId': 'hittypeid',
            'Title': 'title', 'HitTitle': 'title',
            'Description': 'description',
            'Keywords': 'keywords',
            'Reward': 'reward',
            'CreationTime': 'creationtime',
            'MaxAssignments': 'assignments',
            'NumberofAssignmentsAvailable': 'numavailable',
            'NumberofAssignmentsPending': 'numpending',
            'NumberofAssignmentsCompleted': 'numcomplete',
            'HITStatus': 'hitstatus',
            'HITReviewStatus': 'reviewstatus',
            'RequesterAnnotation': 'annotation',
            'AssignmentDurationInSeconds': 'assignmentduration',
            'AutoApprovalTime': 'autoapprovaltime',
            'AutoApprovalDelayInSeconds': 'autoapprovedelay',
            'LifetimeInSeconds': 'hitlifetime',
            'AssignmentId': 'assignmentid',
            'WorkerId': 'workerid',
            'AssignmentStatus': 'assignmentstatus',
            'AcceptTime': 'assignmentaccepttime',
            'SubmitTime': 'assignmentsubmittime',
            'RejectionTime': 'assignmentrejecttime',
            }

results = None
for r in resfiles:
    with open(r['file'], 'r') as resfile:
        print(f'Loading {r["file"]}')
        delim = '\t'
        if 'delimiter' in r:
            if r['delimiter'] == 'comma':
                delim = ','
        rdf: pd.DataFrame = pd.read_csv(resfile, delimiter=delim, parse_dates=True,
                                        low_memory=False)

        coi = rdf.columns.intersection(columns_of_interest)

        rename_keys = coi.intersection(name_map.keys())
        renames = {x[0]: x[1] for x in name_map.items() if x[0] in rename_keys}

        # Some really old ones have no demographic data
        # Color info from http://stackoverflow.com/a/21786287/3846301
        if 'Answer.rsrb.ethnicity' not in coi:
            print(CSI + '31;40m' + '✗' + CSI + '0m' + f'\t{resfile.name.split("/")[-1]} has no demographic information')
        else:
            print(CSI + '32;40m' + '✓' + CSI + '0m' + f'\t{resfile.name.split("/")[-1]} has demographic information')

        try:
            results_selected = rdf.loc[:, coi]
        except KeyError as e:
            print(f'KeyError: {e}')
            print(f'Columns of interest: {coi}')
            print(f'Actual columns: {rdf.columns}')

        # This is useful if you need to figure out which files are problematic
        # but if you don't comment it out, you can end up with duplicates
        # results_selected.loc[:, 'filename'] = resfile.name

        if 'WorkerId' in coi:
            # print(f'Renaming columns: {rename_keys}')
            results_selected.rename(columns=renames, inplace=True)

        if 'Answer.experiment' in coi:
            results_selected.rename(columns={'Answer.experiment': 'Experiment'}, inplace=True)

        if 'Answer.Experiment' in coi:
            results_selected.rename(columns={'Answer.Experiment': 'Experiment'}, inplace=True)

        if not 'Experiment' in results_selected:
            results_selected['Experiment'] = r['name']

        if not 'Experimenter' in results_selected:
            results_selected['Experimenter'] = r['experimenter']

        if results is None:
            results = results_selected
        else:
            results = results.append(results_selected, ignore_index=True)
# cleanup

# FIXME: pd.to_datetime misses a lot of date formats, better off converting by
# hand using dateutil
# results['assignmentsubmittime'] = pd.to_datetime(results['assignmentsubmittime'])
results.rename(columns={'Answer.rsrb.ethnicity': 'Ethnicity',
                        'Answer.rsrb.sex': 'Sex',
                        'Answer.rsrb.age': 'Age'},
               inplace=True)

try:
    results.loc[results['Sex'] == "['Male']", 'Sex'] = 'Male'
    results.loc[results['Sex'] == "['Female']", 'Sex'] = 'Female'
except KeyError:
    results['Sex'] = pd.Series()
    results['Sex'].fillna('unknown;', inplace=True)

try:
    results.loc[results['Ethnicity'] == "['Not Hispanic or Latino']", 'Ethnicity'] = 'NonHisp'
    results.loc[results['Ethnicity'] == "['Hispanic or Latino']", 'Ethnicity'] = 'Hisp'
    results.loc[results['Ethnicity'] == "['N/A']", 'Ethnicity'] = np.nan
except KeyError:
    results['Ethnicity'] = pd.Series()
    results['Ethnicity'].fillna('unknown;', inplace=True)

try:
    results['Answer.rsrb.race'].fillna('unknown;', inplace=True)
except KeyError:
    results['Answer.rsrb.race'] = pd.Series()
    results['Answer.rsrb.race'].fillna('unknown;', inplace=True)

for key in ('amerind', 'asian', 'black', 'other', 'pacif', 'unknown', 'white'):
    try:
        results[f'Answer.rsrb.race.{key}'].fillna(False, inplace=True)
    except KeyError:
        results[f'Answer.rsrb.race.{key}'] = pd.Series()
        results[f'Answer.rsrb.race.{key}'].fillna(False, inplace=True)

datedefault = datetime(1970, 1, 1, 0, 0, 0, tzinfo=tzutc()).isoformat()
results['assignmentaccepttime'].fillna(datedefault, inplace=True)
results['assignmentsubmittime'].fillna(datedefault, inplace=True)
results['creationtime'].fillna(datedefault, inplace=True)
results['assignmentaccepttime'] = results['assignmentaccepttime'].apply(parse)
results['assignmentsubmittime'] = results['assignmentsubmittime'].apply(parse)
results['creationtime'] = results['creationtime'].apply(parse)
# results['duration'] = results['assignmentsubmittime'] - results['assignmentaccepttime']
# results['assignmentaccepttime'] = results['assignmentaccepttime'].astype('datetime64[ns]')  # .tz_convert('US/Eastern')
# results['assignmentsubmittime'] = results['assignmentsubmittime'].astype('datetime64[ns]')  # .tz_convert('US/Eastern')
# results['creationtime'] = results['creationtime'].astype('datetime64[ns]')  # .tz_convert('US/Eastern')
# print(f"Accept time is of {results['assignmentaccepttime'].dtypes}")
# print(f"Submit time is of {results['assignmentsubmittime'].dtypes}")
# print(f"Creation time is of {results['creationtime'].dtypes}")


def normalize_race(row: pd.core.series.Series) -> str:
    """
    Take possible ways race could be specified in RSRB survey and reduce to desired format.

    For calculating racial demographics, the only values we want are:
      * 'American Indian / Alaska Native',
      * 'Asian',
      * 'Black or African American',
      * 'Other',
      * 'Native Hawaiian or Other Pacific Islander',
      * 'Unknown or Not Reported',
      * 'White'
    """
    try:
        if row['Answer.rsrb.race'] in ('amerind;', 'asian;', 'black;', 'other;',
                                       'pacif;', 'white;'):
            return {'amerind;': 'American Indian / Alaska Native',
                    'asian;': 'Asian',
                    'black;': 'Black or African American',
                    'other;': 'Other',
                    'pacif;': 'Native Hawaiian or Other Pacific Islander',
                    'white;': 'White'}[row['Answer.rsrb.race']]
        elif row['Answer.rsrb.race'].find('|') >= 0:
            return 'More Than One Race'
        elif row['Answer.rsrb.race'] == 'unknown;':
            racecols = \
                (row['Answer.rsrb.race.amerind'],
                 row['Answer.rsrb.race.asian'],
                 row['Answer.rsrb.race.black'],
                 row['Answer.rsrb.race.other'],
                 row['Answer.rsrb.race.pacif'],
                 row['Answer.rsrb.race.unknown'],
                 row['Answer.rsrb.race.white'])
        numraces = len([x for x in racecols if x])
        if numraces > 1:
            return 'More Than One Race'
        elif numraces == 0:
            return 'Unknown or Not Reported'
        else:
            return {
                0: 'American Indian / Alaska Native',
                1: 'Asian',
                2: 'Black or African American',
                3: 'Other',
                4: 'Native Hawaiian or Other Pacific Islander',
                5: 'Unknown or Not Reported',
                6: 'White'}[racecols.index(True)]
    except AttributeError as e:
        print(e)
        print(row)


def normalize_age(row: pd.core.series.Series) -> Union[int, str]:
    """Try to make age an integer."""
    try:
        return int(float(row['Age']))
    except ValueError:
        # print(f'Can't convert: \'{row["Age"]}\'')
        return row['Age']


def add_logical_year(row: pd.core.series.Series) -> str:
    """
    The 'year' for the purpose of a given report may not be equivalent to the
    calendar year. Take the breakpoints specified in the config file and set
    the year for each row based on those.
    """
    if isinstance(row['assignmentsubmittime'], datetime):
        submitdate = row['assignmentsubmittime'].date()
    else:
        try:
            submitdate = parse(row['assignmentsubmittime'], tzinfos=pactz).date()
        except (ValueError, TypeError):
            print(f'Submit time unparseable: {row["assignmentsubmittime"]}')
            # print(f'Submit time unparseable: {row.to_dict()}')
            return 'Date unparseable'
    minyear = maxyear = date.today().year
    for year, drange in expdata['datebreaks'].items():
        if submitdate.year < minyear:
            minyear = submitdate.year
        elif submitdate.year > maxyear:
            maxyear = submitdate.year

        if submitdate >= drange['start'] and submitdate <= drange['end']:
            return year
    print(f'Date not in any range: {row["assignmentsubmittime"]}')
    # print(f'Date not in any range: {row.to_dict()}')
    return 'Date out of range'


# def normalize_experiment(row: pd.core.series.Series):
#     """Reduce 'Answer.experiment' or 'Answer.Experiment' to 'Experiment'."""
#     names = row[row.index.intersection(['Answer.experiment', 'Answer.Experiment'])].dropna()
#     return ','.join(names) if names.any() else np.nan


def normalize_browser(row: pd.core.series.Series):
    """
    Reduce possible browser column names to 'Browser'.

    Various people over time have used different names for the same thing.
    """
    browser = row[row.index.intersection(['Answer.browser', 'Answer.browserid', 'Answer.Browser', 'Answer.userAgent'])].dropna()
    return ','.join(browser) if browser.any() else np.nan


# def normalize_list(row):
#     """
#     Reduce possible experiment list columns to 'ExperimentList'.
#     """
#     experiment_list = row[row.index.intersection(['Answer.list', 'Answer.List'])].dropna()
#     return ','.join(experiment_list) if experiment_list.any() else np.nan


results['Race'] = results.apply(normalize_race, axis=1)
results['Year'] = results.apply(add_logical_year, axis=1)
try:
    results['Age'] = results.apply(normalize_age, axis=1)
except KeyError:
    results['Age'] = pd.Series()
    results['Age'].fillna(np.nan, inplace=True)

# results['Experiment'] = results.apply(normalize_experiment, axis=1)
try:
    results['Browser'] = results.apply(normalize_browser, axis=1)
except KeyError:
    results['Browser'] = pd.Series()
    results['Browser'].fillna('Unknown', inplace=True)
# results['ExperimentList'] = results.apply(normalize_list, axis=1)

results.sort_values(['workerid', 'Year', ], inplace=True)

if args.rawsubjects:
    results.to_csv(f'{protocol}_rawsubjects-{date.today().isoformat()}.csv',
                   # date_format='%Y-%m-%dT%H:%M:%S%z',  # Use ISO 8601 format to make R happy
                   index=False)

print(f'Starting with {len(results)} rows.')

# get the oldest instance of each duplicated value
results.drop_duplicates(['workerid', 'Sex', 'Race', 'Ethnicity'], inplace=True)
print(f'After 1st pass removing duplicates there are {len(results)} rows.')

# Dump full results to a SQLite file
# sql_results = results[['workerid', 'hitid', 'hittypeid', 'assignmentid',
#                        'assignmentaccepttime', 'title', 'ExperimentList',
#                        'Sex', 'Race', 'Ethnicity', 'Age', 'Year', 'Experiment',
#                        'Browser']]
# conn = sqlite3.connect(f'{protocol}.{agency}.{date.today().isoformat()}.db')
# sql_results.to_sql(f'{protocol}_{agency}', conn, if_exists='replace')

# Only write out the important columns for final Excel file
core_cols = ('workerid', 'Sex', 'Race', 'Ethnicity', 'Year')
results = results.loc[:, core_cols]

#
# Try to drop more duplicated workers where values ostensibly mismatch
#

# We're going to put the 'Unknown or Not Reported' back at the end but it's
# easier to drop na values
results.replace(['Unknown', 'Unknown or Not Reported'], np.nan, inplace=True)
dupes = results.loc[results.duplicated('workerid', keep=False)]  # default is to not mark 1st instance
# XXX: can this be done in a vectorized way?
for w in dupes['workerid'].unique():
    worker_rows = results[results['workerid'] == w]

    # For year, take lowest
    results.loc[worker_rows.index, 'Year'] = sorted(worker_rows['Year'].dropna().tolist())[0]

    # For sex, race, and ethnicity: if only one non-NA value set all to it
    for col in ('Sex', 'Race', 'Ethnicity'):
        vals = worker_rows[col].dropna().unique()
        if len(vals) == 1:
            results.loc[worker_rows.index, col] = vals.item()

results.drop_duplicates(['workerid', 'Sex', 'Race', 'Ethnicity'], inplace=True)
results.fillna('Unknown or Not Reported', inplace=True)

print(f'After 2nd pass removing duplicates there are {len(results)} rows.')

print(f'There are {len(results.workerid.unique())} unique workers out of {len(results)} rows')

outfile_name = f'{protocol}_report-{date.today().isoformat()}.xlsx'
writer = pd.ExcelWriter(outfile_name, engine='xlsxwriter',
                        options={'remove_timezone': True})
results.to_excel(writer, 'Demographic Data', index=False)
writer.save()

# Something in all this is triggering the error this documents:
# https://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-with-list-with-missing-labels-is-deprecated
