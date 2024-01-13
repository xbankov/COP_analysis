#!/bin/bash
DATA_FOLDER=data/decisionsCOP
URL="https://unfccc.int/decisions?f%5B0%5D=conference%3A4202&f%5B1%5D=conference%3A4252&f%5B2%5D=conference%3A4301&f%5B3%5D=conference%3A4460"
mkdir -p $DATA_FOLDER

src/extract.py --progress_csv $DATA_FOLDER/progress.csv --tab decisions --url $URL --headless
src/download.py --progress_csv $DATA_FOLDER/progress.csv --data_folder $DATA_FOLDER
