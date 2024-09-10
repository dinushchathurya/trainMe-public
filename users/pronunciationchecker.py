import os
import json
import tempfile

import torch

import numpy as np

from pydub import AudioSegment
from collections import Counter
from django.core.files.uploadedfile import TemporaryUploadedFile
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor, Wav2Vec2FeatureExtractor, pipeline

from .models import AudioTranscriptions, AudioPronounciationQuality

# Load the model and processor
model_name = "hafidikhsan/Wav2vec2-large-robust-Pronounciation-Evaluation"
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
processor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)

# Use a pipeline as a high-level helper
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"
pipe = pipeline(
    "audio-classification", 
    model=model,
    feature_extractor=processor,
    chunk_length_s=30,
    device=device
)

id2label = {
    0: "Proficient",
    1: "Advanced",
    2: "Intermediate",
    3: "Beginer"
  }

def create_temp_file(json_data):
    # Create a temporary file and write the JSON data to it
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        temp_file.write(json_data.encode('utf-8'))
        temp_file.flush()
        temp_file_name = temp_file.name

    # Create an instance of TemporaryUploadedFile
    temp_uploaded_file = TemporaryUploadedFile(
        name=os.path.basename(temp_file_name),  # Extract the file name
        content_type='application/json',
        size=len(json_data),
        charset='utf-8'
    )

    # Open the temporary file and assign it to the TemporaryUploadedFile instance
    with open(temp_file_name, 'rb') as f:
        temp_uploaded_file.file = f
    
    return temp_uploaded_file
        

def save_results(qualities, quality_with_timestamp, video_obj):
    try:
        quality_obj = AudioPronounciationQuality.objects.filter(video_id=video_obj.id).latest("modified_at")
    except AudioPronounciationQuality.DoesNotExist:        

        quality_obj = AudioPronounciationQuality()
        
    quality_obj.video_id = video_obj.id
    quality_obj.qualities = create_temp_file(json.dumps(qualities))
    quality_obj.quality_with_timestamp = create_temp_file(json.dumps(quality_with_timestamp))

    quality_obj.save()
    

def get_frames_from_timestamp(audio, start_timestamp_ms, stop_timestamp_ms):
    start_timestamp_ms = start_timestamp_ms * 1000
    stop_timestamp_ms = stop_timestamp_ms * 1000
    
    # Ensure the start timestamp is within the audio duration
    if start_timestamp_ms >= len(audio):
        raise ValueError("Start timestamp is beyond the audio duration")

    # Slice the audio from the start timestamp
    return audio[start_timestamp_ms:stop_timestamp_ms]

def check_pronounciation_quality(video_obj):
    audio_input = AudioSegment.from_file(video_obj.audio.path)

    audio_input = audio_input.set_frame_rate(16000).set_channels(1)

    transcription_path = AudioTranscriptions.objects.filter(video_id=video_obj.id).latest("transcription").transcription.path

    with open(transcription_path, "r") as reader:
        timestamp_data = json.load(reader)["data"]

    labels = []
    qualities = []
    for data in timestamp_data:
        start_timestamp, stop_timestamp = data["timestamp"]
        if stop_timestamp is None:
            stop_timestamp = len(audio_input) / 1000
            
        # start_timestamp_ms = start_timestamp_ms * 1000
        # stop_timestamp_ms = stop_timestamp_ms * 1000
        # frames = audio_input[start_timestamp_ms:].generate_frames_as_segments(frame_duration_ms)

        # for segment, timestamp in get_frames_from_timestamp(audio_input, start_timestamp_ms, frame_duration_ms):
        segment = get_frames_from_timestamp(audio_input, start_timestamp, stop_timestamp)
        segment = np.array(segment.get_array_of_samples()).astype(np.float32) / 32768.0
        inputs = processor(segment, sampling_rate=16000, return_tensors="pt", padding=True)

        with torch.no_grad():
            logits = model(**inputs).logits

        predicted_class = torch.argmax(logits, dim=-1).item()

        qualities.append({
                "quality": id2label[predicted_class],
                "timestamp": [start_timestamp, stop_timestamp]
            }
        )
        labels.append(id2label[predicted_class])

    c = Counter(labels)
    total = sum(c.values())
    percent = {key: round(value / total * 100, 2) for key, value in c.items()}
    for key in id2label.values():
        if key not in percent.keys():
            percent[key] = 0
            
    save_results(percent, qualities, video_obj)
    
    return percent