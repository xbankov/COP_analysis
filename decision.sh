#!/bin/bash
DATA_FOLDER=data/decisions
URL="https://unfccc.int/decisions?f%5B0%5D=conference%3A4460"
mkdir -p $DATA_FOLDER

src/extract.py --progress_csv $DATA_FOLDER/progress.csv --tab decisions --url $URL
src/download.py --progress_csv $DATA_FOLDER/progress.csv
# ./upload.py --progress_csv $DATA_FOLDER/progress.csv
