#!/usr/bin/env python
from pathlib import Path
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from pytube import Playlist, YouTube
from tqdm.auto import tqdm
import config
import time
from utils.logger import setup_logger

logger = setup_logger()


def get_translation(video_id):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcript_list:
        for language_dict in transcript.translation_languages:
            if language_dict["language_code"] == "en":
                translated_transcript = transcript.translate("en")

                transcript = translated_transcript.fetch()
                transcript_string = " ".join(
                    [segment["text"] for segment in transcript]
                )
                transcript = transcript_string
                return transcript


def main():
    logger.info("##########################################")
    logger.info("###### DOWNLOAD YOUTUBE TRANSCRIPTS ######")
    logger.info("##########################################")

    for name, playlist_url in config.YOUTUBE_URLS.items():
        playlist = Playlist(playlist_url)
        data_folder = Path(config.DEFAULT_DATA_DIR) / name
        data_folder.mkdir(parents=True, exist_ok=True)
        data_filename = data_folder / f"{data_folder.name}_transcripts.csv"

        # Read existing data or create an empty DataFrame
        df = pd.read_csv(data_filename) if data_filename.exists() else pd.DataFrame()

        for url in tqdm(playlist):
            requested = False
            yt = YouTube(url)
            video_id = yt.video_id
            video_title = yt.video_id
            transcript = None
            status = None

            if not df.empty and video_id in df["video_id"].values:
                row = df[df["video_id"] == video_id].iloc[0]
                if row["status"] == "Downloaded":
                    transcript, status = row["transcript"], "Downloaded"

            if status != "Downloaded":
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(
                        video_id=video_id, languages=("en",)
                    )
                    transcript_string = " ".join(
                        [segment["text"] for segment in transcript]
                    )
                    transcript = transcript_string
                    status = "Downloaded"
                    requested = True

                except NoTranscriptFound:
                    logger.debug(f"No transcription for language 'en'")
                    if config.TRANSLATE_TO_EN:
                        transcript = get_translation(video_id)
                        status = "Downloaded"

                except TranscriptsDisabled:
                    logger.warning(f"Transcripts disabled")
                except Exception as e:
                    logger.warning(e)
                    logger.warning(type(e))
                    status = "ERROR"
                finally:
                    df = pd.concat(
                        [
                            df,
                            pd.DataFrame(
                                {
                                    "video_id": [video_id],
                                    "video_title": [video_title],
                                    "transcript": [transcript],
                                    "status": [status],
                                }
                            ),
                        ],
                        ignore_index=True,
                    )
                    df.to_csv(data_filename, index=False)
                if requested:
                    time.sleep(config.UNIVERSAL_REQUEST_SLEEP)


if __name__ == "__main__":
    main()
