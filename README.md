This script reads in Mechanical Turk results files with HLP Lab demographic fields in it and generates an Excel file that can be used to generate pivot tables with counts for RSRB and NIH reports.

## Installation
This is a standalone Python script, so you don't need to install it, per se. But you do need the right version of Python and some packages installed.

Minimum Python version is 3.6 due to f-strings and type annotations.

To install required packages, either do
```bash
pip install -r requirements.txt
```

or if you use the Anaconda Python distribution (highly recommended)

```bash
conda install --yes --file requirements.txt
```

## Usage
```bash
python demographic_report.py -r examplefile.yml
```

There is an example YAML file with fake data in it to show what the expected input file should be like.
