#!/bin/bash
DATA_FOLDER=data/documents
URL="https://unfccc.int/documents?f%5B0%5D=category%3AOfficial%20documents&f%5B1%5D=conference%3A4540"
mkdir -p $DATA_FOLDER

src/extract.py --progress_csv $DATA_FOLDER/progress.csv --tab documents --url $URL
src/download.py --progress_csv $DATA_FOLDER/progress.csv --data_folder $DATA_FOLDER
