from datetime import datetime
from flask import Flask, request
from jinja2 import Environment, FileSystemLoader
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth.credentials import OAuthCredentials

import dotenv
import json
import os
import sys
import uuid

dotenv.load_dotenv()
client_id = os.environ.get("YTM_CLIENT_ID", "")
client_secret = os.environ.get("YTM_CLIENT_SECRET", "")

if client_id == "" or client_secret == "":
    print("FATAL: missing environment")
    sys.exit(1)

playlists = {}
sessions = {}
tracklists = {}
users = {}

app = Flask(__name__)
env = Environment(loader=FileSystemLoader("www"))

yt = YTMusic(
    "oauth.json",
    oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret)
)


def epoch() -> int:
    return int(datetime.now().strftime("%s"))


# Load the user/password db
try:
    with open("passwords.dat", "r") as fh:
        text = fh.read().split("\n")
        for line in text:
            line = line.strip()
            if len(line) == 0:
                continue
            pair = line.split()
            if len(pair) != 2:
                raise Exception("FATAL: corrupt password file")
            users[pair[0]] = {"password": pair[1]}
except Exception as e:
    print(f"FATAL: errors: {e}")
    raise


def session_expire():
    now = epoch()
    for sessid in sessions:
        if "expiry" not in sessions[sessid]:
            raise Exception("BUG: session missing expiry")
        if sessions[sessid]["expiry"] <= now:
            del sessions[sessid]


def session_get(sessid: str) -> dict | None:
    session_expire()
    if sessid == "" or sessid not in sessions:
        return None

    return sessions[sessid]


def ytm_load_playlists():
    # print(">>>ytm_load_playlists")

    global playlists

    if len(playlists) != 0:
        raise Exception("BUG: ytm_load_playlists called twice")

    try:
        pls = yt.get_library_playlists(None)
        for pl in pls:
            plid = str(uuid.uuid4())
            assert plid not in playlists
            playlists[plid] = {"title": pl["title"], "playlistId": pl["playlistId"]}
    except Exception as e:
        print(f"FATAL: failed to load playlists: {e}")
        raise


def ytm_expire_tracks():
    # print(">>>ytm_expire_tracks")

    # Doing it this way because the disctionary size
    # is not allowed to change when being used as an iterator
    now = epoch()
    tls = []
    for tl in tracklists:
        assert "expiry" in tracklists[tl]
        if tracklists[tl]["expiry"] <= now:
            tls.append(tl)
    for tl in tls:
        del tracklists[tl]


def ytm_load_playlist_tracks(plid: str):
    # print(f">>>ytm_load_playlist_tracks({plid})")

    global playlists, tracklists

    assert plid in playlists

    ytm_expire_tracks()

    if plid in tracklists:
        return

    playlist = yt.get_playlist(playlists[plid]["playlistId"], None)

    tracks = []
    expiry = epoch() + 600
    assert "tracks" in playlist
    for track in playlist["tracks"]:
        tt = {}
        assert "title" in track
        assert "artists" in track
        tt["title"] = track["title"]
        tt["artists"] = ", ".join([ artist["name"] for artist in track["artists"] ])
        tracks.append(tt)

    tracklists[plid] = {
        "expiry": expiry,
        "tracks": tracks
    }


def ytm_get_playlist_tracks(plid: str):
    # print(f">>>ytm_get_playlist_tracks({plid})")

    global tracklists

    assert plid is not None

    if plid == "":
        tracklists = {}
        return

    if plid not in tracklists:
        ytm_load_playlist_tracks(plid)


def h_root_get(plid: str):
    # print(f">>>h_root_get({plid})")

    tl = {} if plid == "" else tracklists[plid]["tracks"]
    return env.get_template("index.html").render(playlist=playlists, tracklist=tl)


def h_root_post(plid: str):
    # print(f">>>h_root_post({plid})")

    assert plid is not None
    assert plid != ""
    assert plid in tracklists

    return env.get_template("index.html").render(playlist=playlists, select=plid, tracklist=tracklists[plid]["tracks"])


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def h_root():
    # print(f">>>h_root")

    global playlists, tracklists

    plid = request.form.get("plid")
    if plid is None:
        # is this even possible?
        plid = ""

    if plid != "" and plid not in playlists:
        print(f"ERROR: POST: unexpected plid: <{plid}>")
        # for pl in playlists:
        #     print(f"INFO: playlist {pl}: {playlists[pl]['playlistId']}: {playlists[pl]['title']}")
        plid = list(playlists.keys())[0]

    ytm_get_playlist_tracks(plid)

    if request.method == "GET":
        return h_root_get(plid)
    else:
        return h_root_post(plid)


ytm_load_playlists()
# for plid in playlists:
#     print(f"INFO: playlist {plid}: {playlists[plid]['title']}")
