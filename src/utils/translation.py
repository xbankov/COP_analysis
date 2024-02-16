from functools import partial
import token
import unicodedata
from deep_translator import DeeplTranslator, GoogleTranslator
from deep_translator.exceptions import RequestError
import re
import nltk
import shutil
import pandas as pd
from transformers import MarianTokenizer, MarianMTModel
from tqdm import tqdm


from nltk.tokenize import sent_tokenize
from utils.helpers import get_txt_filename
from utils.logger import setup_logger
import config

logger = setup_logger()


def translate_pdfs(csv_path, txts_dir, eng_txts_dir, filename_column):
    data = pd.read_csv(csv_path)
    models = {}

    for _, group in data.groupby("Language"):
        language = group["Language"].iloc[0]  # Language of the current group

        if language == "english":
            # Handle English files by copying them directly to eng_txts_dir
            for _, row in group.iterrows():
                src = get_txt_filename(txts_dir, row[filename_column])
                dst = get_txt_filename(eng_txts_dir, row[filename_column])
                if not dst.exists():
                    shutil.copy(src, dst)
        else:
            # Existing logic for non-English languages
            language_code = config.LANGUAGE_TO_CODE[language]
            model_name = f"Helsinki-NLP/opus-mt-{language_code}-en"
            if language_code not in models:
                models[language_code] = {
                    "model": MarianMTModel.from_pretrained(model_name),
                    "tokenizer": MarianTokenizer.from_pretrained(model_name),
                    "sentencer": partial(sent_tokenize, language=language),
                }

            for _, row in tqdm(
                group.iterrows(), total=len(group), desc=f"Translating {language}"
            ):
                src = get_txt_filename(txts_dir, row[filename_column])
                dst = get_txt_filename(eng_txts_dir, row[filename_column])
                if not dst.exists():
                    with open(src, mode="r", encoding="utf-8") as fin:
                        text = fin.read()

                    for translate in [
                        translate_google,
                        translate_deepl,
                        partial(translate_offline, models=models[language_code]),
                    ]:
                        try:
                            translated_text = translate(text)
                            break

                        except RequestError as e:
                            logger.warning(e)
                            logger.warning(language)
                            logger.warning(f"First 100 chars: {text[:100]}")
                            logger.warning(
                                f"Translating request from {translate} failed!"
                            )

                        except LookupError as e:
                            logger.error(e)
                            logger.error(
                                f"Sentencer not found for language: {language}"
                            )
                        except Exception as e:
                            logger.error(e)
                            logger.error(
                                "Unknown error, couldn't translate continuing on the next text."
                            )

                    with open(dst, mode="w", encoding="utf-8") as fout:
                        fout.write(translated_text)

    data.to_csv(csv_path, index=False)


def clean(string):

    # Replace Arabic ligatures with their corresponding separate letters
    string = unicodedata.normalize("NFKC", string)

    # Standardize whitespace around punctuation and special characters
    string = re.sub(r"\s+([\.,؛:!؟])", r"\1", string)
    string = re.sub(r"([\.,؛:!؟])\s+", r"\1", string)

    # Define a pattern to remove \u202a, \u202b, and \u202c
    pattern = re.compile(r"[\u202a\u202b\u202c]")

    # Remove the Unicode characters
    string = pattern.sub("", string)

    string = re.sub("\s{2,}", " ", string)

    # Remove all punctuation
    string = re.sub(r"[^\w\s]", "", string)

    # lower all capital letters
    string = string.lower()

    return string


import nltk


# Function to split text into chunks
def split_into_chunks(text, max_tokens, overlap_tokens):
    tokens = nltk.word_tokenize(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(len(tokens), start + max_tokens)

        # Add the overlap from the previous chunk
        if start > 0:
            start -= overlap_tokens

        # Add the overlap to the next chunk
        end += overlap_tokens

        # Slice the list of tokens
        chunk = tokens[start:end]

        # Join the tokens back into a string
        chunk_text = " ".join(chunk)

        # Append the chunk to the list of chunks
        chunks.append(chunk_text)

        start = end
    return chunks


def translate_google(text):
    translator = GoogleTranslator(source="auto", target="en")
    if len(text) > 2500:
        texts = split_into_chunks(text, max_tokens=2500, overlap_tokens=50)
        return " ".join(translator.translate_batch(texts))

    else:
        return translator.translate(text)


def translate_deepl(text):
    translator = DeeplTranslator(api_key = , source="auto", target="en", use_free_api=True)
    if len(text) > 2500:
        texts = split_into_chunks(text, max_tokens=2500, overlap_tokens=50)
        return " ".join(translator.translate_batch(texts))

    else:
        return translator.translate(text)


def translate_offline(text, models):
    sentences = models["sentencer"](text)

    # Translate each sentence individually
    translated_sentences = []
    for sentence in sentences:

        encoded = models["tokenizer"](
            [sentence], return_tensors="pt", truncation=True, max_length=512
        )
        translated = models["model"].generate(**encoded)
        decoded = [
            models["tokenizer"].decode(t, skip_special_tokens=True) for t in translated
        ]
        print(" ".join(decoded))
        translated_sentences.append(" ".join(decoded))

    translated_text = " ".join(translated_sentences)
    return translated_text
