from pathlib import Path
import time
import logging
import threading

import customtkinter as ctk
import torch
from CTkMessagebox import CTkMessagebox
from transformers import pipeline
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from huggingface_hub import try_to_load_from_cache as hf_try_to_load_from_cache

import subtitling
from constants import valid_video_file_types
from utils import get_list_of_videos, find_model

def downloading_model(appUI):
    """Code to be run when main button is pressed in UI. Should disable the confirm button, and display processing... instead while process is running, and spin up process in a seperate thread."""
    loading_window_text = f"Downloading {appUI.model_name.get()}"
    run_process_in_thread(appUI, init_model, running_process, loading_window_text)
    #Disable confirm button
    loading_window_text = f"Downloading {appUI.model_name.get()}"
    appUI.confirm_button.configure(state=ctk.DISABLED, text = loading_window_text)

def running_process(appUI):
    """Code to be run when main button is pressed in UI. Should disable the confirm button, and display processing... instead while process is running, and spin up process in a seperate thread."""
    loading_window_text = f"Processing {appUI.path.get()}"
    run_process_in_thread(appUI, run_process, subtitle_complete_pop_up, loading_window_text)

def subtitle_complete_pop_up(appUI):
    #Create pop-up window announcing completion
    completed_text = f"Finshed creating subtitles for {appUI.path.get()}"
    CTkMessagebox(title="Processing Completed", message = completed_text)

def init_model(appUI):
        model_id = find_model(appUI.model_name.get())

        device = "cuda:0"  if torch.cuda.is_available() else "cpu"
    
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)

        processor = AutoProcessor.from_pretrained(model_id)


def run_process_in_thread(appUI, process, process_complete, running_text):
    #Disable confirm button
    appUI.confirm_button.configure(state=ctk.DISABLED, text = running_text)

    def processing():
        process(appUI)
        #Run suppliled function
        process_complete(appUI)
        #Re-enable confirm button
        appUI.confirm_button.configure(state=ctk.NORMAL, text = "Create Subtitles")

    thread = threading.Thread(target=processing, args=())
    thread.start()

def run_process(appUI):
    """Initializes model, and then proceeds to create subtitles based on information from UI."""
    model_id = find_model(appUI.model_name.get())
    parameters = set_parameters(appUI.lang_selection.get(), appUI.replace_lang.get(), appUI.selected_lang.get(), appUI.replace_subs.get())

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

    #Create a list of videos that should be processed
    path = Path(appUI.path.get())
    if appUI.input_mode.get() == 'Single File':
        list_of_videos = [path]
    elif appUI.input_mode.get() == 'Folder':
        list_of_videos = get_list_of_videos(path, appUI.include_subfolders.get())
    else:
        raise RuntimeError("Invalid input mode")

    #Run on all videos in list, logging and continuing through the list on exception.
    while list_of_videos:
        video_path = list_of_videos.pop()
        try:
            subtitling.subtitle_file(path = video_path, pipe = pipe, parameters=parameters)
        except Exception as e:
            logging.error('Error at %s', 'division', exc_info=e)

def run_on_button_press(appUI):
    #Save config
    save_config(appUI)
    # Check if model file exists, and download it if it doesn't
    model_id = find_model(appUI.model_name.get())
    if hf_try_to_load_from_cache(model_id, "model.safetensors"):
        running_process(appUI)
    else:
        downloading_model(appUI)

def save_config(appUI):
    appUI.config.set('main', "input_mode", str(appUI.input_mode.get()))
    appUI.config.set('main', "filepath", str(appUI.path.get()))
    appUI.config.set('main', "model_name", str(appUI.model_name.get()))
    appUI.config.set('main', "lang_selection", str(appUI.lang_selection.get()))
    appUI.config.set('main', "replace_lang", str(appUI.replace_lang.get()))
    appUI.config.set('main', "selected_lang", str(appUI.selected_lang.get()))
    appUI.config.set('main', "replace_subs", str(appUI.replace_subs.get()))

    with open('config.ini', 'w') as f:
            appUI.config.write(f)

def set_parameters(lang_selection, replace_lang, selected_lang, replace_subs):
    """Creates a SubbingParameters object corresponding to parameters entered in ui."""
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
    
    if replace_subs:
        parameters.replace = True
    else:
        parameters.replace = False

    return parameters
