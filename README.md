A small script that uses Whisper to automatically generate English subtitles, in .srt format, for video files. Currently only runs on .mp4 files.

The script expects to be passed a path to a .mp4 file to process, however can also run on all files in a folder via the argument --input_mode: folder will process all files in a given folder, and rootdir will process all files withing a given folder and all of it's subfolders.

By default it will run a first pass to determine the most common language detected throughout the file and then use that language for the translation. If there are multiple language present in the video file can be run with --multi_lang to autodetect language on each chunk seperately.
