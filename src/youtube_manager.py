import google_client
import http.client
import httplib2
import random
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging


# CLIENT_SECRETS_FILE = "./credentials/client_secret.json"
CLIENT_SECRETS_FILE = "./client_secrets.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
httplib2.RETRIES = 1

MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class YoutubeUploader(google_client.GoogleClient):
    def __init__(self):

        super().__init__(
            scope=SCOPES,
            application_name="Youtube Uploader",
            credentials_file="youtube_credentials.json",
            client_secret_file=CLIENT_SECRETS_FILE,
        )
        self.service = build(
            API_SERVICE_NAME,
            API_VERSION,
            http=self.credentials.authorize(httplib2.Http()),
            cache_discovery=False,
        )

    @staticmethod
    def __resumable_upload(request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if response is not None:
                    if "id" in response:
                        logging.log(
                            20,
                            'Video id "%s" was successfully uploaded.' % response["id"],
                        )
                        return True
                    else:
                        logging.log(
                            40,
                            "The upload failed with an unexpected response: %s"
                            % response,
                        )
                        return False
            except HttpError as e:

                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (
                        e.resp.status,
                        e.content,
                    )
                else:
                    logging.log(40, str(e.content))
                    return False

            except RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                logging.log(40, error)
                retry += 1
                if retry > MAX_RETRIES:
                    logging.log(30, "No longer attempting to retry.")
                    return False

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                logging.log(
                    20, "Sleeping %f seconds and then retrying..." % sleep_seconds
                )
                time.sleep(sleep_seconds)

    def initialize_upload(self, title, description, video_file):
        body = dict(
            snippet=dict(
                title=title, description=description, tags=None, categoryId="25"
            ),
            status=dict(privacyStatus="public"),
        )
        insert_request = self.service.videos().insert(
            part=",".join(list(body.keys())),
            body=body,
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True),
        )
        return self.__resumable_upload(insert_request)

    def update_desc(self, vid_title, vid_desc):
        res1 = self.service.channels().list(
            mine=True,
            part='contentDetails'
        ).execute()
        res2 = self.service.playlistItems().list(
            playlistId=res1["items"][0]['contentDetails']['relatedPlaylists']['uploads'],
            part='snippet',
            maxResults=1
        ).execute()
        vid_id = res2["items"][0]["snippet"]["resourceId"]["videoId"]
        vid_snippet = res2["items"][0]["snippet"]
        vid_snippet["description"] = vid_desc
        vid_snippet["title"] = vid_title
        vid_snippet["categoryId"] = 25
        self.service.videos().update(
            part='snippet',
            body=dict(
                snippet=vid_snippet,
                id=vid_id
            )).execute()


if __name__ == '__main__':
    y = YoutubeUploader()

