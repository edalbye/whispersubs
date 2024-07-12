import argparse
import datetime
import math
from pathlib import Path
from statistics import mode
import numpy as np
from scipy.signal import resample
from dataclasses import dataclass

import moviepy.editor as mpy
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


@dataclass
class SubbingParameters:
    replace: bool=True
    multi_lang: bool=True
    replace_lang: bool=False
    preserve_intermediary_files: bool=False
    provide_lang: bool = False
    provided_lang: str = ""

class VideoSubbing:
    """
    Custom class for managing data involved in generating a subtitle track for a given .mp4 video,
    assumed to be located in directory\video_name.mp4
    """
    def __init__(self, file, pipe, *, parameters=None):
        try:
            if file.suffix.lower() == ".mp4":
                self.file = file
            else:
                raise TypeError("Can only process .mp4 files")
        except TypeError as e:
            print("Error: %s." % e)

        if parameters is None:
            self.parameters = SubbingParameters()
        else:
            self.parameters = parameters
        
        self.pipe = pipe

        #Extract audio data from file
        with mpy.AudioFileClip(str(self.file)) as mp3:
            self.audio_input = mp3_to_mono_soundarray_16kHz(mp3)

        #Determine which language should be used if only processing from one language
        if not self.parameters.multi_lang:
            if self.parameters.provide_lang:
                self.lang = self.parameters.provided_lang
            else:
                self.lang = determine_lang(audio_input=self.audio_input, file=self.file, pipe=self.pipe, replace_lang=self.parameters.replace_lang, preserve_intermediary_files=self.parameters.preserve_intermediary_files)

    def apply_whisper(self):
        """
        Applies whisper model using auto language if multi_lang=True,
        and otherwise using language as described in self.makelang
        """
        if self.parameters.multi_lang:
            result = self.pipe(self.audio_input, return_timestamps=True,
                 generate_kwargs={"task": "translate"})
        else:
            result = self.pipe(self.audio_input, batch_size = 8, return_timestamps=True,
                 generate_kwargs={"language": self.lang, "task": "translate"})
        return result["chunks"]

    def cleanup_mp3(self):
        """
        Removes video_name.mp3 file 
        that is created during processing
        """
        try:
            self.file.with_suffix(".mp3").unlink()
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))


    def cleanup_langfile(self):
        """
        Removes video_namelang.txt file
        that is created during processing
        """
        try:
            self.file.with_name(self.file.stem+"lang.txt").unlink()
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))


    def create_subs(self):
        """
        Creates a subtitle file called video_name.srt.
        If replace is False, then will check if file exists already and do nothing if it does.
        """
        filesub = self.file.with_suffix(".srt")
        if self.parameters.replace is False and filesub.exists():
            return
        subs = self.apply_whisper()

        write_subs(filesub, subs)

def determine_lang(audio_input, file, pipe, replace_lang=False, preserve_intermediary_files=False):
    """Used to determine what language to use, in the case that only a single language is expected in the audio.
        Divides audio up into 30 second chunks and runs through whisper pipeline "pipe",  then returns the most common 
        language appearing in the output. A text file with all the detected languages, as well as the most common
        detected can be saved with "preserve_intermediary_files"=True. This file will also be checked for before
        doing any processing, and it's result used instead if it is found."""
    filelang = file.with_name(file.stem+"lang.txt") #Location of detected language file
    if filelang.exists() and replace_lang is False:
        with filelang.open(mode="r", encoding="utf-8") as f:
            first_line = f.readline()
            lang = first_line.split(":")[-1].strip()
    else:
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

class VideoProcessing:
    """
    Custom class to manage required input data and model,
    use the corresponding method to create subtitles using
    VideoSubbing class
    """
    def __init__(self, path, *, parameters=None, model_id = "openai/whisper-large-v3"):

        self.device = "cuda:0"  if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.model_id = model_id

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id, torch_dtype=self.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        self.model.to(self.device)

        self.processor = AutoProcessor.from_pretrained(self.model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=10,
            #stride_length_s=2,
            batch_size=1,
            return_timestamps=True,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )
        self.parameters = parameters
        self.path = path

    def subtitle_file(self):
        """Produces subtitle file for a given .mp4"""
        if self.path.suffix.lower() == ".mp4":
            subbing = VideoSubbing(
                    file = self.path,
                    pipe = self.pipe,
                    parameters = self.parameters
                )
            subbing.create_subs()
        else:
            print("Warning: Input file was not a .mp4")

    def subtitle_folder(self):
        """Produces subtitle files for all .mp4s in a folder"""
        for file in self.path.glob('*.mp4'):
            if file.is_file():
                print(file)
                subbing = VideoSubbing(
                    file = self.path,
                    pipe = self.pipe,
                    parameters = self.parameters
                )
                subbing.create_subs()


    def subtitle_folder_all(self):
        """Produces subtitle files for all .mp4s in a folder, and all of it's subfolders"""
        self.subtitle_folder()
        for file in self.path.glob('**/*.mp4'):
            if file.is_file():
                print(file)
                subbing = VideoSubbing(
                    file = self.path,
                    pipe = self.pipe,
                    parameters = self.parameters
                )
                subbing.create_subs()


def mp3_to_mono_soundarray_16kHz(mp3):
    # Get the stereo sound array
    stereo_sound_array = mp3.to_soundarray()
    
    # Convert stereo to mono by averaging the channels
    if stereo_sound_array.ndim == 2 and stereo_sound_array.shape[1] == 2:
        mono_sound_array = stereo_sound_array.mean(axis=1)
    else:
        mono_sound_array = stereo_sound_array  # Already mono
    
    # Get the original sample rate
    original_sample_rate = mp3.fps
    
    # Define the new sample rate
    new_sample_rate = 16000
    
    # Calculate the number of samples for the new sample rate
    number_of_samples = int(len(mono_sound_array) * new_sample_rate / original_sample_rate)
    
    # Resample the audio
    resampled_sound_array = resample(mono_sound_array, number_of_samples)
    
    return resampled_sound_array

def run_command_line():
    """Captures arguments from the command line, and creates subtitles based on inputs"""
    parser = argparse.ArgumentParser()

    #parser.add_argument("location", type=str)
    parser.add_argument("--input_mode", choices=['file', 'folder', 'rootdir'], default = 'file',
                        help='Use folder or rootdir to process all files, or all subfolders')
    parser.add_argument("--replace", action='store_true',
                        help='Overwrite existing subtitle files')
    parser.add_argument("--multi_lang", action='store_true',
                        help='To process multiple languages within the same file')
    parser.add_argument("--replace_lang", action='store_true',
                        help='Force script to redetect language, if relevent')
    parser.add_argument("--preserve_intermediary_files", action='store_true',
                        help='Remove auxillary files created during processing')



    args = parser.parse_args()

    location = Path(r"C:\Users\darkt\hindivideotest.mp4")

    #location = Path(args.location)
    input_mode = args.input_mode

    parameters = SubbingParameters(replace = args.replace, multi_lang = args.multi_lang, replace_lang = args.replace_lang, preserve_intermediary_files = args.preserve_intermediary_files)

    print(parameters)

    VideoProcessingRun = VideoProcessing(path = location, parameters = parameters)

    if input_mode == 'file':
        VideoProcessingRun.subtitle_file()
    elif input_mode == 'folder':
        VideoProcessingRun.subtitle_folder()
    elif input_mode == 'rootdir':
        VideoProcessingRun.subtitle_folder_all()

#mp3 = mpy.AudioFileClip(r"C:\Users\darkt\shorttest.mp3")
#aud = mp3_to_mono_soundarray_16kHz(mp3)

if __name__ == "__main__":
    run_command_line()
