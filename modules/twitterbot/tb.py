import json##TEST
import os
from datetime import timedelta
from time import sleep
from tqdm import tqdm
from moviepy.editor import *
from vosk import SetLogLevel

from .mulitthread_vosk import startanalysing
from .GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer
from .notification import notification
from .countwords import countsaidwords
from .percentofmood import moodpercent
from ..twitter import *

listname = os.environ.get("channel-config")
channelconfraw = open(listname, "r")
channelconf = json.load(channelconfraw)


class wordprep:
    sentence_list = []

    def __init__(self, workdir, vfile):
        # look if path has / at end of string. if not add it
        
        SetLogLevel(-1)
        
        if workdir[-1] == '/':
            self.workdir = workdir
        elif workdir[-1] != '/':
            self.workdir = workdir+'/'

        self.vfile = vfile
    # obsolete
    """ def convertevideotowav(self):
        print('converting')
        sound = AudioFileClip(os.path.join(self.workdir,self.vfile))
        sound.write_audiofile(self.afilename, fps=44100, nbytes=2, buffersize=2000, ffmpeg_params=["-ac", "1"], write_logfile=False, verbose=True)
    """
    

    def analyse(self):
        startanalysing(os.path.join(self.workdir, self.vfile), self.workdir)
        


class trimming:

    editlist = []
    trackvods = []
    uploadlist = []
    jsonwordlist = []
    noti = notification()

    def __init__(self, workdir, vfile, word, channel, startpadding=0.7, endpadding=0.5):
        self.workdir = workdir
        self.vfile = vfile
        self.word = word
        self.channel = channel
        self.startpadding = startpadding
        self.endpadding = endpadding

    def timeconv(self, intime):
        return str(timedelta(seconds=intime))[:-4]

    def trim_on_word(self):
        print(self.word)
        print("snipping")
        with open(os.path.join(self.workdir, 'output.txt'), 'r') as fr:
            for line in fr:
                line = str(line.rstrip())
                line = line.replace("\"", ",")
                line = line.replace("\'", "\"")
                self.jsonwordlist.append(line)

        count = 0
        for line in self.jsonwordlist:
            try:
                line = json.loads(line)
                if len(line) == 0 or len(line) == 1:
                    pass
                elif line['word'] in self.word and line['conf'] >= 0.85:
                    count = count + 1
            except:
                pass
        print(f'{count} {self.word}\'s in file')
        self.noti.message(f'there are {count} {self.word}, to be processed')
        wpbar = tqdm(total=count)

        if count == 0:
            print('passing because no words to process')
            return

        if os.path.isdir(os.path.join(self.workdir, 'output')) == False:
                        os.mkdir(os.path.join(self.workdir, 'output'))
        
        for line in self.jsonwordlist:
            try:
                line = json.loads(line)
                if len(line) == 0 or len(line) == 1:
                    pass
                elif line['word'] in self.word and line['conf'] >= 0.8:
                    fstart = line['start']
                    fend = line['end']
                    start = fstart - self.startpadding
                    end = fend + self.endpadding
                    # print('word:', line['word'], 'start:', self.timeconv(start), 'end:', self.timeconv(end))
                    endtimecode = self.timeconv(end)
                    #vodfile = line['word']+'-' + endtimecode.replace(":", ".")+'.mp4'
                    # print(start, end)
                    wpbar.update(1)
                    self.editlist.append(VideoFileClip(os.path.join(
                        self.workdir, self.vfile)).subclip(start, end))
                    # print('append to list\n')
            except Exception as e:
                print('there was n error with  appending the file:'+str(e))
                wpbar.close()
                pass
        wpbar.close()

        print("stitching")

        final_clip = concatenate_videoclips(self.editlist)
        # final_clip.write_videofile(workdir+'output/'+'stitched-video-nonf.mp4')
        final_clip.write_videofile(os.path.join(self.workdir, 'output/', 'stitched-video.mp4'), fps=30,
                                   temp_audiofile="temp-audio.m4a", remove_temp=True, codec="libx264", audio_codec="aac")
        """ subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-err_detect', 'ignore_err', '-i', os.path.join(self.workdir,'output/','stitched-video-nonf.mp4'), '-c', 'copy', os.path.join(self.workdir,'output/','stitched-video.mp4'), '-y'])
        os.remove(os.path.join(self.workdir,'output/','stitched-video-nonf.mp4')) """

        sleep(20)

        clip = VideoFileClip(os.path.join(
            self.workdir, 'output/', 'stitched-video.mp4'))
        print('duration:', clip.duration)
        if clip.duration > 120:
            timessecons = clip.duration // 120
            rest = clip.duration % 120
            startsec = 0
            endsec = 120
            n = 0
            while n != timessecons:
                start = 120 * n
                end = 120 * n + 120
                print('n', start, end)

                clip = VideoFileClip(os.path.join(
                    self.workdir, 'output/', 'stitched-video.mp4')).subclip(start, end)
                clip.write_videofile(os.path.join(self.workdir, 'output/'+str(n)+'-part.mp4'),
                                     temp_audiofile="temp-audio.m4a", remove_temp=True, codec="libx264", audio_codec="aac", logger=None)
                self.uploadlist.append(str(n)+'-part.mp4')
                n += 1
            if rest != 0:
                clip = VideoFileClip(os.path.join(
                    self.workdir, 'output/', 'stitched-video.mp4'))

                print(timessecons, clip.duration)
                start = 120 * timessecons
                end = start + rest
                print('rest', start, end)

                clip = clip.subclip(start, end)
                clip.write_videofile(os.path.join(self.workdir, 'output/'+str(rest)+'-part.mp4'),
                                     temp_audiofile="temp-audio.m4a", remove_temp=True, codec="libx264", audio_codec="aac", logger=None)
                self.uploadlist.append(str(rest)+'-part.mp4')
        
        print(len(self.uploadlist))
        print(self.uploadlist)
        
        sleep(10)
        
        if len(self.uploadlist) != 0:
            print('uploading ...')
            for c, ugoal in enumerate(self.uploadlist, start=1):
                print(f'upload-{c}: {ugoal}')
                tweet_media(self.workdir+'/output/'+ugoal, '#'+self.channel+' '+str(c)+'/'+str(len(self.uploadlist)))
        else:
            print('uploading')
            tweet_media(self.workdir+'/output/'+'stitched-video.mp4', '#'+self.channel)
            


class sentimenttweet:

    def __init__(self, channel, workdir):
        self.channel = channel
        self.workdir = workdir

    def tweetsentiment(self):
        
        moodpercent(self.workdir, self.channel)

        countsaidwords(self.workdir, self.channel)
        
        


class init:
    def __init__(self, path, word, sp=5, ep=3, channel='', test=False):
        patharray = path.split('/')
        self.workdir = "/".join(patharray[:-1])
        self.vfile = patharray[-1:][0]
        self.word = word
        self.channel = channel
        try:
            if channelconf['streamers'][channel]['tbot']['start'] and channelconf['streamers']['tbot'][channel]['end']:
                self.sp = channelconf['streamers'][channel]['start']
                self.ep = channelconf['streamers'][channel]['end']
        except:
            print('start/end puffer not defined setting standart values')
            self.sp = sp
            self.ep = ep
        self.test = test
        print(f'|{sp}| + |video| + |{ep}|')

    def start(self):
        """cv = combinevids(self.workdir)
        """
        # start wordpre
        if self.test == 0 or 3:
            wp = wordprep(self.workdir, self.vfile)
            wp.analyse()
            
        if self.test == 0 or 1:
            # trimming and concating video also uplad to twitter
            tr = trimming(self.workdir, self.vfile, self.word, self.channel, self.sp, self.ep)
            tr.trim_on_word()

            # tweet sentiment analyses
            st = sentimenttweet(self.channel, self.workdir)
            st.tweetsentiment()

        if self.test == 0:
            try:
                os.remove(os.path.join(self.workdir, 'output.txt'))
                #os.remove(os.path.join(self.workdir, self.vfile))
            except Exception as e:
                print('faild to delete temp files', e)
