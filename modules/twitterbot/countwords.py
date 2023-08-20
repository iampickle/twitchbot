import json
import numpy as np
from datetime import timedelta
import uuid
from ..twitter import *
import os


def countsaidwords(workdir, channel):
    import matplotlib.pyplot as plt

    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    txt = os.path.join(workdir, 'output.txt')
    darray = []
    farray = []
    with open(txt, 'r') as datafile:
        for line in datafile:
            try:
                line = str(line.rstrip())
                line = line.replace("\"", ",")
                line = line.replace("\'", "\"")
                line = json.loads(line)
            except:
                pass
            time = line['start'] // 60
            farray.append(time)

    plt.style.use('dark_background')
    plt.hist(farray, bins=300)
    plt.title(f'Word-Count over Time:{channel}')
    plt.ylabel('Words')
    plt.xlabel('Time in Minutes')
    plt.savefig(filename)
    tweet_pic(filename, f"chart of word count over stream from: {channel}") 
