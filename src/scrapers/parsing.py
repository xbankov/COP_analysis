import re


def get_eng_url_from_td(td):
    select_element = td.select_one(".select-wrapper select")
    english_option = select_element.find(
        "option", string=re.compile("english", re.IGNORECASE)
    )
    return english_option["value"]


def parse_text(text):
    return text.strip().replace("/", "_").replace("-", "_").replace(" ", "_")


def parse_date(date):
    return date.strip().replace(" ", ".")