# src/main.py
from utils.logger import setup_logger
from scrapers.initial_scraper import scrape_data
import config

# Set up the logger
logger = setup_logger()


def main():
    try:
        # Replace 'your_url_here' with the actual URL you want to scrape
        url_to_scrape = config.MeetingDocuments2021_2023

        logger.info(f"Scraping data from {url_to_scrape}")
        scrape_data(url_to_scrape)

        logger.info("Scraping complete.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
