# scripts/match_and_edit.py
import json
import os
import subprocess
import argparse

def ffmpeg_exists():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def load_json(path):
    with open(path,'r') as f:
        return json.load(f)

def find_closest(target, candidates):
    if not candidates:
        return None
    best = min(candidates, key=lambda x: abs(x-target))
    return best

def build_segments(video_path, beats, out_dir, seg_len=0.9, merge_threshold=0.3):
    os.makedirs(out_dir, exist_ok=True)
    seg_files = []

    if not beats:
        return seg_files

    # sort beats
    beats = sorted(beats)

    # merge close beats
    merged = []
    start = beats[0]
    end = beats[0] + seg_len
    for t in beats[1:]:
        if t <= end + merge_threshold:  # close beats, extend segment
            end = t + seg_len
        else:
            merged.append((start, end))
            start = t
            end = t + seg_len
    merged.append((start, end))

    # generate clips
    for i, (start, end) in enumerate(merged):
        out_seg = os.path.join(out_dir, f"seg_{i:03d}.mp4")
        duration = end - start
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start}",
            "-i", video_path,
            "-t", f"{duration}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-strict", "-2",
            out_seg
        ]
        subprocess.run(cmd, check=True)
        seg_files.append(out_seg)
    return seg_files

def concat_segments(seg_files, out_path):
    if not seg_files:
        raise RuntimeError("no segments to concat")
    list_file = os.path.join(os.path.dirname(out_path), "segments.txt")
    with open(list_file, 'w') as f:
        for p in seg_files:
            f.write(f"file '{p}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out_path]
    subprocess.run(cmd, check=True)

def attach_audio(video_path, audio_path, out_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        out_path
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--beats", help="path to peaks.json (audio)")
    parser.add_argument("--motion", help="path to motion_peaks.json (optional)")
    parser.add_argument("--audio", help="audio file to attach (wav/mp3)")
    parser.add_argument("--out", default="../output/final/final_video.mp4")
    args = parser.parse_args()

    if not ffmpeg_exists():
        raise RuntimeError("ffmpeg not found on PATH. Install and add to PATH.")

    base = os.path.abspath(os.path.dirname(__file__))
    beats_json = os.path.abspath(os.path.join(base, args.beats)) if args.beats else None
    motion_json = os.path.abspath(os.path.join(base, args.motion)) if args.motion else None
    audio_path = os.path.abspath(os.path.join(base, args.audio)) if args.audio else None
    out_path = os.path.abspath(os.path.join(base, args.out))

    beats = []
    if beats_json and os.path.exists(beats_json):
        beats = load_json(beats_json).get('peaks', [])

    motion_peaks = []
    if motion_json and os.path.exists(motion_json):
        motion_peaks = load_json(motion_json).get('peaks', [])

    # map beats to nearest motion peaks if available
    if motion_peaks:
        mapped = []
        for b in beats:
            m = find_closest(b, motion_peaks)
            mapped.append(m if m is not None else b)
        target_beats = mapped
    else:
        target_beats = beats

    if not target_beats:
        raise RuntimeError("no beats to process")

    seg_dir = os.path.join(os.path.dirname(out_path), "segments")
    seg_files = build_segments(args.video, target_beats, seg_dir)

    concat_path = os.path.join(os.path.dirname(out_path), "concat.mp4")
    concat_segments(seg_files, concat_path)

    final_path = out_path
    if audio_path:
        attach_audio(concat_path, audio_path, final_path)
    else:
        os.replace(concat_path, final_path)

    print("final video saved:", final_path)
