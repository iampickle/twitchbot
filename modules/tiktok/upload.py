import os
from dotenv import load_dotenv
load_dotenv()
import subprocess
from tiktok_uploader.upload import upload_video, upload_videos
from tiktok_uploader.auth import AuthBackend


cookies = os.environ.get("session-cookies")
print(cookies)

def tiktok_upload(channel, date, videopath):
    command = ['/home/tbot/.local/bin/tiktok-uploader', '-v', videopath, '-d', f'Zusammenfassung von {channel} am {date} #foryou #foryoupage #fyp #streaming #twitch #hightlight #{channel} #{channel}twitch #funny #germantwitch #lol', '-c', cookies]
    try:
        result = subprocess.run(
            command,
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        print(f'STDOUT:\n{result.stdout}')
    except subprocess.CalledProcessError as e:
        # Print stderr only when an error occurs
        print(f'STDOUT:\n{result.stdout}')
        print(f'STDERR:\n{e.stdout}')
    except Exception as e:
        print(f'failed tiktok upload of {channel} for reason: {e}')