import subprocess
import os
import time
from faster_whisper import WhisperModel
from TikTokLive import TikTokLiveClient
import json
import os
import subprocess

# Ordre de préférence : les qualités basses sont plus souvent en H.264
PREFERRED = ["sd", "hd", "md", "ld", "uhd", "origin"]

def get_stream_url(user_id, quality="h264_hd"):
    tiktok_url = f"https://www.tiktok.com/@{user_id}/live"
    print(tiktok_url)
    print(quality)

    result = subprocess.run(
        ["streamlink", "--http-cookie", f"sessionid=708c4263f0ad25e268778b5bae825828",
         "--stream-url", tiktok_url, quality],
        capture_output=True, text=True, timeout=30,
    )

    if result.returncode != 0:
        raise Exception(f"Erreur Streamlink: {result.stderr.strip()}")

    stream_url = result.stdout.strip()
    if not stream_url:
        raise Exception("Aucun flux trouvé")
    return stream_url

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


import os
import subprocess
import numpy as np

SAMPLE_RATE = 16000
CHUNK_SECONDS = 15
BYTES_PER_CHUNK = SAMPLE_RATE * 2 * CHUNK_SECONDS  # 16 bits = 2 octets par échantillon


def transcribe_live(user_id, output_file):

    print("aaaaa", user_id)
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    audio_url = get_stream_url(user_id, quality="h264_ao")

    ffmpeg = subprocess.Popen(
        ["ffmpeg", "-loglevel", "quiet", "-i", audio_url,
         "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-f", "s16le", "pipe:1"],
        stdout=subprocess.PIPE,
    )

    try:
        while True:
            raw = ffmpeg.stdout.read(BYTES_PER_CHUNK)
            if not raw:
                print("Flux terminé")
                break

            # PCM 16 bits -> float32 entre -1 et 1
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            segments, info = model.transcribe(
                audio,
                language="fr",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            for seg in segments:
                print(seg.text.strip())
                with open(output_file, "a", encoding="utf8") as f:
                    f.write(seg.text.strip()+"\n")
    finally:
        ffmpeg.kill()