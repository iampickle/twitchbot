import os
from dotenv import load_dotenv
load_dotenv()
import subprocess


cookies = os.environ.get("session-cookies")

def tiktok_upload(channel, date, videopath):
    subprocess.call(['tiktok-uploader', '-v', videopath, '-d', f'Zusammenfassung von {channel} am {date} #foryou #foryoupage #fyp #streaming #twitch #hightlight #{channel} #{channel}twitch #funny #germantwitch #lol', '-c', cookies], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'done with uploading {channel} to tiktok!')