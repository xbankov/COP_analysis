# COP_analysis

Create a databank from official and unofficial documents from global climate conferences in recent years by scraping their official website (in a considering time between requests) and analyzing the documents to comment on topics and trends discussed and focused on.

Databank is stored at: https://drive.google.com/drive/u/0/folders/10uDRjYWxMBosoL_bfs8gwxFg0dVcyyfA

## Installation steps

### Install Conda

`conda create -n copscraper python=3.11.5`

`conda activate copscraper`

### Install python packages

`pip install -r requirements.txt`

## Run steps

### Extract&Download bash script with arguments:

- ./decisions.sh - parses decisions url with specific format and downloads files stored in progress_csv with default download_path
- ./documents.sh - parses documents url with specific format and downloads files stored in progress_csv with default download_path

### Extract

- extract progress_csv, see code for arguments

### Download

- download pdf that have not yet been downloaded given the progress_csv, see code for arguments
