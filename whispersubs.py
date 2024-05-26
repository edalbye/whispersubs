import argparse
import datetime
import math
from pathlib import Path
from statistics import mode

import moviepy.editor as mpy
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"

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

class VideoSubbing:
    """
    Custom class for managing data involved in generating a subtitle track for a given .mp4 video,
    assumed to be located in directory\video_name.mp4
    """
    def __init__(self, file):
        try:
            if file.suffix.lower() == ".mp4":
                self.file = file
            else:
                raise TypeError("Can only process .mp4 files")
        except TypeError as e:
            print("Error: %s." % e)

    def makemp3(self):
        """
        Creates a video_name.mp3 file containing the audio from the video, if one doesn't exist
        and returns the path to the mp3 file containing audio
        """
        if not (self.file.with_suffix(".mp3")).exists():
            clip = mpy.AudioFileClip(str(self.file))
            clip.write_audiofile(str(self.file.with_suffix(".mp3")))
        return self.file.with_suffix(".mp3")

    def makelang(self, replace_lang=False):
        """
        For use when forcing a single language, which defaults to the most common.
        Creates a txt file video_namelang.txt if replace_lang is True,
        or if file does not already exist. If the file exists reads {lang} from the first line,
        hich should be formatted as "Language: {lang}"
        Returns language to be used.
        """
        filelang = self.file.with_name(self.file.stem+"lang.txt")
        if filelang.exists() and replace_lang is False:
            with filelang.open(mode="r", encoding="utf-8") as f:
                first_line = f.readline()
                lang = first_line.split(":")[-1].strip()
        else:
            result = pipe(str(self.makemp3()), chunk_length_s=30, return_timestamps=True,
                           return_language=True, generate_kwargs={"task": "translate"})
            langlist = [result["chunks"][i]["language"] for i in range(len(result["chunks"]))]
            lang = mode(langlist)
            with filelang.open(mode="w+", encoding="utf-8") as f:
                f.write(f"Language: {lang}\n\n")
                for i, langi in enumerate(langlist):
                    if result["chunks"][i]["timestamp"][0] is None:
                        continue
                    else:
                        f.write(f'{str(datetime.timedelta(
                            seconds=math.floor(result["chunks"][i]["timestamp"][0])))}  {langi}\n')

        return lang

    def apply_whisper(self, pipel, multi_lang=True, replace_lang=False):
        """
        Applies whisper model using auto language if multi_lang=True,
        and otherwise using language as described in self.makelang
        """
        if multi_lang:
            result = pipel(str(self.makemp3()), return_timestamps=True,
                 generate_kwargs={"task": "translate"})
        else:
            result = pipel(str(self.makemp3()), batch_size = 8, return_timestamps=True,
                 generate_kwargs={"language": self.makelang(replace_lang), "task": "translate"})
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


    def create_subs(self, pipel, replace=True, multi_lang=True, replace_lang=False, cleanup=False):
        """
        Creates a subtitle file called video_name.srt.
        If replace is False, then will check if file exists already and do nothing if it does.
        """
        filesub = self.file.with_suffix(".srt")
        if replace is False and filesub.exists():
            return
        subs = self.apply_whisper(pipel, multi_lang = multi_lang, replace_lang = replace_lang)

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

        if cleanup:
            self.cleanup_mp3()
            if not multi_lang:
                self.cleanup_langfile()



def subtitle_file(filename):
    """Produces subtitle file for a given .mp4"""
    if filename.suffix.lower() == ".mp4":
        subbing = VideoSubbing(filename)
        subbing.create_subs(pipe, replace=replace,
                             multi_lang=multi_lang, replace_lang=replace_lang, cleanup=cleanup)
    else:
        print("Warning: Input file was not a .mp4")

def subtitle_folder(directory):
    """Produces subtitle files for all .mp4s in a folder"""
    for file in directory.glob('*.mp4'):
        if file.is_file():
            print(file)
            subbing = VideoSubbing(file)
            subbing.create_subs(pipe, replace=replace,
                                 multi_lang=multi_lang, replace_lang=replace_lang, cleanup=cleanup)


def subtitle_folder_all(directory):
    """Produces subtitle files for all .mp4s in a folder, and all of it's subfolders"""
    subtitle_folder(directory)
    for file in directory.glob('**/*.mp4'):
        if file.is_file():
            print(file)
            subbing = VideoSubbing(file)
            subbing.create_subs(pipe, replace=replace,
                                 multi_lang=multi_lang, replace_lang=replace_lang, cleanup=cleanup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("location", type=str)
    parser.add_argument("--input_mode", choices=['file', 'folder', 'rootdir'], default = 'file',
                        help='Use folder or rootdir to process all files, or all subfolders')
    parser.add_argument("--replace", action='store_true',
                        help='Overwrite existing subtitle files')
    parser.add_argument("--multi_lang", action='store_true',
                        help='To process multiple languages within the same file')
    parser.add_argument("--replace_lang", action='store_true',
                        help='Force script to redetect language, if relevent')
    parser.add_argument("--cleanup", action='store_true',
                        help='Remove auxillary files created during processing')


    args = parser.parse_args()

    location = Path(args.location)
    replace = args.replace
    multi_lang = args.multi_lang
    replace_lang = args.replace_lang
    cleanup = args.cleanup
    input_mode = args.input_mode

    print(replace)

    if input_mode == 'file':
        subtitle_file(location)
    elif input_mode == 'folder':
        subtitle_folder(location)
    elif input_mode == 'rootdir':
        subtitle_folder_all(location)
