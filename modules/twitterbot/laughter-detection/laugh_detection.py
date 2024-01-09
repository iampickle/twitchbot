import configs
from distutils.util import strtobool
from functools import partial
import laugh_segmenter
import os
import sys
import torch
import numpy as np
sys.path.append('./utils/')
import torch_utils
import data_loaders
import audio_utils
import multiprocessing

sample_rate = 8000
model_path = 'checkpoints/in_use/resnet_with_augmentation'
config = configs.CONFIG_MAP['resnet_with_augmentation']
save_to_audio_files = False
save_to_textgrid = True
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

class laughdetect:
    def __init__(self, audio_path, thresholds=0.7, min_lengths=0.2, num_processes=4):
        self.audio_path = audio_path
        self.thresholds = [thresholds]
        self.min_lengths = [min_lengths]
        self.num_processes = num_processes

    def start(self):
        # Load the Model
        model = config['model'](
            dropout_rate=0.0, linear_layer_size=config['linear_layer_size'], filter_sizes=config['filter_sizes'])
        feature_fn = config['feature_fn']
        model.set_device(device)

        if os.path.exists(model_path):
            if device == 'cuda':
                torch_utils.load_checkpoint(model_path+'/best.pth.tar', model)
            else:
                checkpoint = torch.load(
                    model_path+'/best.pth.tar', lambda storage, loc: storage)
                model.load_state_dict(checkpoint['state_dict'])
            model.eval()
        else:
            raise Exception(f"Model checkpoint not found at {model_path}")

        inference_dataset = data_loaders.SwitchBoardLaughterInferenceDataset(
            audio_path=self.audio_path, feature_fn=feature_fn, sr=sample_rate)
        collate_fn = partial(audio_utils.pad_sequences_with_labels,
                             expand_channel_dim=config['expand_channel_dim'])
        inference_generator = torch.utils.data.DataLoader(
            inference_dataset, num_workers=self.num_processes, batch_size=8, shuffle=False, collate_fn=collate_fn)

        # Make Predictions

        probs = []
        for model_inputs, _ in inference_generator:
            x = torch.from_numpy(model_inputs).float().to(device)
            preds = model(x).cpu().detach().numpy().squeeze()
            if len(preds.shape) == 0:
                preds = [float(preds)]
            else:
                preds = list(preds)
            probs += preds
        probs = np.array(probs)

        file_length = audio_utils.get_audio_length(self.audio_path)

        fps = len(probs)/float(file_length)

        probs = laugh_segmenter.lowpass(probs)
        instance_dict = laugh_segmenter.get_laughter_instances(
            probs, thresholds=self.thresholds, min_lengths=self.min_lengths, fps=fps)

        for setting, instances in instance_dict.items():
            laughs = [{'start': i[0], 'end': i[1]} for i in instances]
            print(laughs)


if __name__ == "__main__":
    audio_path = "./tst_wave.wav"  # Replace with the actual path to your audio file
    thresholds = 0.85
    min_lengths = 0.9
    num_processes = 4

    ld = laughdetect(audio_path, thresholds, min_lengths, num_processes)
    ld.start()
