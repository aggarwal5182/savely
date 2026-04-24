REM 1. Install ffmpeg (needed by yt-dlp to merge streams)
REM    Windows: https://ffmpeg.org/download.html
REM    macOS: brew install ffmpeg

REM 2. Set up Python env
cd savely
python -m venv venv
venv\Scripts\activate        REM Windows

REM 3. Install packages
pip install -r requirements.txt

REM 4. Run
python app.py
REM → Open http://localhost:5000