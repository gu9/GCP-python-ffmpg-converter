from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import argparse
import os
import pathlib


class GoogleClient:
    def __init__(self, scope, application_name, credentials_file, client_secret_file):
        self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        self.flags.noauth_local_webserver = True
        self.scope = scope
        self.application_name = application_name
        self.credentials_file = credentials_file
        self.client_secret_file = client_secret_file
        self.credentials = self._get_credentials()

    def _get_credentials(self):

        # home_dir = os.path.expanduser('')
        # credential_dir = os.path.join(home_dir, "credentials")
        home_dir = str(pathlib.Path(__file__).parent)
        credential_dir = os.path.join(home_dir, "credentials")
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, self.credentials_file)
        store = Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file,
                                                  self.scope)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store, self.flags)
        return credentials
