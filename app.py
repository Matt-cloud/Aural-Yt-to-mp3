from flask import Flask, request, render_template, send_file
from flask_socketio import SocketIO
from utils.basic import settings, join, createToken, makeResponse, readJson, writeJson, numerize

import json
import os
import youtube_dl
import requests
import glob
import time 
import threading
import logging
    
app = Flask(__name__)
main_api_token = createToken(10)
socket = SocketIO(app)
yt_video = "https://youtube.com/watch?v="
max_cache_time = 30

tempCsettings = readJson("settings.json")
if tempCsettings['downloads_folder'][0] == 'cwd':
    tempCsettings['downloads_folder'][0] = os.getcwd()

if tempCsettings['database'][0] == 'cwd':
    tempCsettings['database'][0] = os.getcwd()

downloads_folder = join(tempCsettings['downloads_folder'])
database_path = tempCsettings['database'] # Bad name ik

@socket.on("convertRequest")
def on_convertRequest(data):
    root = request.url_root
    download_api = root + "api/v1/download"
    requests.post(f"{download_api}?id={data['id']}&token={main_api_token}&sid={request.sid}")

@socket.on("update_item_database")
def update_item_database(data):
    _id = data['video_id']
    database = readJson(database_path)

    for i, item in enumerate(database['data']):
        if item['id'] == _id:
            database['data'][i]['downloads'] += 1
            database['data'][i]['timestamp'] = int(time.time())

            downloads = database['data'][i]['downloads']
            timestamp = database['data'][i]['timestamp']

            socket.emit("update_results", {
                "downloads": downloads,
                "last_download": timestamp,
                "id": _id
            })

            break
    writeJson(database_path, database)

@app.route("/api/v1/get_song")
def get_song():
    _id = request.args.get("id")
    title = request.args.get("title")
    
    return send_file(join(f"{downloads_folder}/{_id}.mp3"), attachment_filename=title + ".mp3", as_attachment=True)

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
                    
                    database = readJson(database_path)

                    createData = True
                    cached = True
                    appendToDatabase = True

                    # if glob.glob(join(f"{downloads_folder}/{info['id']}.*")):
                    for i, item in enumerate(database['data']):
                        if item['id'] == info['id']:
                            appendToDatabase = False

                            downloads = database['data'][i]['downloads']
                            timestamp = 0

                            if item['cached']:
                                timestamp = database['data'][i]['timestamp']

                                createData = False
                            else:
                                database['data'][i]['cached'] = True
                            break

                    if createData:
                        ydl.download([url])

                        cached = False

                        if appendToDatabase:
                            data = {
                                "id": info['id'],
                                "title": info['title'],
                                "timestamp": 0,
                                "downloads": 0,
                                "cached": True
                            }

                            downloads = data['downloads']
                            timestamp = data['timestamp']
                            database['data'].append(data)

                    writeJson(database_path, database)

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
                        "download_url": request.url_root + f"api/v1/get_song?id={info['id']}&title={info['title']}",
                        "video_id": video_id
                    }, room=sid)

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

def handleCachedSongs():
    while True:
        database = readJson(database_path)

        if max_cache_time == 0:
            break

        for i, item in enumerate(database['data']):
            now = int(time.time())
            item_time = item['timestamp']
            if item_time != 0:
                seconds_passed = now - item_time
                
                if seconds_passed > max_cache_time:
                    song_path = join(f"{downloads_folder}/{item['id']}.mp3")
                    if os.path.exists(song_path):
                        os.remove(song_path)
                        database['data'][i]['cached'] = False
                        database['data'][i]['timestamp'] = 0

                    # database['data'][:] = [d for d in database['data'] if d.get("id") != item['id']]
                    writeJson(database_path, database)

        time.sleep(10)

def main():
    threading.Thread(target=handleCachedSongs, daemon=True).start()
    socket.run(app, **settings()["flask_options"])

if __name__ == "__main__":
    main()
