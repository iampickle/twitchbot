from ..twitter import *
import json
import numpy as np
from datetime import timedelta
import uuid
import os
import matplotlib.pyplot as plt

def countsaidwords(results, workdir, channel):
    workdir = os.path.join(workdir, 'analytics/')

    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    #txt = os.path.join(workdir, 'output.txt')
    darray = []
    farray = []
    #with open(txt, 'r') as datafile:
    for line in results:
        try:
            #line = str(line.rstrip())
            line = line.replace("\"", ",")
            line = line.replace("\'", "\"")
            line = json.loads(line)
            time = line['start'] // 60
            farray.append(time)
        except:
            pass

    plt.style.use('dark_background')
    plt.hist(farray, bins=130)
    plt.title(f'Word-Count over Time:{channel}')
    plt.ylabel('Words')
    plt.xlabel('Time in Minutes')
    plt.savefig(filename)
    plt.close()
    tweet_pics([filename], f"chart of word count over stream from: {channel}") 
