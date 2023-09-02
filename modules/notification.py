import requests
from dotenv import load_dotenv
load_dotenv()
import os
from logbook import Logger, StreamHandler


class notification:

    def __init__(self):
        if os.environ.get("Authorization-IFTTT"):
            self.Authtoken = os.environ.get("Authorization-IFTTT")
            self.event = os.environ.get("event")
            self.user = ''
            self.check=True
        else:
            self.check=False
            

    def message(self, message):
        if self.check == True:
            log = Logger(self.user)
            report = {}
            report["value1"] = message
            try:
                requests.post(f"https://maker.ifttt.com/trigger/{self.event}/with/key/{self.Authtoken}", data=report)
            except Exception as e:
                print(f"notification could not be send: {e}")

            log.info(f'📨 send message:"{message}", to event:"{self.event}"')