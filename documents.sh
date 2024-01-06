mkdir data/documents/

./src/extract.py --progress_csv data/documents/progress.csv --tab documents --url "https://unfccc.int/decisions?f%5B0%5D=body%3A1342&f%5B1%5D=body%3A1343&f%5B2%5D=body%3A4099&f%5B3%5D=conference%3A4301&f%5B4%5D=conference%3A4460"
./download.py --progress_csv data/documents/progress.csv --download
./upload.py 