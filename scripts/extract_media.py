# scripts/extract_media.py
import os
import cv2
import argparse

def extract_frames_opencv(video_path, frames_out, step=5):
    os.makedirs(frames_out, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    print(f"fps: {fps}, total frames: {total}")

    idx = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if idx % step == 0:
            timestamp = idx / fps
            out_name = os.path.join(frames_out, f"frame_{saved:06d}_t{timestamp:.3f}.jpg")
            cv2.imwrite(out_name, frame)
            saved += 1

        idx += 1

    cap.release()
    print(f"saved {saved} frames to {frames_out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--frames-out", default="../output/frames")
    parser.add_argument("--frame-step", type=int, default=5)
    args = parser.parse_args()

    video_path = os.path.abspath(args.video)
    base = os.path.abspath(os.path.dirname(__file__))
    frames_out = os.path.abspath(os.path.join(base, args.frames_out))
    os.makedirs(frames_out, exist_ok=True)

    print("extracting frames...")
    try:
        extract_frames_opencv(video_path, frames_out, args.frame_step)
    except Exception as e:
        print("error extracting frames:", e)
        raise

    print("done")
