import subprocess
import os
import time
from faster_whisper import WhisperModel
from TikTokLive import TikTokLiveClient
import asyncio


async def isLivingDef(unique_id):
    client = TikTokLiveClient(unique_id="@" + unique_id)

    try:
        is_live = await client.is_live()

        if is_live:
            print(f"{unique_id} is live")
            print(is_live)
        else:
            print(f"{unique_id} is offline")
        return is_live

    except Exception as ex:
        print(f"{unique_id}: {ex}")

    return False

def get_stream_url(user_id, quality="best"):
    tiktok_url = f"https://www.tiktok.com/@{user_id}/live"
    
    result = subprocess.run(
        [
            "streamlink",
            "--http-cookie", "sessionid=5bd1f4f54127f13c9c5c783aa4d3ec77",
            "--stream-url",
            tiktok_url,
            quality,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise Exception(f"Erreur Streamlink : {result.stderr.strip()}")

    stream_url = result.stdout.strip()
    if not stream_url:
        raise Exception("Aucun flux trouvé pour cette URL")

    return stream_url

def transcribe_live(stream_url, output_file="transcription.txt", chunk_seconds=15):
    model = WhisperModel("base", device="cpu", compute_type="int8")  # "small"/"medium" = plus précis mais plus lent

    with open(output_file, "a", encoding="utf-8") as f:
        while True:
            chunk_path = "chunk_temp.wav"

            # Capture chunk_seconds d'audio depuis le flux live
            cmd = [
                "ffmpeg", "-y",
                "-i", stream_url,
                "-t", str(chunk_seconds),
                "-vn",                    # pas de vidéo
                "-ar", "16000",           # 16kHz requis par Whisper
                "-ac", "1",               # mono
                "-loglevel", "error",
                chunk_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=chunk_seconds + 20)

            if result.returncode != 0 or not os.path.exists(chunk_path):
                print("Erreur ffmpeg, le live est peut-être terminé :", result.stderr)
                break

            # Transcription du segment
            segments, info = model.transcribe(chunk_path, language="fr")  # None = auto-détection langue
            for segment in segments:
                line = f"[{time.strftime('%H:%M:%S')}] {segment.text.strip()}"
                print(line)
                f.write(line + "\n")
                f.flush()

            os.remove(chunk_path)