#!/bin/bash
DATA_FOLDER=data/documents
URL="https://unfccc.int/documents?f%5B0%5D=category%3ANon-Official%20Documents&f%5B1%5D=conference%3A4112&f%5B2%5D=conference%3A4121&f%5B3%5D=conference%3A4202&f%5B4%5D=conference%3A4225&f%5B5%5D=conference%3A4252&f%5B6%5D=conference%3A4300&f%5B7%5D=conference%3A4301&f%5B8%5D=conference%3A4370&f%5B9%5D=conference%3A4460&f%5B10%5D=conference%3A4466&f%5B11%5D=conference%3A4526&f%5B12%5D=conference%3A4540&f%5B13%5D=document_type%3A853&f%5B14%5D=document_type%3A1934&f%5B15%5D=topic%3A4123"
mkdir -p $DATA_FOLDER

src/extract.py --progress_csv $DATA_FOLDER/progress.csv --tab documents --url $URL
src/download.py --progress_csv $DATA_FOLDER/progress.csv --data_folder $DATA_FOLDER
