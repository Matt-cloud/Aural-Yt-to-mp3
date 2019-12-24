from flask import Flask, request, render_template, send_file
from flask_socketio import SocketIO
from utils.basic import settings, join, createToken, makeResponse, readJson, writeJson, numerize

import json
import os
import youtube_dl
import requests
import glob
import time 
    

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

@app.route("/api/v1/get_song")
def get_song():
    _id = request.args.get("id")
    return send_file(join(f"{downloads_folder}/{_id}.mp3"), as_attachment=True)

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
    

    url = yt_video + video_id
    info = youtube_dl.YoutubeDL().extract_info(url, download=False)
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": join(f"{downloads_folder}/{info['id']}.%(ext)s"),
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
                    socket.emit("convert_info", {
                        "thumbnail": info['thumbnail']
                    }, room=sid)
                    
                    database = readJson(f"{downloads_folder}/database.json")

                    cached = True
                    createData = True
                    if glob.glob(join(f"{downloads_folder}/{info['id']}.*")):
                        print("File exists")
                        for i, item in enumerate(database['data']):
                            if item['id'] == info['id']:
                                database['data'][i]['downloads'] += 1
                                database['data'][i]['timestamp'] = int(time.time())
                                
                                downloads = database['data'][i]['downloads']
                                timestamp = database['data'][i]['timestamp']

                                createData = False

                    if createData:
                        cached = False
                        ydl.download([url])
                        data = {
                            "id": info['id'],
                            "title": info['title'],
                            "timestamp": int(time.time()),
                            "downloads": 0
                        }

                        downloads = data['downloads']
                        timestamp = data['timestamp']

                        database['data'].append(data)

                    writeJson(f"{downloads_folder}/database.json", database)

                    socket.emit("convert_complete", {
                        "thumbnail": info['thumbnail'],
                        "title": info['title'],
                        "views": numerize(info['view_count']),
                        "likes": numerize(info['like_count']),
                        "dislikes": numerize(info['dislike_count']),
                        "downloads": numerize(downloads),
                        "last_download": timestamp,
                        "upload_date": info['upload_date'],
                        "cached": cached,
                        "download_url": request.url_root + f"api/v1/get_song?id={info['id']}"
                    })

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
