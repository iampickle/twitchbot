from __future__ import unicode_literals
from xml.etree.ElementInclude import include
from dotenv import load_dotenv
load_dotenv()
import datetime
import os
import subprocess
import sys
import time
import json
from datetime import date
from multiprocessing import Process
import subprocess

import logbook

import modules.checkstream as checkstream
import modules.dl_stream as dl_stream
import modules.getauth as getauth
import modules.notification as notification
import modules.twitterbot.viewer_stats as viewer_stats
import modules.weighting as weighting
from modules.twitter import *

#logsetup
logbook.StreamHandler(sys.stdout).push_application()
log = logbook.Logger('main')
logbook.set_datetime_format("local")

#setup env vars and stuff
now = datetime.datetime.now()
listname = os.environ.get("channel-config")
channelconfraw = open(listname, "r")
channelconf = json.load(channelconfraw)
dir = os.environ.get("dir")

#folder routine2
def sub1(channel, token):
    workdir = dir+'/'+channel
    today = date.today()
    folder = channel + "-stream-" + str(today)

    if os.path.isdir(workdir+'/'+folder) == False:
        os.mkdir(workdir+'/'+folder)
        log.info("📂 sub folder created")
    else:
        log.info("📂 sub folder allready created")

    workdir = workdir+'/'+folder+'/'

    log.info("📂 working dir is: "+workdir)

    if channel in channelconf['streamers']:
        if 'tbot' in channelconf['streamers'][channel]:
            tweet_text(f'🔴 {channel} ist live!\nhttps://www.twitch.tv/{channel}\nTitel: {checkstream.get_title(channel, token)}\n#{channel}')
            log.info('📈 start plot data collection')
            plotp = Process(
                target=viewer_stats.collect_data, args=(token, 60, workdir, channel,))
            plotp.start()

    log.info("⬇️ starting download")
    filename = now.strftime("%H.%M")
    dl_stream.dlstream(channel, filename, workdir, token)

#folder routine1
def check_main_folder(channel):

    if os.path.isdir(dir+'/'+channel) ==False:
        os.mkdir(dir+'/'+channel)
        log.info("📂 folder created")
    else:
        log.info("📂 folder allready created")

def starup(channel):
    global log
    notification.user = channel
    check_main_folder(channel)
    weighting.readstate(channel, log)
    wait = 0
    
    while True:
        log = logbook.Logger(channel)
        #check if token is to old

        if wait == 0:
            wait, token = getauth.post(channel)
        elif wait <= time.time():
            wait, token = getauth.post(channel)
        else:
            pass
        
        #check streamstate
        if checkstream.checkUser(channel, token) == True:
            log.info("🔴 is online")
            weighting.onlinetimeweighting(channel, log)
            sub1(channel, token)
        weights = weighting.analyseweights()
        if weights == 'array error':
            log.error(weights)
            pass
        #look if array was set reacently and if not just look in hour now in array and the sleep accoringly
        if len(weights) == 24:
            time.sleep(120)
        elif now.hour in weights:
            time.sleep(30)
        else:
            time.sleep(120)

def start_threads():
    process_list =[]

    log.info("📂 save path is: "+dir)
    log.info("🧑‍🤝‍🧑 starting workers")

    #with trio.open_nursery() as nursery:
        #nursery.start_soon(uinput)
    for streamer in channelconf['streamers']:
        log.info('starting worker of: '+streamer)
        process_list.append(Process(target=starup, args=(streamer,)))
            #nursery.start_soon(starup, line.rstrip())
    if process_list != 0:
        for process in process_list:
            process.start()
    
                

if __name__ == "__main__":
    subprocess.Popen(['python', './modules/uptimecheck.py'])
    
    start_threads()