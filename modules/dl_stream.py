import os
import subprocess
import time
from datetime import date, datetime
from multiprocessing import Process, Semaphore

import re
import glob
from logbook import Logger
from moviepy.editor import *
import json

import modules.twitterbot.youtube_upload as ytupload
from modules.notification import notification
import modules.checkstream as checkstream

noti = notification()
from modules.twitterbot import tb 

listname = os.environ.get("channel-config")
channelconfraw = open(listname, "r")
channelconf = json.load(channelconfraw)

num = 0
pool_sema = Semaphore(6)
clip_start = 0

def extract_time(filename):
        # Extrahiere die Uhrzeit (HH.MM) aus dem Dateinamen
        time_str = os.path.splitext(filename)[0]
        try:
            hours, minutes = map(int, time_str.split('.'))
            return hours, minutes
        except ValueError:
            # Wenn der Dateiname nicht dem erwarteten Muster entspricht, wird die Datei am Ende sortiert
            return 24, 0

def dek(workdir, tempfilename, channel, log, token, pausetime=720):
    noti.message("starting download of: "+channel)
    log.info("⬇️ download started")

    try:
        print(channel)
        subprocess.call(["streamlink", "twitch.tv/" + channel, 'best', "-o", workdir+tempfilename,
                        '-l', 'none', '--hls-duration', '24:00:00'], stdout=subprocess.DEVNULL)
    except Exception as e:
        log.info(e)
        
    waittime = time.time()
    log.info('⚠️ lost stream')
    while True:
        if time.time() - waittime >= pausetime:
            break
        time.sleep(20)
        if checkstream.checkUser(channel, token) == True:
            log.info('❕ stream still active reopening download')
            return 'reopen'
        


def dlstream(channel, filename, workdir, token):
    log = Logger(channel)
    #os.chdir(folder)
    url = 'https://www.twitch.tv/' + channel
    
    #set file 
    now = datetime.now()
    filename = now.strftime("%H.%M")
    tempfilename = "temp_1_" + filename  + ".mp4"
    tempfilename5 = 'temp_1.5_' + filename + '.mp4'
    tempfilename2 = "temp_2_" + filename + ".mp4"
    
    streamcount = 0
    streamfiles = []
    udate = date.today()
    while True:
        check = dek(workdir, filename+'_'+str(streamcount)+'_stream.mp4', channel, log, token)
        streamfiles.append(workdir+filename+'_'+str(streamcount)+'_stream.mp4')
        streamcount += 1
        if check != 'reopen':
            break
    
    
    if len(streamfiles) == 1:
        print(len(streamfiles))
        streamfilenames = streamfiles[0].split('/')[-1]
        print(f'renaming: {streamfilenames} ==> {tempfilename}')
        os.rename(streamfiles[0], workdir+tempfilename)
    if len(streamfiles) > 1:
        log.info('🪡 stitching streamfiles togehter')
        videos = []
        for stream in streamfiles:
            videos.append(VideoFileClip(stream))
        final = concatenate_videoclips(videos)
        final.write_videofile(workdir+tempfilename, verbose=False, logger=None)
        for vin in videos:
            vin.close()
        for streamfile in streamfiles:
            time.sleep(2)
            os.remove(streamfile)
        
    print(workdir+'*.mp4')
    prefiles = glob.glob(workdir+'/*.mp4')
    #prefiles.pop(workdir+filename)
    pattern = re.compile(r"\d\d\.\d\d_\d_stream\.mp4", re.IGNORECASE)
    for i in prefiles:
        i = i.split('/')
        if pattern.match(i[-1]):
            print(f'renaming: {i[-1]} ==> {i[-1][:5]+".mp4"}')
            os.rename(workdir+i[-1], workdir+i[-1][:5]+'.mp4')
        
    prestreamfiles = []
    print(workdir+'*.mp4')
    prefiles = glob.glob(workdir+'/*.mp4')
    #prefiles.pop(workdir+filename)
    opattern = re.compile(r"\d\d\.\d\d\.mp4", re.IGNORECASE)
    for i in prefiles:
        i = i.split('/')
        if opattern.match(i[-1]):
            prestreamfiles.append(i[-1])
    print(prestreamfiles)
    if prestreamfiles == []:
        pass
    else:
        sorted_mp4_files = sorted(prestreamfiles, key=extract_time)
        print(sorted_mp4_files)
        videos = []
        os.rename(workdir+tempfilename, workdir+'2'+tempfilename)
        for stream in sorted_mp4_files:
            videos.append(VideoFileClip(workdir+stream))
        videos.append(VideoFileClip(workdir+'2'+tempfilename))
        final = concatenate_videoclips(videos)
        final.write_videofile(workdir+tempfilename, verbose=False, logger=None)
        for vin in videos:
            vin.close()
        os.remove(workdir+'2'+tempfilename)
        for stream in sorted_mp4_files:
            time.sleep(2)
            os.remove(workdir+stream)
        
        

    log.info("🔴 Recording stream is done")
    noti.message("download done, start fixing of: "+channel)

    log.info("🧰 managing")   
    try:
        if 'tbot' in channelconf['streamers'][channel]:
            log.info("🐦 starting twitter_bot")
            noti.message("start twitterbot")
            noti.message("start fixing")
            subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-err_detect', 'ignore_err', '-i', workdir+tempfilename, '-c', 'copy', workdir+tempfilename5])
            os.remove(workdir+tempfilename)
            log.info("🧰 file fixed")
                 
            tbs = tb.init(os.path.join(workdir, tempfilename5), channelconf['streamers'][str(channel)]['tbot']['words'], channel=channel)
            tbs.start()            
        if 'ytupload' in channelconf['streamers'][channel]:
            if channelconf['streamers'][channel]['ytupload'] == True:
                p = Process(target=fixm, args=(workdir, tempfilename5, tempfilename2, filename, log, 1, channel, udate,))
                p.start()
        else:
            p = Process(target=fixm, args=(workdir, tempfilename, tempfilename2, filename, log, 0, channel, udate,))
            p.start()
    except Exception as e:  
        log.info(e)
    
    return filename

def fixm(workdir, tempfilename,tempfilename2, filename, log, choosen, channel, udate=date.today()):
    time.sleep(25)

    lt1 = tempfilename
    lt2 = tempfilename2
    fn = filename

    #subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-err_detect', 'ignore_err', '-i', workdir+lt1, '-c', 'copy', workdir+lt2])

    if choosen == 0:
        log.info("🧰 file fixed")
        subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-i', workdir+lt1, '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a', 'copy', workdir+fn + ".mp4"])
        log.info("🧰 file compressed")
        
    elif choosen == 1:
        vfile = VideoFileClip(os.path.join(workdir, lt1))
        duration = vfile.duration
        vfile.close()
        if vfile.duration >= 43200:
            vlist = ytupload.yt_pre_splitter(workdir, lt1)
            log.info("⬆️ uploading to youtube")
            print(vlist)
            try:
                for n, vid in enumerate(vlist, start=1):
                    vid = ['/'.join(vid.split('/')[:-1])+'/',vid.split('/')[-1]]
                    print(vid)
                    ytupload.upload(vid[0], vid[1], udate+'/'+str(n), channel)
                for vid in vlist:
                    os.remove(vid)
            except Exception as e:
                print(e)
                log.info("⬆️ youtube upload failed")

        else:
            ytupload.upload(workdir, lt1, udate, channel)

        subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-i', workdir+lt1, '-c:v', 'libx264', '-crf', '21', '-preset', 'faster', '-c:a', 'copy', workdir+fn + ".mp4"])
        log.info("🧰 file compressed")
        
    try:
        #os.remove(workdir+lt2)
        os.remove(workdir+lt1)
        log.info("🗑️ deleted temp files!")
    except Exception as e:
        log.error(f'faild to delete temp files: \n{e}')