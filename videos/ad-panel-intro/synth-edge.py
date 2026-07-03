import sys
import os
import asyncio
import edge_tts
import subprocess

if len(sys.argv) < 4:
    print("Usage: python synth-edge.py <text> <voice> <output_wav_path>")
    sys.exit(1)

text = sys.argv[1]
voice = sys.argv[2] # e.g. zh-CN-YunxiNeural
output_path = sys.argv[3] # e.g. D:\...\card-01.wav

async def amain():
    communicate = edge_tts.Communicate(text, voice)
    # Save as temp mp3
    tmp_mp3 = output_path.replace(".wav", ".mp3")
    await communicate.save(tmp_mp3)
    # Transcode to WAV using FFmpeg (resample to 24000Hz mono)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_mp3, "-ar", "24000", "-ac", "1", output_path])
    try:
        if os.path.exists(tmp_mp3):
            os.remove(tmp_mp3)
    except:
        pass

if __name__ == "__main__":
    asyncio.run(amain())
