import json
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import uuid
from ..twitter import *
import os

def countsaidwords(workdir, channel):
    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    txt = os.path.join(workdir, 'output.txt')
    datafile = open(txt, 'r')
    darray = []
    farray = []
    for line in datafile:
        try:
            line = str(line.rstrip())
            line = line.replace("\"", ",")
            line = line.replace("\'", "\"")
            line = json.loads(line)
        except:
            pass
        time = line['start'] // 60
        darray.append(line['start'])
        farray.append(time)
    farray = np.array(farray)    
    nparray = np.array(darray)
    nparray.sort()

    datesarray = []
    valuesarray = []
    last = 0
    for i in range(0, int(farray.max()), 10):
        count = ((last*60 < nparray) & (nparray < i*60)).sum()
        valuesarray.append(count)
        s = str(timedelta(minutes=i)).split(':')
        s = f'{s[0]}:{s[1]}'
        datesarray.append(s)
        last = i
    plt.style.use('dark_background')
    plt.plot(datesarray,valuesarray)   
    plt.tick_params(axis='x', labelrotation=90)
    plt.savefig(filename)
    tweet_pic(filename, f"chart of word count over stream from: {channel}")

    """ plt.hist(nparray, bins=300)
    plt.gca().set(title='Frequency Histogram', ylabel='Frequency')
    plt.show() """
    