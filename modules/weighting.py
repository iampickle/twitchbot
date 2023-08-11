import datetime
import os
from ast import literal_eval
from logbook import Logger, StreamHandler

dir = os.environ.get("dir")

def readstate(channel, log):
    global dayweights
    log = Logger(channel)
    completefilename = dir+'/'+channel+'/weighting.tmp'

    if os.path.isfile(completefilename) == False:
        dayweights = create_blank(channel, log)
    elif os.path.isfile(completefilename) == True:
        with open(completefilename, 'r') as arrayfile:
            dayweights = literal_eval(arrayfile.read())
    elif dayweights == None:
        dayweights = create_blank(channel, log)
    else:
        with open(completefilename, 'r') as arrayfile:
            dayweights = literal_eval(arrayfile.read())
        
    log.info('📄⬇️ loaded: '+str(dayweights)+', out of: '+completefilename)

def create_blank(channel, log):
    completefilename = f"{dir}/{channel}/weighting.tmp"
    log.info("error no weight data, creating blank")
    with open(completefilename, "a") as arrayfile:
        arrayfile.write("[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]")
        log.info('📄⬆️ file written: ' + completefilename)
    return [0] * 24
    
def onlinetimeweighting(channel, log):
    now = datetime.datetime.now()
    nowtime = now.hour
    log.info(channel+' hour: '+str(nowtime))
    log = Logger(channel)
    completefilename = os.path.join(dir+'/'+channel, 'weighting.tmp')
    arrayfile = open(completefilename, 'r')

    dayweightss = arrayfile.read()
    dayweights = literal_eval(dayweightss)
    arrayfile.close()
    for r in range(len(dayweights)):
        if r == nowtime:   
            if dayweights[nowtime] < 10:
                dayweights[nowtime] += 1  
            else:
                pass
        else:
            if dayweights[r] != 0:
                dayweights[r] -= 0.5
                dayweights[r] = int(dayweights[r])
            elif dayweights[r] == 0:
                pass

    arrayfile = open(completefilename, 'w')
    arrayfile.write(str(dayweights))
    arrayfile.close()
    log.info('📄⬆️ written: '+str(dayweights)+', to: '+completefilename)
    
def analyseweights():
    if not dayweights:
        return 'array error'

    maxval = max(dayweights)
    results = [r for r, weight in enumerate(dayweights) if weight == maxval]
    return results