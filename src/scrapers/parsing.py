import re

from utils.logger import setup_logger

logger = setup_logger()


def get_pdf_info_from_td(td):
    try:
        select_element = td.select_one(".select-wrapper select")
        english_option = select_element.find(
            "option", string=re.compile("english", re.IGNORECASE)
        )

        if english_option:
            return english_option["value"], english_option.text.split(" ")[0].lower()
        else:
            logger.debug("No English PDF found. Trying any other language PDF.")
            option = select_element.find("option")
            return option["value"], option.text.split(" ")[0].lower()

    except AttributeError:
        logger.warning("No PDF found.")
        return None, None


def parse_text(text):
    return text.strip().replace("/", "_").replace("-", "_").replace(" ", "_")


def parse_date(date):
    return date.strip().replace(" ", ".")
