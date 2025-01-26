import json
import re
import time

import pandas as pd
from deep_translator import DeeplTranslator, GoogleTranslator
from deep_translator.exceptions import RequestError
from tqdm import tqdm

import config
from utils.helpers import get_json_filename, load_tag, read_json, save_tag
from utils.logger import setup_logger

logger = setup_logger()


def translate_pdfs(csv_path, json_dir):
    data = pd.read_csv(csv_path)
    files = []
    for _, group in data.groupby("language"):
        language = group["language"].iloc[0]  # Language of the current group
        language_code = config.LANGUAGE_TO_CODE[language]

        for _, row in tqdm(
            group.iterrows(),
            total=len(group),
            desc=f"Cleaning and translating {language}",
        ):
            json_path = get_json_filename(json_dir, row["id"])
            json_dict = read_json(json_path)

            if (
                not "translated_text" in json_dict.keys()
                and not config.FORCE["TRANSLATE"]
            ):
                text = load_tag(json_path, "original_text")
                sentences = split_sentences(text, language_code)
                if len(sentences) == 0:
                    print(f"{json_path} contains no sentences. Check if not scan!")
                    files.append(json_path)
                    continue

                if language == "english":
                    save_tag(json_path, "translated_text", text)
                    continue

                for translate in [
                    translate_google,
                    translate_deepl,
                ]:
                    try:
                        translated_text = translate(sentences)
                        break

                    except RequestError as e:
                        logger.warning(e)
                        logger.warning(language)
                        logger.warning(f"First 500 chars: {text[:500]}")
                        logger.warning(f"Translating request from {translate} failed!")

                    except Exception as e:
                        logger.error(e)
                        logger.error(
                            "Unknown error, couldn't translate continuing on the next text."
                        )

                save_tag(json_path, "translated_text", translated_text)
    logger.error(f"These files had zero sentences: {files}")


def clean_sentence(sentence):
    cleaned_sentence = re.sub(r"\s", " ", sentence)
    cleaned_sentence = re.sub(r"،", " ", cleaned_sentence)
    cleaned_sentence = re.sub(r"(\s)\s+", r"\1", cleaned_sentence)
    cleaned_sentence = re.sub(r"[^\w\s\u0600-\u06FF]", "", cleaned_sentence)
    cleaned_sentence = cleaned_sentence.strip()
    return cleaned_sentence


def split_sentences(text, language_code):
    cleaned_text = re.sub(r"(\s)\s+", r"\1", text)
    if language_code == "ar":
        sentences = re.split("\u202a|\u202b|\u202c", cleaned_text)
        sentences = [
            clean_sentence(s) for s in sentences if len(clean_sentence(s)) != 0
        ]
    else:
        sentences = re.split("\.", cleaned_text)
        sentences = [
            clean_sentence(s) for s in sentences if len(clean_sentence(s)) != 0
        ]
    return sentences


def translate(translator, sentences):
    translations = []
    current_string = ""
    for sentence in sentences:
        if len(current_string) + len(sentence) < config.MAX_CHARS:
            current_string += " " + sentence
        else:
            translated_string = translator.translate(current_string)
            translations.append(translated_string)
            current_string = ""
            time.sleep(config.UNIVERSAL_REQUEST_SLEEP)

    return "\n".join(translations)


def translate_google(sentences):
    translator = GoogleTranslator(source="auto", target="en")
    return translate(translator, sentences)


def translate_deepl(sentences):
    with open("secret.json") as fp:
        secret = json.load(fp)

    translator = DeeplTranslator(
        api_key=secret["deepl"], source="auto", target="en", use_free_api=True
    )
    return translate(translator, sentences)
