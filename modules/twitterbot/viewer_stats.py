import modules.checkstream as checkstream
from ..twitter import *
import datetime
import requests
import matplotlib.pyplot as plt
import os
import uuid
import time


def collect_data(token, stime, workdir, channel):
    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    client_id=os.environ.get("Client-ID-Twitch")
    url = 'https://api.twitch.tv/helix/streams?user_login=' + channel
    x_values = []
    y_values = []
    while True:
            API_HEADERS = {
                'Client-ID' : client_id,
                'Authorization' : 'Bearer ' + token,
            }
            try:
                req = requests.get(url, headers=API_HEADERS)
                jsondata = req.json()
                viewer = jsondata['data'][0]['viewer_count']
            except:
                break

            if checkstream.checkUser(channel, token) == True:
                data = datetime.datetime.now()
                x_values.append(data)

                y_values.append(viewer)

            elif checkstream.checkUser(channel, token) == False:
                print('exiting')
                break
            time.sleep(stime)

    print('ploting')
    plt.style.use('dark_background')
    # plot
    plt.plot(x_values,y_values)
    # beautify the x-labels
    plt.gcf().autofmt_xdate()
    plt.savefig(filename)
    tweet_pic(filename, f"chart of viewercount over stream from: {channel}")
    #os.remove(filename)