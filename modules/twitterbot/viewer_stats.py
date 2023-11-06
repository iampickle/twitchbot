import modules.checkstream as checkstream
from ..twitter import *
import datetime
import requests
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
import uuid
import socket
import time
import json
import plotly.figure_factory as ff
import pandas as pd
from multiprocessing import Process, Queue
from modules.twitterbot.GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer
from modules.twitterbot.db import *
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import numpy as np
load_dotenv()


class vstats():
    
    def __init__(self, token, stime, workdir, channel, dbid):
        
        self.client_id = os.environ.get("Client-ID-Twitch")
        self.token = token
        self.stime = stime
        self.channel = channel
        self.dbid = dbid
        self.vad = SentimentIntensityAnalyzer()
        self.fileq = Queue()
        self.arrayq = Queue()
        
        self.workdir = os.path.join(workdir, 'analytics/')
        if not os.path.exists(self.workdir):
             os.makedirs(self.workdir)
             
        self.start()
    
    def collect_data(self):
        categorylegend = []
        legendcount = 0
        url = f'https://api.twitch.tv/helix/streams?user_login={self.channel}'
        API_HEADERS = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.token}',
        }

        # Function to load and resize image
        def load_and_resize_image(game_id):
            url = f'https://api.twitch.tv/helix/games?id={game_id}'
            response = requests.get(url, headers=API_HEADERS)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                game_info = data['data'][0]
                category_picture_url = game_info['box_art_url'].replace('{width}x{height}', '1140x1520')
            else:
                return None

            response = requests.get(category_picture_url)

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
            else:
                print(f"Error fetching image for category '{game_id}'. Status code: {response.status_code}")
                return None
            
            img_width, img_height = img.size
            fixed_width = 25
            new_width = fixed_width
            new_height = int(img_height * (fixed_width / img_width))
            img = img.resize((new_width, new_height))
            return img

        # Function to retrieve data from Twitch API
        def get_data(type=None):
            req = requests.get(url, headers=API_HEADERS)
            jsondata = req.json()
            try:
                if type == None:
                    return jsondata['data'][0]
                else:
                    return jsondata['data'][0][type]
            except:
                return None

        name = str(uuid.uuid4())+'.png'
        filename = os.path.join(self.workdir, name)
        x_values = []
        y_values = []
        change_title = []
        dbarray = []
        old_title = get_data('game_id')

        x_values.append(datetime.datetime.now())
        y_values.append(get_data('viewer_count'))
        categorylegend.append(f'start: {old_title}\r')
        change_title.append([datetime.datetime.now(), old_title])
        print('starting loop')

        while True:
            try:
                chname = None
                time.sleep(self.stime)
                
                try:
                    viewer = get_data('viewer_count')
                    now_title = get_data('game_id')
                    gn = get_data('game_name')
                    
                    if now_title != old_title and now_title != None:
                        legendcount += 1
                        old_title = now_title
                        categorylegend.append(f'{str(legendcount)}: {gn}\r')
                        chname = now_title
                        change_title.append([datetime.datetime.now(), now_title])
                except:
                    break

                if checkstream.checkUser(self.channel, self.token) == True:
                    data = datetime.datetime.now()
                    x_values.append(data)
                    y_values.append(viewer)
                    
                    if chname != None:
                        dbarray.append([time.time(), data, viewer, chname])
                    else:
                        dbarray.append([time.time(), data, viewer])
                elif checkstream.checkUser(self.channel, self.token) == False:
                    print('pre exit plotting waiting 15min')
                    time.sleep(900)
                    
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('exiting plotting')
                        break
                    else:
                        pass
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting loop...")
                break
        if os.environ.get("db-host"):
            db = database()
            db.dump_array_via_id(self.dbid, 'viewotime', dbarray) 
            db.cd()
        
        # Generate random vertical lines
        image_paths = [x[1] for x in change_title]

        # Generate random data for the graph

        # Plot the graph and add indicators
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        ax.plot(x_values, y_values, label='viewers')  # Random graph

        xs = [x[0] for x in change_title]
        xs = np.asarray(xs)
        ax.vlines(xs, 0, ax.get_ylim()[1], color='purple', lw=2, alpha=0.7)
        scaled_images = [load_and_resize_image(path) for path in image_paths]

        for i, (x, img) in enumerate(zip(xs, scaled_images)):
            ab = AnnotationBbox(OffsetImage(img), (x, 1), frameon=False)
            ax.add_artist(ab)

        ax.legend()

        # Show the plot
        plt.savefig(filename)
        plt.close()
        self.fileq.put([filename, categorylegend])
        #os.remove(filename)
    
    def connect_to_twitch_chat(self):
            server = 'irc.chat.twitch.tv'
            port = 6667
            irc = socket.socket()
            irc.settimeout(3)
            irc.connect((server, port))
            irc.send(f'NICK justinfan12345\n'.encode('utf-8'))
            irc.send(f'JOIN #{self.channel}\n'.encode('utf-8'))
            return irc

    def read_chat(self):
        buffer = ''
        try:
            buffer += self.irc.recv(2048).decode('utf-8')
            if buffer == "PING :tmi.twitch.tv\r\n":
                self.irc.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            lines = buffer.split('\n')
            buffer = lines.pop()
            for line in lines:
                if "PRIVMSG" in line:
                    username = line.split('!')[0][1:]
                    message = ':'.join(line.split(':')[2:])
                    return username, message, time.time()
        except Exception as e:
            return None
    
    def collect_chat(self):
        bigbuarray = []
        c = time.time() + 240
        timeout = 0
        self.irc = self.connect_to_twitch_chat()
        while True:
            try:
                c += 1
                message = self.read_chat()
                if message != None:
                    timeout = 0
                    bigbuarray.append(message)
                elif message == None:
                    timeout += 1
                if timeout == 100:
                    time.sleep(5)
                    try:
                        self.irc.close()  # Close the socket connection
                        self.irc = None
                        self.irc = self.connect_to_twitch_chat()
                    except:
                        pass
                if c <= time.time() or timeout >= 20:
                    c = time.time() + 240
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('pre exit chat waiting 15min')
                        time.sleep(900)
                        if checkstream.checkUser(self.channel, self.token) == False:
                            print('exiting chat')
                            try:
                                self.irc.close()  # Close the socket connection
                            except:
                                pass
                            break           
            except Exception as e:
                print(f'main error: {e}')
        
        if os.environ.get("db-host"):    
            #write to db
            db = database()
            db.dump_array_via_id(int(self.dbid), 'topchatter', bigbuarray)
            db.cd()
        
        # Convert to a DataFrame and remove the Timestamp
        df = pd.DataFrame(bigbuarray, columns=['username', 'message', 'timestamp'])
        df = df[['username', 'message']]  # Keep only 'username' and 'message'

        # Count the number of messages per user
        message_counts = df['username'].value_counts().reset_index()
        message_counts.columns = ['username', 'messages']

        # Keep only the top 10
        top = message_counts.head(10)
        fig = ff.create_table(top)
        fig.update_layout(
                        template="plotly_dark",  # Use Plotly's dark theme
                        autosize=False,
                        width=500,
                        height=200,
                        )

        name = str(uuid.uuid4())+'.png'
        filename = os.path.join(self.workdir, name)
        print('ploting table')
        fig.write_image(filename, scale=2)
        
        self.arrayq.put(filename)
                



    def start(self):
        cd = Process(target=self.collect_data)
        vs = Process(target=self.collect_chat)
        cd.start()
        vs.start()
        cd.join()
        vs.join()
        f = self.fileq.get()
        a = self.arrayq.get()
        print('done')
        
        tweet_pics([f[0],a], f"chart of viewercount and top messages of stream from: {self.channel}\r\r{''.join(f[1])}")

        
        
        