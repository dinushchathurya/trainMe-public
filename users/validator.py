import os
import tempfile
import subprocess
from django.conf import settings

from django.core.exceptions import ValidationError

from moviepy.editor import VideoFileClip


def file_size(value):
    filesize=value.size
    if filesize>209715200:
        raise ValidationError("maximum size is 10 mb")
    
    
def convert_to_pdf(instance):
    # Get the full path of the uploaded PPTX file
    pptx_path = os.path.join(settings.MEDIA_ROOT, instance.ppt.path)
    
    # Create a PDF filename
    pdf_filename = os.path.basename(instance.ppt.path.replace(".pptx", ".pdf"))
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'pdf')
    
    if not os.path.exists(pdf_path):
        os.makedirs(pdf_path, exist_ok=True)
        
    if os.path.isfile(pptx_path) and not os.access(pptx_path, os.R_OK):
        print(f"Error: No Read permissions for {pptx_path}")
    
    # Convert PPTX to PDF using unoconv
    # subprocess.run(['unoconv', '-f', 'pdf', '-c', 'socket,host=libreoffice,port=8100;urp;', '-o', pdf_path, pptx_path], check=True, capture_output=True, text=True)
    try:
        result = subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", pdf_path,
            pptx_path
        ], check=True, capture_output=True, text=True)
        print(f"Conversion successful. Output: {result.stdout}")
        return os.path.join(pdf_path, pdf_filename)
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed. Error: {e.stderr}")
        return None
    

def video2audio(video_obj):
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