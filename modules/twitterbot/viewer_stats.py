import modules.checkstream as checkstream
from ..twitter import *
import datetime
import requests
import matplotlib.pyplot as plt
import os
import uuid
import time


def collect_data(token, stime, workdir, channel):
    categorylegend = []
    legendcount = 0
    url = 'https://api.twitch.tv/helix/streams?user_login=' + channel
    client_id=os.environ.get("Client-ID-Twitch")
    API_HEADERS = {
                'Client-ID' : client_id,
                'Authorization' : 'Bearer ' + token,
            }
    def get_data(type):
        req = requests.get(url, headers=API_HEADERS)
        jsondata = req.json()
        return jsondata['data'][0][type]
    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    x_values = []
    y_values = []
    change_title = []
    old_title = get_data('game_name')
    
    categorylegend.append(f'start: {old_title}\r')
    while True:
            try:
                viewer = get_data('viewer_count')
                now_title = get_data('game_name')
                if now_title != old_title:
                    legendcount += 1
                    old_title = now_title
                    categorylegend.append(f'{str(legendcount)}: {now_title}\r')
                    print(now_title)
                    change_title.append(datetime.datetime.now())
            except:
                break
            
            if checkstream.checkUser(channel, token) == True:
                data = datetime.datetime.now()
                x_values.append(data)

                y_values.append(viewer)

            elif checkstream.checkUser(channel, token) == False:
                print('pre exit waiting 15min')
                time.sleep(900)
                if checkstream.checkUser(channel, token) == False:
                    print('exiting')
                    break
                else:
                    pass
            time.sleep(stime)

    print('ploting')
    plt.style.use('dark_background')
    plt.vlines(x = change_title, ymin = 0, ymax = max(y_values), color='purple', label='category change')
    # plot
    plt.plot(x_values,y_values, label='viewers')
    # beautify the x-labels
    plt.gcf().autofmt_xdate()
    plt.savefig(filename)
    plt.legend()
    plt.close()
    tweet_pic(filename, f"chart of viewercount over stream from: {channel}", text=''.join(categorylegend))
    #os.remove(filename)