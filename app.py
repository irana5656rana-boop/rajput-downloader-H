import os
from urllib.parse import urlparse
from flask import Flask, jsonify, render_template, request
import yt_dlp

app=Flask(__name__)
ALLOWED={"tiktok.com","instagram.com","facebook.com","fb.watch","youtube.com","youtu.be"}

def allowed(url):
    try:
        h=(urlparse(url).hostname or "").lower()
        return any(h==d or h.endswith("."+d) for d in ALLOWED)
    except: return False

def opts():
    return {"quiet":True,"no_warnings":True,"noplaylist":True,"retries":3,
            "fragment_retries":3,"socket_timeout":30,
            "http_headers":{"Accept-Language":"en-US,en;q=0.9"}}

@app.get("/")
def home(): return render_template("index.html")

@app.get("/health")
def health(): return jsonify(status="online",name="RAJPUT Downloader")

@app.post("/api/info")
def info():
    url=((request.get_json(silent=True) or {}).get("url") or "").strip()
    if not allowed(url): return jsonify(success=False,error="Invalid or unsupported URL."),400
    try:
        with yt_dlp.YoutubeDL(opts()) as y: x=y.extract_info(url,download=False)
        return jsonify(success=True,title=x.get("title") or "Video",thumbnail=x.get("thumbnail"),
                       duration=x.get("duration"),uploader=x.get("uploader") or x.get("channel"))
    except Exception as e:
        return jsonify(success=False,error=str(e) or "Video info nahi mili."),500

@app.post("/api/download")
def download():
    import tempfile
    from flask import send_file
    d=request.get_json(silent=True) or {}; url=(d.get("url") or "").strip()
    if not allowed(url): return jsonify(success=False,error="Invalid or unsupported URL."),400
    mode=d.get("mode","video"); q=str(d.get("quality","1080")); folder=tempfile.mkdtemp()
    o=opts(); o["outtmpl"]=os.path.join(folder,"%(title).80s.%(ext)s")
    if mode=="audio":
        o["format"]="bestaudio/best"
        o["postprocessors"]=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    else:
        o["format"]=f"bestvideo[height<={q}]+bestaudio/best[height<={q}]/best"
    try:
        with yt_dlp.YoutubeDL(o) as y:
            x=y.extract_info(url,download=True); p=y.prepare_filename(x)
        if mode=="audio": p=os.path.splitext(p)[0]+".mp3"
        return send_file(p,as_attachment=True,download_name=os.path.basename(p))
    except Exception as e:
        return jsonify(success=False,error=str(e) or "Download failed."),500

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
