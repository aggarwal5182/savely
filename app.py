import os
import uuid
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ── cleanup: delete files older than 10 minutes ──────────────────────────────
def cleanup_old_files():
    while True:
        time.sleep(300)
        cutoff = time.time() - 600
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)

threading.Thread(target=cleanup_old_files, daemon=True).start()

# ── helpers ───────────────────────────────────────────────────────────────────
def build_ydl_opts(quality: str, output_path: str) -> dict:
    """Build yt-dlp options based on requested quality."""
    base = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "cookiefile": None,          # set path if you have cookies.txt
    }

    if quality == "audio":
        base.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    elif quality == "1080":
        base["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best"
        base["merge_output_format"] = "mp4"
    elif quality == "720":
        base["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best"
        base["merge_output_format"] = "mp4"
    elif quality == "480":
        base["format"] = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best"
        base["merge_output_format"] = "mp4"
    else:
        # "best" / photo
        base["format"] = "best"
        base["merge_output_format"] = "mp4"

    return base


# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    """Fetch metadata (title, thumbnail, formats) without downloading."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    # collect available heights
    formats = info.get("formats", [])
    heights = sorted(
        {f["height"] for f in formats if f.get("height") and f.get("vcodec") != "none"},
        reverse=True,
    )

    # build quality options for the frontend
    quality_options = []
    for h in heights[:4]:          # cap at top 4 video resolutions
        quality_options.append({
            "label": f"{h}p",
            "quality": str(h),
            "ext": "mp4",
        })
    if not quality_options:
        quality_options.append({"label": "Best available", "quality": "best", "ext": "mp4"})
    quality_options.append({"label": "Audio only (MP3)", "quality": "audio", "ext": "mp3"})

    return jsonify({
        "title": info.get("title", "Media"),
        "uploader": info.get("uploader") or info.get("channel") or "Unknown",
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "platform": info.get("extractor_key", ""),
        "qualities": quality_options,
    })

@app.route("/api/download", methods=["POST"])
def download():
    """Download the media and return a temporary link."""
    data = request.get_json(silent=True) or {}
    url     = (data.get("url") or "").strip()
    quality = (data.get("quality") or "best").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # fetch title first so we can use it in the filename
    info_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info.get("title", "video")
    except Exception:
        raw_title = "video"

    # sanitise title — remove characters that break filenames
    safe_title = "".join(c for c in raw_title if c.isalnum() or c in " -_()[]").strip()
    safe_title = safe_title[:80] or "video"   # cap length

    # e.g.  "My Cool Reel - 720p.mp4"
    quality_label = f"{quality}p" if quality.isdigit() else quality
    out_tmpl = str(DOWNLOAD_DIR / f"{safe_title} - {quality_label}.%(ext)s")

    opts = build_ydl_opts(quality, out_tmpl)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Download failed: {e}"}), 500

    # find the actual file (extension may differ after post-processing)
    actual_file = None
    for p in DOWNLOAD_DIR.iterdir():
        if p.stem.startswith(safe_title):
            actual_file = p
            break

    if not actual_file or not actual_file.exists():
        return jsonify({"error": "File not found after download"}), 500

    return jsonify({
        "download_url": f"/files/{actual_file.name}",
        "filename": actual_file.name,
        "size_mb": round(actual_file.stat().st_size / 1_048_576, 1),
    })

@app.route("/files/<filename>")
def serve_file(filename):
    """Serve a downloaded file."""
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
