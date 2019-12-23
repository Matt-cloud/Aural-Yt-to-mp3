from flask import Flask, request, render_template
from flask_socketio import SocketIO
from utils.basic import settings, join, createToken, makeResponse

import json
import os
import youtube_dl
import requests
    

app = Flask(__name__)
main_api_token = createToken(10)
socket = SocketIO(app)
yt_video = "https://youtube.com/watch?v="
downloads_folder = join("downloads")

@socket.on("convertRequest")
def on_convertRequest(data):
    root = request.url_root
    download_api = root + "api/v1/download"
    requests.post(f"{download_api}?id={data['id']}&token={main_api_token}&sid={request.sid}")

@app.route("/api/v1/download", methods=["POST"])
def download():
    video_id = request.args.get("id")
    token = request.args.get("token")
    sid = request.args.get("sid")

    def progress_hook(d):
        if "_percent_str" in list(d.keys()):
            percentage = float(d["_percent_str"].replace("%", "").replace(" ", ""))
            complete = False
        else:
            percentage = 100.0
            complete = True
        
        socket.emit("convert_progress", {
            "percentage": percentage,
            "complete": complete,
            "process": "Converting..."
        }, room=sid)
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": join(f"{downloads_folder}/%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ],
        "progress_hooks": [progress_hook]
    }

    if not sid:
        return makeResponse({
            "error_message": "Session id not provided."
        }, "missing_session_id", 401)

    if token:
        if token == main_api_token:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([yt_video + video_id])
                except youtube_dl.utils.DownloadError:
                    return makeResponse({
                        "error_message": "The video you requested does not exist or is private."
                    }, "video_not_found", 404)
            return makeResponse()
        return makeResponse({
            "error_message": "The token you provided does not match the required token."
        }, "unauthorized_token", 403)
    return makeResponse({
        "error_message": "You did not provide a token."
    }, "missing_token", 403)

@app.route("/")
def index():
    return render_template("index.html")

def main():
    socket.run(app, **settings()["flask_options"])

if __name__ == "__main__":
    main()
