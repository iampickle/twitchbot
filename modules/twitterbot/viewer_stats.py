import modules.checkstream as checkstream
from ..twitter import *
import datetime
import requests
import matplotlib.pyplot as plt
import os
import uuid
import socket
import time
from tabulate import tabulate
from multiprocessing import Process, Queue
from modules.twitterbot.GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer

def connect_to_twitch_chat(channel):
            server = 'irc.chat.twitch.tv'
            port = 6667
            irc = socket.socket()
            irc.connect((server, port))
            irc.send(f'NICK justinfan12345\n'.encode('utf-8'))
            irc.send(f'JOIN #{channel}\n'.encode('utf-8'))
            return irc
class vstats():
    
    def __init__(self, token, stime, workdir, channel):
        
        self.token = token
        self.stime = stime
        self.workdir = workdir
        self.channel = channel
        self.vad = SentimentIntensityAnalyzer()
        self.irc = connect_to_twitch_chat(self.channel)
        self.fileq = Queue()
        self.arrayq = Queue()

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
            return jsondata['data'][0][type]
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
                    if now_title != old_title:
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
                    print('pre exit waiting 15min')
                    time.sleep(900)
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('exiting')
                        break
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
        

    def read_chat(self):
        buffer = ''
        buffer += self.irc.recv(2048).decode('utf-8')
        lines = buffer.split('\n')
        buffer = lines.pop()
        for line in lines:
            if "PRIVMSG" in line:
                username = line.split('!')[0][1:]
                message = ':'.join(line.split(':')[2:])
                return username, message, time.time()
    
    def collect_chat(self):
        bigbuarray = []
        c = 0
        while True:
            message = self.read_chat()
            if message != None:
                bigbuarray.append(message)
            if c == 50:
                if checkstream.checkUser(self.channel, self.token) == False:
                    print('pre exit waiting 15min')
                    time.sleep(900)
                    if checkstream.checkUser(self.channel, self.token) == False:
                        print('exiting')
                        self.arrayq.put(bigbuarray)
                    else:
                        pass
                    



    def start(self):
        cd = Process(target=self.collect_data)
        cd.start()
        vs = Process(target=self.collect_chat)
        vs.start()
        cd.join()
        vs.join()
        
        f = self.fileq.get()
        a = self.arrayq.get()
        name_counts = {}

        for item in a:
            name = item[0]
            if name in name_counts:
                name_counts[name] += 1
            else:
                name_counts[name] = 1
                
        sorted_name_counts = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        table = tabulate(sorted_name_counts, headers=["Name", "Count"], tablefmt="simple")
        tweet_pic(f[0], f"chart of viewercount over stream from: {self.channel}\r{''.join(f[1])}\rtop catter\r{table}")

        
        
        