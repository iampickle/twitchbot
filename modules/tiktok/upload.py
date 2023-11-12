import os
from dotenv import load_dotenv
load_dotenv()
import subprocess


cookies = os.environ.get("session-cookies")

def tiktok_upload(channel, date, videopath):
    subprocess.call(['tiktok-uploader', '-v', videopath, '-d', f'Zusammen fassung von {channel} am {date}', '-c', cookies], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('done!')