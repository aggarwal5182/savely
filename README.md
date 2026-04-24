# Savely — Social Media Downloader

A FastDL-style web app built with Flask + yt-dlp that lets users
download videos, photos, and audio from Instagram, TikTok, YouTube,
Twitter/X, Pinterest, and more.

---

## Project structure

```
savely/
├── app.py                  # Flask backend + API routes
├── requirements.txt
├── downloads/              # Temp file storage (auto-cleaned every 10 min)
├── templates/
│   └── index.html          # Jinja2 template
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## Local setup

### 1. Prerequisites

- Python 3.10+
- ffmpeg (required by yt-dlp for merging video+audio streams)

Install ffmpeg:
- **Windows**: https://ffmpeg.org/download.html  → add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 2. Install dependencies

```bash
cd savely
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run

```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## API reference

### POST /api/info
Fetch metadata without downloading.

**Request body:**
```json
{ "url": "https://www.instagram.com/p/..." }
```

**Response:**
```json
{
  "title": "Post title",
  "uploader": "username",
  "thumbnail": "https://...",
  "duration": 42,
  "platform": "Instagram",
  "qualities": [
    { "label": "1080p", "quality": "1080", "ext": "mp4" },
    { "label": "720p",  "quality": "720",  "ext": "mp4" },
    { "label": "Audio only (MP3)", "quality": "audio", "ext": "mp3" }
  ]
}
```

### POST /api/download
Download a file and get a temporary link.

**Request body:**
```json
{ "url": "https://...", "quality": "720" }
```

**Response:**
```json
{
  "download_url": "/files/abc123.mp4",
  "filename": "abc123.mp4",
  "size_mb": 8.4
}
```

### GET /files/<filename>
Serve the downloaded file (as attachment). Files are deleted after ~10 minutes.

---

## Deployment (Render / Railway)

1. Push the project to a GitHub repo.
2. Create a new **Web Service** on Render or Railway.
3. Set **build command**: `pip install -r requirements.txt`
4. Set **start command**: `gunicorn app:app`
5. Add `gunicorn` to requirements.txt.
6. Set environment variable `PYTHON_VERSION=3.11`.

> **Note on Instagram**: Instagram increasingly blocks server-side
> requests. For reliable IG support, provide a `cookies.txt`
> (exported from your browser after logging in) and set the
> `cookiefile` path in `build_ydl_opts()` in app.py.

---

## Keeping yt-dlp updated

Sites update frequently. Run this periodically:
```bash
pip install -U yt-dlp
```

Or add a weekly cron job on your server.

---

## Legal note

This tool accesses only publicly available content.
Users are responsible for complying with the terms of service
of the platforms they download from and applicable copyright law.
