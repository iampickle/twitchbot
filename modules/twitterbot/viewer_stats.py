import modules.checkstream as checkstream
from ..twitter import *
import datetime
import requests
import matplotlib.pyplot as plt
import os
import uuid
import socket
import time
import plotly.figure_factory as ff
import pandas as pd
from multiprocessing import Process, Queue
from modules.twitterbot.GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer


class vstats():
    
    def __init__(self, token, stime, workdir, channel):
        
        self.token = token
        self.stime = stime
        self.workdir = workdir
        self.channel = channel
        self.vad = SentimentIntensityAnalyzer()
        self.fileq = Queue()
        self.arrayq = Queue()
        self.irc = self.connect_to_twitch_chat()
    
    def collect_data(self):
        categorylegend = []
        legendcount = 0
        url = 'https://api.twitch.tv/helix/streams?user_login=' + self.channel
        client_id=os.environ.get("Client-ID-Twitch")
        API_HEADERS = {
                    'Client-ID' : client_id,
                    'Authorization' : 'Bearer ' + self.token,
                }
        def get_data(type):
            req = requests.get(url, headers=API_HEADERS)
            jsondata = req.json()
            try:
                return jsondata['data'][0][type]
            except:
                return  None
        name = str(uuid.uuid4())+'.png'
        filename = os.path.join(self.workdir, name)
        x_values = []
        y_values = []
        change_title = []
        old_title = get_data('game_name')
        
        categorylegend.append(f'start: {old_title}\r')
        while True:
                try:
                    viewer = get_data('viewer_count')
                    now_title = get_data('game_name')
                    if now_title != old_title and now_title != None:
                        legendcount += 1
                        old_title = now_title
                        categorylegend.append(f'{str(legendcount)}: {now_title}\r')
                        print(now_title)
                        change_title.append(datetime.datetime.now())
                except:
                    break
                
                if checkstream.checkUser(self.channel, self.token) == True:
                    data = datetime.datetime.now()
                    x_values.append(data)

                    y_values.append(viewer)

                elif checkstream.checkUser(self.channel, self.token) == False:
                    print('pre exit ploting waiting 15min')
                    time.sleep(720)
                    print('exit')
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('exiting ploting')
                        exit()
                    else:
                        pass

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
        c = 0
        timeout = 0
        while True:
            message = self.read_chat()
            if message != None:
                timeout = 0
                bigbuarray.append(message)
            elif message == None:
                timeout += 1
            if timeout == 100:
                time.sleep(5)
                self.irc = self.connect_to_twitch_chat()
            if c == 10 or timeout >= 10:
                c = 0
                if checkstream.checkUser(self.channel, self.token) == False:
                    print('pre exit chat waiting 15min')
                    time.sleep(300)
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('exiting chat')
                        self.irc.close()
                        self.arrayq.put(bigbuarray)
                        exit()
                        
            c += 1
                    



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
        
        # Convert to a DataFrame and remove the Timestamp
        df = pd.DataFrame(a, columns=['username', 'message', 'timestamp'])
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
        
        tweet_pics([f[0],filename], f"chart of viewercount and top messages of stream from: {self.channel}\r\r{''.join(f[1])}")

        
        
        