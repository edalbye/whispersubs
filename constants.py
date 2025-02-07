from pathlib import Path
#List of video file suffices that are compatible with ffmpeg
valid_video_file_types = {".mp4", ".mov", ".webm", ".flv", ".ogv", ".ogg", ".avi", ".m4v", ".m4a"}
supported_models = ["WhisperLargeV3", "WhisperLargeV3-Turbo"]
supported_languages = ["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Marathi", "Maori", "Nepali", "Norwegian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili", "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh"]
config_defaults = {
    'input_mode': "Single File",
    'filepath': str(Path.cwd()),
    'model_name': "WhisperLargeV3",
    'lang_selection': "Auto-Detect Single Language",
    'replace_lang': False,
    'selected_lang': "",
    'replace_subs': False,
}
