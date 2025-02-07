from pathlib import Path
#List of video file suffices that are compatible with ffmpeg
valid_video_file_types = {".mp4", ".mov", ".webm", ".flv", ".ogv", ".ogg", ".avi", ".m4v", ".m4a"}
supported_models = ["WhisperLargeV3", "WhisperLargeV3-Turbo"]
supported_languages = ["English", "Spanish"]
config_defaults = {
    'input_mode': "Single File",
    'filepath': str(Path.cwd()),
    'model_name': "WhisperLargeV3",
    'lang_selection': "Auto-Detect Single Language",
    'replace_lang': False,
    'selected_lang': "",
    'replace_subs': False,
}
