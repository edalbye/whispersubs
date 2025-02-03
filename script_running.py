from pathlib import Path
import tkinter.filedialog as tkfd
import time
import logging

import customtkinter as ctk
import torch
from transformers import pipeline
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

import main
import subtitling
from constants import valid_video_file_types
from utils import get_list_of_videos





def run_process(appUI, model_id = "openai/whisper-large-v3"):
    parameters = set_parameters(appUI.lang_selection.get(), appUI.replace_lang.get(), appUI.selected_lang.get(), appUI.replace.get())

    device = "cuda:0"  if torch.cuda.is_available() else "cpu"
    print(device)
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=10,
        #stride_length_s=2,
        batch_size=1,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )
    path = Path(appUI.path.get())
    if appUI.input_mode.get() == 'Single File':
        list_of_videos = [path]
    elif appUI.input_mode.get() == 'Folder':
        list_of_videos = get_list_of_videos(path, appUI.include_subfolders.get())
    else:
        raise RuntimeError("Invalid input mode")

    while list_of_videos:
        video_path = list_of_videos.pop()
        try:
            subtitling.subtitle_file(path = video_path, pipe = pipe, parameters=parameters)
        except Exception as e:
            logging.error('Error at %s', 'division', exc_info=e)


def set_parameters(lang_selection, replace_lang, selected_lang, replace):
    parameters = subtitling.SubbingParameters()
    if lang_selection == "Auto-Detect Single Language":
        parameters.multi_lang = False
        if replace_lang:
            parameters.replace = True
    elif lang_selection == "Auto-Detect Multiple Language":
        parameters.multi_lang = True
    elif lang_selection == "Choose Language":
        parameters.multi_lang = False
        parameters.provide_lang = True
        parameters.provided_lang = selected_lang
    
    if replace:
        parameters.replace = True
    else:
        parameters.replace = False

    return parameters




