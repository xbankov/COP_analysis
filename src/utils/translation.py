from functools import partial
import time
import unicodedata
import json
import re

import spacy
import pandas as pd
from tqdm import tqdm

from deep_translator import DeeplTranslator, GoogleTranslator
from deep_translator.exceptions import RequestError
from transformers import MarianTokenizer, MarianMTModel

from utils.helpers import get_txt_filename
from utils.logger import setup_logger

import config

logger = setup_logger()


def translate_pdfs(csv_path, txts_dir, eng_txts_dir, filename_column):
    data = pd.read_csv(csv_path)
    for _, group in data.groupby("Language"):
        language = group["Language"].iloc[0]  # Language of the current group
        language_code = config.LANGUAGE_TO_CODE[language]

        for _, row in tqdm(
            group.iterrows(),
            total=len(group),
            desc=f"Cleaning and translating {language}",
        ):
            src = get_txt_filename(txts_dir, row[filename_column])
            dst = get_txt_filename(eng_txts_dir, row[filename_column])
            if not dst.exists():
                with open(src, mode="r", encoding="utf-8") as fin:
                    text = fin.read()
                sentences = split_sentences(text, language_code)                
                if language == "english":
                    with open(dst, mode="w", encoding="utf-8") as fout:
                        fout.write("\n".join(sentences))
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
                        logger.warning(f"First 100 chars: {text[:200]}")
                        logger.warning(f"Translating request from {translate} failed!")

                    except Exception as e:
                        logger.error(e)
                        logger.error(
                            "Unknown error, couldn't translate continuing on the next text."
                        )

                with open(dst, mode="w", encoding="utf-8") as fout:
                    fout.write(translated_text)


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
            time.sleep(config.REQUEST_SLEEP)

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
