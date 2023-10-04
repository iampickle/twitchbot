from ..twitter import *


def countsaidwords(results, workdir, channel):
    import json
    import numpy as np
    from datetime import timedelta
    import uuid
    import os
    import matplotlib.pyplot as plt

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
        except:
            pass
        time = line['start'] // 60
        farray.append(time)

    plt.style.use('dark_background')
    plt.hist(farray, bins=130)
    plt.title(f'Word-Count over Time:{channel}')
    plt.ylabel('Words')
    plt.xlabel('Time in Minutes')
    plt.savefig(filename)
    plt.close()
    tweet_pic(filename, f"chart of word count over stream from: {channel}") 
