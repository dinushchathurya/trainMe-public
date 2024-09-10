import os
import io
import tempfile

from .models import Video
from moviepy.editor import VideoFileClip
from django.core.files.uploadedfile import TemporaryUploadedFile

__base_path__ = os.getcwd()

def video2audio(video_obj: Video):
    # Load the video file
    video_file_path = video_obj.video.path
    video_clip = VideoFileClip(video_file_path)

    file_name = os.path.basename(video_file_path).split(".")
    if len(file_name) > 2:
        file_name = ".".join(file_name[:-1])
    else:
        file_name = file_name[0]

    # Extract the audio from the video
    audio_clip = video_clip.audio

    # Create a temporary file to store the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_path = temp_audio_file.name

    # Write the audio to a bytes buffer
    audio_clip.write_audiofile(temp_audio_path, codec='pcm_s16le')
    
    return temp_audio_path

    # # Read the audio back as bytes
    # with open(temp_audio_path, 'rb') as f:
    #     audio_bytes = f.read()

    # # Get the audio as bytes
    # # audio_bytes = audio_buffer.read()
    # temp_file = TemporaryUploadedFile(
    #     name=file_name + ".wav",
    #     content_type='text/plain',  # Adjust the content type as needed
    #     size=len(audio_bytes),
    #     charset='utf-8'
    # )

    # temp_file.write(audio_bytes)
    # temp_file.seek(0)
    # video_obj.audio = temp_file

    # video_obj.save()

    # # Clean up the temporary file
    # if os.path.exists(temp_audio_path):
    #     os.remove(temp_audio_path)

    # # Close the clips
    # audio_clip.close()
    # video_clip.close()