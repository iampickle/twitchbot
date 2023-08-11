import os
from dotenv import load_dotenv
load_dotenv()
from simple_youtube_api.Channel import Channel
from simple_youtube_api.LocalVideo import LocalVideo

dir = os.environ.get("dir")
dir += '/.yt-credentials'

print(os.path.join("client_secret.json",dir))
channel = Channel()
channel.login(os.path.join(dir,"client_secret.json"), os.path.join(dir,"credentials.storage"))