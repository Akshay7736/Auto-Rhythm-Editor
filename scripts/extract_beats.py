# scripts/extract_beats.py
import librosa
import numpy as np
import argparse
import json
import os


def detect_beats(audio_path, out_json, sr=22050):
    print("loading audio...", audio_path)
    y, sr = librosa.load(audio_path, sr=sr)

    print("extracting onset envelope...")
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    print("detecting peaks...")
    peaks = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")

    print(f"found {len(peaks)} peaks")

    result = {
        "audio_path": audio_path,
        "sample_rate": sr,
        "num_peaks": int(len(peaks)),
        "peaks": peaks.tolist(),
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(result, f, indent=4)

    print(f"saved peak timestamps to: {out_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="path to extracted audio wav/mp3")
    parser.add_argument("--out", default="../output/peaks/peaks.json")
    args = parser.parse_args()

    audio = args.audio
    base = os.path.abspath(os.path.dirname(__file__))
    out_json = os.path.abspath(os.path.join(base, args.out))

    detect_beats(audio, out_json)
