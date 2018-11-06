This script reads in Mechanical Turk results files with HLP Lab demographic fields in it and generates an Excel file that can be used to generate pivot tables with counts for RSRB and NIH reports.

## Usage
```bash
python demographic_report.py -r examplefile.yml
```

Minimum Python version is 3.6 due to f-strings and type annotations.

There is an example YAML file with fake data in it to show what the expected input file should be like.