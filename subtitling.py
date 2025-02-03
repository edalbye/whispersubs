from dataclasses import dataclass
from pathlib import Path

import torch
from transformers import pipeline
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

from audio_processing import extract_audio
from utils import determine_lang, write_subs
from constants import valid_video_file_types

@dataclass
class SubbingParameters:
    replace: bool = True
    multi_lang: bool = True
    replace_lang: bool = False
    preserve_intermediary_files: bool = False
    provide_lang: bool = False
    provided_lang: str = ""

class VideoSubbing:
    """
    Custom class for managing data involved in generating a subtitle track for a given video,
    assumed to be located in directory\video_name
    """
    def __init__(self, file, pipe, *, parameters=None):
        self.file = file
        

        if parameters is None:
            self.parameters = SubbingParameters()
        else:
            self.parameters = parameters
        
        self.pipe = pipe

        #Extract audio data from file
        self.audio_input = str(extract_audio((self.file)))

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

    def cleanup_wav(self):
        """
        Removes video_name.wav file 
        that is created during processing
        """
        try:
            self.file.with_suffix(".wav").unlink()
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

def subtitle_file(path: Path, pipe, parameters: SubbingParameters = None):
    """Produces subtitle file for a given video file"""
    if path.suffix.lower() in valid_video_file_types:
        subbing = VideoSubbing(
                file = path,
                pipe = pipe,
                parameters = parameters
            )
        if subbing.audio_input is str(None):
            return
        subbing.create_subs()
        if not parameters.preserve_intermediary_files:
            subbing.cleanup_wav()
    else:
        print("Warning: Input file format not recognized")

def subtitle_folder(path: Path, pipe, parameters: SubbingParameters = None):
    """Produces subtitle files for all video files in a folder"""
    for filetype in valid_video_file_types:
        allowed_filename = r"*"+filetype
        for file in path.glob(allowed_filename):
            if file.is_file():
                print(file)
                subtitle_file(file, pipe, parameters)

def subtitle_folder_all(path: Path, pipe, parameters: SubbingParameters = None):
    """Produces subtitle files for all video files in a folder, and all of it's subfolders"""
    subtitle_folder(path, pipe, parameters)
    folder_list = [f for f in path.glob('**/*') if f.is_dir()]
    for folder in folder_list:
        subtitle_folder(folder, pipe, parameters)

def create_subtitles(path, input_mode, include_subfolders, parameters = None, model_id = "openai/whisper-large-v3"):
    device = "cuda:0"  if torch.cuda.is_available() else "cpu"
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

    if input_mode == 'file':
        subtitle_file(path, pipe, parameters)
    elif input_mode == 'folder' and not include_subfolders:
        subtitle_folder(path, pipe, parameters)
    elif input_mode == 'folder':
        subtitle_folder_all(path, pipe, parameters)