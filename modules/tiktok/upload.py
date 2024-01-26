import os
from dotenv import load_dotenv
load_dotenv()
from tiktok_uploader.upload import  upload_videos
from tiktok_uploader.auth import AuthBackend

cookies = os.environ.get("session-cookies")

def tiktok_upload(channel, date, videopath):
    try:
        videos = [
            {
                'path': videopath,
                'description': f'Zusammenfassung von {channel} am {date} #foryou #foryoupage #fyp #streaming #twitch #hightlight #{channel} #{channel}twitch #funny #germantwitch #lol'
            }
        ]
        auth = AuthBackend(cookies=cookies)
        upload_videos(videos=videos, auth=auth, headless=True)
        print(f'done with uploading {channel} to tiktok!')
    except Exception as e:
        print(f'failed tiktok upload of {channel} for reason: {e}')