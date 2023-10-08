from websockets.sync.client import connect
import json
from dotenv import load_dotenv
load_dotenv()
import os

listname = os.environ.get("channel-config")
channelconfraw = open(listname, "r")
channelconf = json.load(channelconfraw)
if 'compress-server' in channelconf:
    ip = channelconf['compress-server']['ip']
    port = channelconf['compress-server']['port']

def job(user, date, infile, outfile):
    with connect(f"ws://{ip}:{port}") as websocket:
        websocket.send(json.dumps(['compress', str(user), str(date), str(infile), str(outfile)]))
        re = websocket.recv()
        if re == '1':
            return True
        