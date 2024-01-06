#!/bin/bash
DATA_FOLDER=data/documents
URL="https://unfccc.int/decisions?f%5B0%5D=body%3A1342&f%5B1%5D=body%3A1343&f%5B2%5D=body%3A4099&f%5B3%5D=conference%3A4301&f%5B4%5D=conference%3A4460"
mkdir -p $DATA_FOLDER

src/extract.py --progress_csv $DATA_FOLDER/progress.csv --tab documents --url $URL
src/download.py --progress_csv $DATA_FOLDER/progress.csv
# ./upload.py --progress_csv $DATA_FOLDER/progress.csv
