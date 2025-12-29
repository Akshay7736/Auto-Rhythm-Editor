1. create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1


2. install requirements
pip install -r requirements.txt


3. ensure ffmpeg is installed and on PATH
ffmpeg -version


4. run streamlit app
streamlit run app.py


5. upload a video and an optional audio file


notes:
- scripts create output files under output/ directory
- if your video has no audio, upload a separate audio file