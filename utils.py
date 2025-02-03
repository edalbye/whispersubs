from pathlib import Path
from statistics import mode
import datetime
import math

from constants import valid_video_file_types

def determine_lang(audio_input, file, pipe, replace_lang=False, preserve_intermediary_files=False):
    """Used to determine what language to use, in the case that only a single language is expected in the audio.
        Divides audio up into 30 second chunks and runs through whisper pipeline "pipe",  then returns the most common 
        language appearing in the output. A text file with all the detected languages, as well as the most common
        detected can be saved with "preserve_intermediary_files"=True. This file will also be checked for before
        doing any processing, and it's result used instead if it is found."""
    if audio_input is str(None):
        return None
    filelang = file.with_name(file.stem+"lang.txt") #Location of detected language file
    if filelang.exists() and replace_lang is False:
        with filelang.open(mode="r", encoding="utf-8") as f:
            first_line = f.readline()
            lang = first_line.split(":")[-1].strip()
    else:
        lang = determine_lang_whisper(audio_input, filelang, pipe, preserve_intermediary_files)

    return lang

def determine_lang_whisper(audio_input, filelang, pipe, preserve_intermediary_files=False):
    if audio_input is str(None):
        return None
    result = pipe(audio_input, chunk_length_s=30, return_timestamps=True,
                return_language=True, generate_kwargs={"task": "translate"})
    langlist = [result["chunks"][i]["language"] for i in range(len(result["chunks"]))]
    lang = mode(langlist)

    #Save text file with details of language detection, if requested
    if preserve_intermediary_files:
        with filelang.open(mode="w+", encoding="utf-8") as f:
            f.write(f"Language: {lang}\n\n")
            for i, langi in enumerate(langlist):
                if result["chunks"][i]["timestamp"][0] is None:
                    continue
                else:
                    f.write(f'{str(datetime.timedelta(seconds=math.floor(result["chunks"][i]["timestamp"][0])))}  {langi}\n')
    return lang

def write_subs(filesub, subs):
    """Taking the output "subs" from VideoSubbing.create_subs(), which is of the form pipe(...)["chunks"],
        formats the timestamps and text into the .srt format and saves it to the file "filesub" """
    with filesub.open(mode='w', encoding="utf-8") as f:
        for i, subsi in enumerate(subs):
            sub = []
            sub.append(i+1)
            if subs[i]["timestamp"][0] is None:
                continue
            else:
                sub.append(str(datetime.timedelta(seconds=math.floor(subsi["timestamp"][0]))))
            if subs[i]["timestamp"][1] is None:
                sub.append(str(datetime.timedelta(seconds=math.floor(subsi["timestamp"][0]+10))))
            else:
                sub.append(str(datetime.timedelta(seconds=math.floor(subsi["timestamp"][1]))))
            sub.append(subsi["text"])

            f.write(f'{sub[0]}\n0{sub[1]},000  -->  0{sub[2]},000\n{sub[3]}\n\n')

def find_model(ModelId):
    if ModelId == "CripserWhisper":
        return "nyrahealth/CrisperWhisper"
    if ModelId == "WhisperLargeV3":
        return "openai/whisper-large-v3"
    return ModelId

def get_list_of_videos(path: Path, include_subfolders):
    list_of_videos = []
    append_videos_from_folder(path, list_of_videos)
    if include_subfolders:
        folder_list = [f for f in path.glob('**/*') if f.is_dir()]
        for folder in folder_list:
            append_videos_from_folder(folder, list_of_videos)
    return list_of_videos

def append_videos_from_folder(path: Path, list_of_videos: list):
    for filetype in valid_video_file_types:
        allowed_filename = r"*"+filetype
        for file in path.glob(allowed_filename):
            if file.is_file():
                list_of_videos.append(file)
