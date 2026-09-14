import os
import tempfile
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

ALLOWED = {
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "fb.watch",
}


def allowed(url):
    try:
        host = (urlparse(url).hostname or "").lower()
        return any(host == d or host.endswith("." + d) for d in ALLOWED)
    except Exception:
        return False


def base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,

        # YouTube JavaScript challenge solver
        "js_runtimes": {
            "deno": {}
        },

        # Try a browser-like YouTube client
        "extractor_args": {
            "youtube": {
                "player_client": ["web_safari"]
            }
        },

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/18.0 Safari/605.1.15"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        status="online",
        name="RAJPUT Downloader"
    )


@app.post("/api/info")
def info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not allowed(url):
        return jsonify(
            success=False,
            error="Invalid or unsupported URL."
        ), 400

    try:
        options = base_opts()

        with yt_dlp.YoutubeDL(options) as ydl:
            info_data = ydl.extract_info(
                url,
                download=False
            )

        return jsonify(
            success=True,
            title=info_data.get("title") or "Video",
            thumbnail=info_data.get("thumbnail"),
            duration=info_data.get("duration"),
            uploader=(
                info_data.get("uploader")
                or info_data.get("channel")
            ),
        )

    except Exception as e:
        return jsonify(
            success=False,
            error=str(e) or "Video info nahi mili."
        ), 500


@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}

    url = (data.get("url") or "").strip()
    mode = data.get("mode", "video")
    quality = str(data.get("quality", "1080"))

    if not allowed(url):
        return jsonify(
            success=False,
            error="Invalid or unsupported URL."
        ), 400

    folder = tempfile.mkdtemp()

    options = base_opts()

    options["outtmpl"] = os.path.join(
        folder,
        "%(title).80s.%(ext)s"
    )

    if mode == "audio":
        options["format"] = "bestaudio/best"

        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    else:
        options["format"] = (
            f"bestvideo[height<={quality}]"
            f"+bestaudio/"
            f"best[height<={quality}]/best"
        )

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_data = ydl.extract_info(
                url,
                download=True
            )

            file_path = ydl.prepare_filename(info_data)

        if mode == "audio":
            file_path = os.path.splitext(file_path)[0] + ".mp3"

        if not os.path.exists(file_path):
            files = os.listdir(folder)

            if not files:
                raise Exception(
                    "Download file create nahi hui."
                )

            file_path = os.path.join(
                folder,
                files[0]
            )

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )

    except Exception as e:
        return jsonify(
            success=False,
            error=str(e) or "Download failed."
        ), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
            )
