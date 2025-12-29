import subprocess
import os
import argparse

def ffmpeg_exists():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def merge(video_in, audio_in, output_path):
    if not ffmpeg_exists():
        raise RuntimeError("ffmpeg not installed or not in PATH")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_in,
        "-i", audio_in,
        "-c:v", "copy",
        "-c:a", "aac",
        output_path
    ]

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("audio")
    parser.add_argument("output")
    args = parser.parse_args()

    merge(args.video, args.audio, args.output)
