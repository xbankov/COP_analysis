#!/usr/bin/env python

from pathlib import Path
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from pytube import Playlist
from pytube import YouTube
from tqdm import tqdm
import config

from utils.logger import setup_logger

logger = setup_logger()


def main():
    for name, playlist_url in config.YOUTUBE_URLS.items():
        playlist = Playlist(playlist_url)

        data_folder = Path(config.DEFAULT_DATA_FOLDER) / name
        data_folder.mkdir(parents=True, exist_ok=True)

        video_ids = []
        video_titles = []
        transcripts = []
        statuses = []

        for url in tqdm(playlist):
            yt = YouTube(url)
            video_id = yt.video_id
            video_title = yt.video_id
            transcript = ""
            status = "Error"
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id=video_id, languages=("en",)
                )
                transcript_string = " ".join(
                    [segment["text"] for segment in transcript]
                )
                transcript = transcript_string
                status = "Downloaded"
            except NoTranscriptFound:
                logger.warning(f"No transcription for language {'en'}")
                status = "NO_ENG"
            except TranscriptsDisabled:
                logger.warning(f"Transcripts disabled")
                status = "NO_TRANSCRIPT"
            except Exception as e:
                logger.warning(e)
                logger.warning(type(e))
                status = "ERROR"
            finally:
                video_ids.append(video_id)
                video_titles.append(video_title)
                transcripts.append(transcript)
                statuses.append(status)

        df = pd.DataFrame(
            {
                "video_id": video_ids,
                "video_title": video_titles,
                "transcript": transcripts,
                "status": statuses,
            }
        )
        df.to_csv(data_folder / f"{data_folder.name}_transcripts.csv", index=False)


if __name__ == "__main__":
    main()
