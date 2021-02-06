from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime as dt


class GdriveManager(GoogleAuth):
    def __init__(self):
        super().__init__()
        self.CommandLineAuth()  # client_secrets.json need to be in the same directory as the script
        self.drive = GoogleDrive(self)
        # self.main_folder = "1_cEaYA7s8xMmWVYB6zhiI_4-tl7-oEBx"  # serkan
        self.main_folder = "1DcVziAso1QJkJeJi0ke9wYOgJ1snWgWi"  # Name of folder is Youtube

    def upload_video_content(self, video_file, txt_file):
        # create and upload daily folder to main folder
        # folder = self.drive.CreateFile(
        #     {
        #         "title": dt.strftime(dt.now(), "%d/%m/%Y"),
        #         "mimeType": "application/vnd.google-apps.folder",
        #         "parents": [{"id": self.main_folder}],
        #     }
        # )
        # folder.Upload()
        # folder_id = folder.attr["metadata"]["id"]
        vid_title = f"{dt.strftime(dt.now(), '%d/%m/%Y')} Daily NL Trend News"
        date = dt.strftime(dt.now(), "%d-%m-%Y")
        file = self.drive.CreateFile(
            {
                "title": vid_title,
                "mimeType": "video/mp4",
                "parents": [{"id": self.main_folder}],
            }
        )
        file.SetContentFile(video_file)
        file.Upload()
        file1 = self.drive.CreateFile(
            {
                "title": date + ".txt",
                "parents": [{"id": self.main_folder}],
            }
        )
        file1.SetContentFile(txt_file)
        file1.Upload()

        return True