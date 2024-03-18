import json
import time
import subprocess
import multiprocessing
from vosk import Model, KaldiRecognizer, SetLogLevel
from moviepy.editor import AudioFileClip
from tqdm import tqdm
import os
from dotenv import load_dotenv
load_dotenv()

def process_audio(model, filename, thread_num, num_threads, output_queue, process_queue):
    # Initialisiere den Vosk-Sprachmodell und den KaldiRecognizer
    SetLogLevel(-1)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    
    # Berechne die Gesamtdauer des Audiofiles
    audio_clip = AudioFileClip(filename)
    audio_duration = audio_clip.duration
    audio_clip.close()

    # Berechne die Start- und Endposition des aktuellen Prozesses
    start = int((thread_num / num_threads) * audio_duration)
    end = int(((thread_num + 1) / num_threads) * audio_duration)
    print(f'process:{thread_num}, START:{start}, END:{end}')

    # Erstelle die ffmpeg-Instanz für den aktuellen Prozess
    ffmpeg_command = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            filename,
            '-ss',
            str(start),
            '-to',
            str(end),
            "-ar",
            '16000',
            "-ac",
            "1",
            "-f",
            "s16le",
            "-",
        ]
    
    with subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE) as process:
        lastend = 0
        while True:
            # Lese den Audiostream des aktuellen Prozesses
            data = process.stdout.read(4000)
            
            if len(data) == 0:
                #print('proc: ', thread_num, 'finished')
                process_queue.put('finished')
                break
            if rec.AcceptWaveform(data):
                part_result = json.loads(rec.Result())
                sentence = part_result['text']
                if len(sentence) <= 1:
                    # sometimes there are bugs in recognition
                    # and it returns an empty dictionary
                    # {'text': ''}
                    continue
                else:
                    for obj in part_result['result']:
                        # print(obj)
                        if len(obj) <= 1:
                            continue
                        else:
                            lenghtword = obj['end']-lastend
                            lastend= obj['end']
                            #xsprint(lenghtword)
                            process_queue.put(lenghtword)
                            obj['end'] = float(obj['end']) + float(start)
                            obj['start'] = float(obj['start']) + float(start)
                            output_queue.put(str(obj))
                            
                                

def transcribe_audio(filename, num_threads):
    vm = os.environ.get("vosk-model")
    # Erstelle eine Warteschlange für die Ergebnisse
    output_queue = multiprocessing.Queue()
    process_queue = multiprocessing.Queue()
    print(vm)
    model = Model(model_name=vm)

    # Erstelle eine Liste der Prozesse
    processes = []
    for i in range(num_threads):
        process = multiprocessing.Process(target=process_audio, args=(model, filename, i, num_threads, output_queue, process_queue))
        processes.append(process)

    # Starte die Prozesse
    for process in processes:
        process.start()

    # Warte auf das Ende der Prozesse
    check_thread = 0
    while True:
        get = process_queue.get()
        if get == 'finished':
            check_thread += 1
        else:
            pass
            #pbar.update(get)
        
        if check_thread == num_threads:
            print('all processes finished')
            break
                

    # Sammle die Ergebnisse aus der Warteschlange
    results = []
    while not output_queue.empty():
        result = output_queue.get()
        results.append(result)

    return results

def startanalysing(filename, workdir):
    # Passe die Anzahl der Threads und den Dateinamen an
    num_threads = int(os.environ.get("vosk-threads"))

    audio_clip = AudioFileClip(filename)
    audio_duration = audio_clip.duration
    print(f'audio lenth: {audio_duration}')
    # Führe die Transkription durch
    results = transcribe_audio(filename, num_threads)

    # Schreibe die Ergebnisse in eine Textdatei
    with open(workdir+'output.txt', 'w') as f:
        for result in results:
            f.write(str(result)+'\n')
    return results
