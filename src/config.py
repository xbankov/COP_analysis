HEADLESS = True
DEFAULT_DRIVER_PATH = "/home/xbankov/COP_analysis/chromedriver-linux64/chromedriver"
DEFAULT_DATA_FOLDER = "data"
DEFAULT_HTML_FILENAME = "loaded_page.html"
DEFAULT_CSV_FILENAME = "data.csv"
DEFAULT_YT_FILENAME = "transcripts.csv"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3",
}
DOCUMENT_URLS = {
    "HSSpeeches": "https://unfccc.int/documents?f%5B0%5D=category%3ANon-Official%20Documents&f%5B1%5D=conference%3A4112&f%5B2%5D=conference%3A4121&f%5B3%5D=conference%3A4202&f%5B4%5D=conference%3A4225&f%5B5%5D=conference%3A4252&f%5B6%5D=conference%3A4300&f%5B7%5D=conference%3A4301&f%5B8%5D=conference%3A4370&f%5B9%5D=conference%3A4460&f%5B10%5D=conference%3A4466&f%5B11%5D=conference%3A4526&f%5B12%5D=conference%3A4540&f%5B13%5D=document_type%3A853&f%5B14%5D=document_type%3A1934&f%5B15%5D=topic%3A4123",
}
DECISION_URLS = {
    "DecisionDocs": "https://unfccc.int/decisions?f%5B0%5D=conference%3A4202&f%5B1%5D=conference%3A4252&f%5B2%5D=conference%3A4301&f%5B3%5D=conference%3A4460",
}
YOUTUBE_URLS = {
    "YouTube/COP28": "https://www.youtube.com/playlist?list=PLBcZ22cUY9RLMkm-apVgzZ8JSi0Tsywd3",
    "YouTube/SB58": "https://www.youtube.com/playlist?list=PLBcZ22cUY9RL6ptbdJJzqbaZn62ZPOha_",
    "YouTube/COP27": "https://www.youtube.com/playlist?list=PLBcZ22cUY9RJc1scZLmb8SdZezq3IM00i",
    "YouTube/SB56": "https://www.youtube.com/playlist?list=PLBcZ22cUY9RIInokbMFmY6b28skN2wQtF",
    "YouTube/COP26": "https://www.youtube.com/playlist?list=PLBcZ22cUY9RL4TEKTBfoLupiqS5n7Kr6c",
}
FORCE = {"HTML": False, "PARSE": False, "DOWNLOAD": False, "PDF_EXTRACT": True}
TRANSLATE_TO_EN = True
