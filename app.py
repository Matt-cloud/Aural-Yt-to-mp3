from flask import Flask, request, render_template
from flask_socketio import SocketIO
from utils.basic import settings, join

import json
import os
import youtube_dl

app = Flask(__name__)
socket = SocketIO(app)
yt_video = "https://youtube.com/watch?v="
downloads_folder = join("downloads")
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": join(f"{downloads_folder}/%(title)s.%(ext)s"),
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }
    ]
}

@app.route("/api/v1/download", methods=["POST"])
def download():
    video_id = request.args.get("id")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_video + video_id])
    return "ok"

@app.route("/")
def index():
    return render_template("index.html")

def main():
    socket.run(app, **settings()["flask_options"])

if __name__ == "__main__":
    main()
