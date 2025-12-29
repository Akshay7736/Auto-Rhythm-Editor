# scripts/detect_motion.py
import cv2
import mediapipe as mp
import json
import argparse
import os
import math

mp_pose = mp.solutions.pose


def calc_landmark_vector(landmarks):
    return [ (lm.x, lm.y, getattr(lm, 'z', 0)) for lm in landmarks ]


def l2_distance(a, b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def detect_motion(video_path, out_json, frame_step=5):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

    prev_vec = None
    motion_scores = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_step == 0:
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(image_rgb)
            if res.pose_landmarks:
                vec = [ (lm.x, lm.y) for lm in res.pose_landmarks.landmark ]
                if prev_vec is not None:
                    # compute simple motion score: sum of L2 on selected landmarks
                    s = 0.0
                    for (x1,y1),(x2,y2) in zip(prev_vec, vec):
                        dx = x1-x2
                        dy = y1-y2
                        s += (dx*dx + dy*dy)
                    motion_scores.append({
                        "time": frame_idx/fps,
                        "score": s
                    })
                prev_vec = vec
        frame_idx += 1

    cap.release()
    pose.close()

    # find peaks in motion scores
    scores = [m['score'] for m in motion_scores]
    times = [m['time'] for m in motion_scores]

    if len(scores) == 0:
        print("no motion scores found")
        result = {"num_peaks":0, "peaks": []}
    else:
        mean = sum(scores)/len(scores)
        std = (sum((x-mean)**2 for x in scores)/len(scores))**0.5
        thresh = mean + 0.8*std
        peaks = [times[i] for i,s in enumerate(scores) if s > thresh]
        result = {"num_peaks": len(peaks), "peaks": peaks}

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(result, f, indent=4)

    print(f"saved motion peaks to: {out_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--out", default="../output/motion/motion_peaks.json")
    parser.add_argument("--frame-step", type=int, default=5)
    args = parser.parse_args()

    base = os.path.abspath(os.path.dirname(__file__))
    out_json = os.path.abspath(os.path.join(base, args.out))

    detect_motion(args.video, out_json, args.frame_step)
