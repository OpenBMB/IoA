import json
import uuid
import os
import requests
from common.log import logger

TEMP_DIR = "./temp"
WHISPER_URL = "http://166.111.121.22:8848/whisper"
MAX_CHAR = 10000


def get_youtube_transcript(youtube_id: str | None = None, url: str | None = None):
    from pytube import YouTube

    def _audio_to_text(yt: YouTube):
        logger.info("No captions found. Trying to extract text from audio.")
        os.makedirs(TEMP_DIR, exist_ok=True)
        uid = uuid.uuid4().hex
        try:
            audio = yt.streams.filter(only_audio=True).first()
            ext = audio.mime_type.split("/")[-1]
            filename = f"audio_{uid}.{ext}"
            logger.info(f"Downloading the audio file and save to {TEMP_DIR}/{filename}")
            audio.download(output_path=TEMP_DIR, filename=filename)
            logger.info("Downloaded")
        except Exception as e:
            return f"Error: {e}"
        with open(os.path.join(TEMP_DIR, filename), "rb") as file:
            # Create a dictionary to hold the file data
            files = {"file": (filename.split("/")[-1], file, "multipart/form-data")}

            # Send the POST request with the file
            logger.info("Running speech-to-text...")
            response = requests.post(WHISPER_URL, files=files)

        return response.json()["text"]

    if youtube_id is None and url is None:
        return "You should provide either youtube_id or url"
    elif youtube_id is not None and url is not None:
        if url != f"https://www.youtube.com/watch?v={youtube_id}":
            return "youtube_id and url are not matched. Ensure that url is correct, or simply pass one of them."
    elif url is None:
        url = f"https://www.youtube.com/watch?v={youtube_id}"
    try:
        yt = YouTube(url)
        yt.bypass_age_gate()
    except Exception as e:
        return f"Error: {e}"
    captions = yt.captions
    if len(captions) == 0:
        return _audio_to_text(yt)[:MAX_CHAR]
    text = ""
    for lang in ["en", "fr", "es", "de", "zh-CN", "zh-Hant", "zh-HK", "it", "nl", "pt", "ru", "ja", "ko"]:
        caption = yt.captions.get(lang, None)
        if caption is not None:
            try:
                json_captions = caption.json_captions
                for event in json_captions["events"]:
                    for seg in event["segs"]:
                        text += seg["utf8"] + "\n"
            except Exception as e:
                text = ""
                continue
    if text == "":
        return _audio_to_text(yt)[:MAX_CHAR]
    return text.strip()[:MAX_CHAR]


def search_youtube(query: str, num_results: int = 5):
    import re
    from youtube_search import YoutubeSearch

    real_suffix_pat = re.compile(r"/watch\?v=[a-zA-Z0-9_-]{11}")

    results = YoutubeSearch(query, num_results).to_json()
    data = json.loads(results)
    url_suffix_list = []
    if len(data["videos"]) > 0:
        url_suffix_list = [
            "https://www.youtube.com" + real_suffix_pat.findall(video["url_suffix"])[0] for video in data["videos"]
        ]
    return str(url_suffix_list)


if __name__ == "__main__":
    # print(search_youtube("how to make a cake", 5))
    # print(get_youtube_transcript(youtube_id="nl8o9PsJPAQ"))
    print(get_youtube_transcript(url="https://www.youtube.com/watch?v=EYXQmbZNhy8"))
