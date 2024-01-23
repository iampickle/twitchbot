from __future__ import unicode_literals
from modules.twitterbot.db import *
from modules.twitter import *
import modules.weighting as weighting
from modules.twitterbot.viewer_stats import vstats as vs
import modules.notification as notification
import modules.getauth as getauth
import modules.dl_stream as dl_stream
import modules.checkstream as checkstream
import logbook
from multiprocessing import Process
import json
import time
import sys
import subprocess
import os
from datetime import datetime
from xml.etree.ElementInclude import include
from dotenv import load_dotenv
load_dotenv()


# logsetup
logbook.StreamHandler(sys.stdout).push_application()
log = logbook.Logger('main')
logbook.set_datetime_format("local")

# setup env vars and stuff
listname = os.environ.get("channel-config")
channelconfraw = open(listname, "r")
channelconf = json.load(channelconfraw)
dir = os.environ.get("dir")


class main:
    def __init__(self, channel):
        self.channel = channel
        self.workdir = os.path.join(dir, channel)
        self.token = None
        self.log = None

    # folder routine2
    def sub(self):
        today = datetime.today()
        folder = self.channel + "-stream-" + str(today.strftime("%Y-%m-%d"))
        dbid = None

        if os.path.isdir(workdir+'/'+folder) == False:
            os.mkdir(workdir+'/'+folder)
            self.log.info("📂 sub folder created")
        else:
            self.log.info("📂 sub folder allready created")

        workdir = workdir+'/'+folder+'/'

        self.log.info("📂 working dir is: "+workdir)

        if self.channel in channelconf['streamers']:
            if 'tbot' in channelconf['streamers'][self.channel]:
                if os.environ.get("db-host"):
                    db = database()
                    dbid = db.create_frame(
                        self.channel, now.strftime('%Y-%m-%d %H:%M:%S'))
                    db.cd()
                self.log.info(
                    f'📑 writing to db as {self.channel} id is = {dbid}')
                tweet_text(
                    f'🔴 {self.cshannel} ist live!\nhttps://www.twitch.tv/{self.channel}\nTitel: {checkstream.get_title(self.channel, self.token)}\n#{self.channel}')
                self.log.info('📈 start plot and data collection')
                plotp = Process(target=vs, args=(
                    self.token, 900, workdir, self.channel, dbid))
                plotp.start()

        self.log.info("⬇️ starting download")
        filename = now.strftime("%H.%M")
        dl_stream.dlstream(self.channel, filename, workdir,
                           self.token, today, dbid)

    def starup(self):
        notification.user = self.channel

        if os.path.isdir(dir+'/'+self.channel) == False:
            os.mkdir(dir+'/'+self.channel)
            log.info("📂 folder created")
        else:
            log.info("📂 folder allready created")

        weighting.readstate(self.channel, log)
        wait = 0
        while True:
            try:
                while True:
                    global now
                    now = datetime.now()
                    self.log = logbook.Logger(self.channel)
                    # check if token is to old

                    if wait == 0:
                        wait, self.token = getauth.post(self.channel)
                    elif wait <= time.time():
                        wait, self.token = getauth.post(self.channel)
                    else:
                        pass

                    # check streamstate
                    if checkstream.checkUser(self.channel, self.token) == True:
                        self.log.info("🔴 is online")
                        weighting.onlinetimeweighting(self.channel, self.log)
                        self.sub1()
                    weights = weighting.analyseweights()
                    if weights == 'array error':
                        self.log.error(weights)
                        pass
                    # look if array was set reacently and if not just look in hour now in array and the sleep accoringly
                    if len(weights) == 24:
                        time.sleep(120)
                    elif now.hour in weights:
                        time.sleep(30)
                    else:
                        time.sleep(120)
            except Exception as e:
                log.warn(f'Main loop failed restarting, error-code: {e}')


def start_threads():
    process_list = []

    log.info("📂 save path is: "+dir)
    log.info("🧑‍🤝‍🧑 starting workers")

    # with trio.open_nursery() as nursery:
    # nursery.start_soon(uinput)
    for streamer in channelconf['streamers']:
        log.info('starting worker of: '+streamer)
        st = main(streamer)
        process_list.append(Process(target=st.starup))
        # nursery.start_soon(starup, line.rstrip())
    if process_list != 0:
        for process in process_list:
            process.start()


if __name__ == "__main__":
    subprocess.Popen(['python', './modules/uptimecheck.py'])

    start_threads()
