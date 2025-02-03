import argparse
from pathlib import Path

from subtitling import create_subtitles, SubbingParameters
from utils import find_model

def run_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("location", type=str)
    parser.add_argument("--input_mode", choices=['file', 'folder', 'rootdir'], default='file',
                        help='Use folder or rootdir to process all files, or all subfolders')
    parser.add_argument("--include_subfolders", action='store_true',
                        help='Whether to include files in all subfolders, when running over a folder.')
    parser.add_argument("--replace", action='store_true',
                        help='Overwrite existing subtitle files')
    parser.add_argument("--multi_lang", action='store_true',
                        help='To process multiple languages within the same file')
    parser.add_argument("--replace_lang", action='store_true',
                        help='Force script to redetect language, if relevant')
    parser.add_argument("--preserve_intermediary_files", action='store_true',
                        help='Remove auxiliary files created during processing')

    args = parser.parse_args()

    location = Path(args.location)

    input_mode = args.input_mode

    include_subfolders = args.include_subfolders

    parameters = SubbingParameters(replace=args.replace, multi_lang=args.multi_lang, 
                                   replace_lang=args.replace_lang, 
                                   preserve_intermediary_files=args.preserve_intermediary_files)

    model_id = find_model(args.model_id) if hasattr(args, 'model_id') else "openai/whisper-large-v3"
    create_subtitles(path=location, input_mode=input_mode, include_subfolders = include_subfolders, parameters=parameters)

if __name__ == "__main__":
    run_command_line()