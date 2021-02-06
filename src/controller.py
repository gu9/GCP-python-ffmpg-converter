from rss_handler import RssHandler
from gdrive_manager import GdriveManager
from video_handler import VideoHandler
from youtube_manager import YoutubeUploader
from pathlib import PosixPath
import sqlite3 as sql
import os
import platform
import requests
from datetime import datetime as dt
import configparser
import time

_PLAT_SYS = platform.system()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/credentials.json"

if _PLAT_SYS == "Darwin":
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = "/usr/local/etc/openssl/cert.pem"
elif _PLAT_SYS == "Linux":
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = "/etc/ssl/certs/ca-certificates.crt"


class Controller:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.rss_manager = RssHandler(self.config.get("OTHER", "rss_url"))
        self.vid_parts = {
                "font": self.config.get("VIDEO", "font"),
                "intro": self.config.get("VIDEO", "intro"),
                "transition": self.config.get("VIDEO", "transition"),
                "outro": self.config.get("VIDEO", "outro"),
                "background_music": self.config.get("VIDEO", "background_music"),
        }
        self.continue_to_upload = True

    def delete_garbage_files(self):
        protected_files = list(self.vid_parts.values())
        p = PosixPath("vid_sources")
        for file in p.iterdir():
            if file.as_posix() not in protected_files:
                file.unlink()

    def upload_content(self, video_file):
        vid_info = self.create_vid_info()
        # TO Youtube
        # uploading_process = youtube.initialize_upload(
        #     title=vid_info["title"], description=vid_info["desc"], video_file=video_file
        # )

        # TO Gdrive
        gdrive = GdriveManager()
        uploading_process = gdrive.upload_video_content(video_file, vid_info["info_file"])
        if uploading_process is True:
            time.sleep(300)
            youtube = YoutubeUploader()
            youtube.update_desc(vid_title=vid_info["desc"])
        return True

    def create_vid_info(self):
        vid_title = f"{dt.strftime(dt.now(), '%d/%m/%Y')} Trending News in The Netherlands."
        desc = f"{dt.strftime(dt.now(), '%d/%m/%Y')} Trending News in The Netherlands."
        for news in self.rss_manager.rss_feeds.values():
            title, url, excerpt = news["title"], news["url"], news["content"]["txt"]
            desc += "\n" + title + "\n" + "-" * 10 + "\n" + excerpt + "\n" + url + "\n" + "-" * 30 # todo test this bitch
        # save to file
        info_file = "vid_sources/vid_info.txt"
        with open(info_file, "+w") as file:
            file.writelines(f"Title: {vid_title}\n")
            file.writelines("*"*15 + "\n")
            file.writelines(desc)
        info = {"title": vid_title, "desc": desc, "info_file": info_file}
        return info

    def initialize_process(self):
        if not self.rss_manager.rss_feeds:
            pass
        else:
            video_producer = VideoHandler(self.rss_manager.rss_feeds, self.vid_parts)
            news_video = video_producer.create_news_video()
            # news_video = 'vid_sources/finished.mp4'
            upload = self.upload_content(news_video)
            if upload is True:
                self.delete_garbage_files()
                return True
            else:
                self.continue_to_upload = False


if __name__ == "__main__":

    # while True:
    initialize = Controller()

    initialize.initialize_process()
