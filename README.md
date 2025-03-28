A small script that uses Whisper to automatically generate English subtitles, in .srt format, for video files. Currently runs on a number of video file formats, the exact list is available in constants.py.

Now launches a GUI where files and options can be selected.

Models currently supported are WhiperLargeV3 and WhiperLargeV3Turbo. The turbo model is strongly recommended on systems without cuda capability.

Auto-Detect single language will first attempt to predict the most common language appearing in the video, then will use that language to transcribe and translate everything. Auto-Detect multiple languages will simply process small chunks of the video based on what the model thinks it hears in each separate chunk. This is good for multilanguage sources, but may cause hallucinations if the model can't clearly identify each segment and will generally give worst results that detecting a single language when only one is present.
