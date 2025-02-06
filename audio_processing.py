from pathlib import Path
from pydub import AudioSegment

def extract_audio(video_path:Path):
    """Extracts audio from video located at given path, and saves it as a .wav. Returns a path to that wav file."""
    # Load the video file
    try:
        video_clip = AudioSegment.from_file(video_path)
    except IndexError as e:
        raise TypeError("Video file has no audio track.") from e

    # Force the audio to be single channel, and sets the frame rate to 16kHz since these are expected input data for whisper model.
    video_clip = video_clip.set_channels(1)
    video_clip = video_clip.set_frame_rate(16000)

    audio_path = video_path.with_suffix(".wav")
    # Export audio to file
    video_clip.export(audio_path, format='wav')

    return audio_path
