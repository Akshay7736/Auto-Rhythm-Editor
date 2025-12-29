# app.py
import streamlit as st
import os
import subprocess
import tempfile

st.set_page_config(page_title="auto rhythm editor", layout="centered")

BASE = os.path.abspath(os.path.dirname(__file__))
SCRIPTS = os.path.join(BASE, 'scripts')
OUT_DIR = os.path.join(BASE, 'output')
PYTHON = os.path.join(BASE, ".venv", "Scripts", "python.exe")  # use venv python

os.makedirs(OUT_DIR, exist_ok=True)

st.title('auto rhythm video editor')

video_up = st.file_uploader('upload video', type=['mp4','mov'])
audio_up = st.file_uploader('upload audio (optional)', type=['mp3','wav'])

if st.button('process'):
    if not video_up:
        st.error('please upload a video')
    else:
        with st.spinner('saving files...'):
            tmp = tempfile.mkdtemp()
            video_path = os.path.join(tmp, 'input_video.mp4')
            with open(video_path, 'wb') as f:
                f.write(video_up.read())

            if audio_up:
                audio_path = os.path.join(tmp, 'input_audio.wav')
                with open(audio_path, 'wb') as f:
                    f.write(audio_up.read())
            else:
                audio_path = None

        try:
            st.info('extracting frames...')
            cmd = [PYTHON, os.path.join(SCRIPTS, 'extract_media.py'), video_path, '--frame-step', '5']
            subprocess.run(cmd, check=True)

            # beat detection
            if audio_path:
                ainput = audio_path
            else:
                ainput = os.path.join(BASE, 'output', 'audio', 'extracted_audio.wav')

            if os.path.exists(ainput):
                st.info('detecting beats...')
                cmd = [PYTHON, os.path.join(SCRIPTS, 'extract_beats.py'), ainput]
                subprocess.run(cmd, check=True)
            else:
                st.warning('no audio available; proceeding with motion-only sync')

            st.info('detecting motion...')
            cmd = [PYTHON, os.path.join(SCRIPTS, 'detect_motion.py'), video_path]
            subprocess.run(cmd, check=True)

            st.info('matching beats & generating final video...')
            beats_json = os.path.join(BASE, 'output', 'peaks', 'peaks.json')
            motion_json = os.path.join(BASE, 'output', 'motion', 'motion_peaks.json')
            out_final = os.path.join(BASE, 'output', 'final', 'final_video.mp4')

            cmd = [
                PYTHON,
                os.path.join(SCRIPTS, 'match_and_edit.py'),
                video_path,
                '--beats', beats_json,
                '--motion', motion_json,
            ]
            if audio_path:
                cmd += ['--audio', audio_path]
            else:
                extracted_audio = os.path.join(BASE, 'output', 'audio', 'extracted_audio.wav')
                if os.path.exists(extracted_audio):
                    cmd += ['--audio', extracted_audio]

            cmd += ['--out', out_final]
            subprocess.run(cmd, check=True)

            st.success('processing finished')
            st.video(out_final)
            with open(out_final, 'rb') as f:
                st.download_button('download final video', f, file_name='final_video.mp4')

        except subprocess.CalledProcessError as e:
            st.error('processing failed: ' + str(e))
