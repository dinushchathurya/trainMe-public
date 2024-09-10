# import numpy as np
# import librosa
# import noisereduce as nr
# import tensorflow as tf
# import pyaudio
# import wave
# import os

# # Constants
# RATE = 24414
# CHUNK = 512
# CHANNELS = 1
# RECORD_SECONDS = 7.1
# FORMAT = pyaudio.paInt16
# WAVE_OUTPUT_FILE = "temp_output.wav"

# # Load the model
# saved_model_path = "users/models/model8723.json"
# saved_weights_path = "users/models/model8723_weights.h5"

# with open(saved_model_path, 'r') as json_file:
#     json_savedModel = json_file.read()
    
# model = tf.keras.models.model_from_json(json_savedModel)
# model.load_weights(saved_weights_path)

# model.compile(loss='categorical_crossentropy', 
#               optimizer='RMSProp', 
#               metrics=['categorical_accuracy'])

# def preprocess(file_path, frame_length=2048, hop_length=512):
#     y, sr = librosa.load(file_path, sr=RATE)
#     y = librosa.util.normalize(y)
#     y = nr.reduce_noise(y, sr=sr)
    
#     f1 = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length, center=True).T 
#     f2 = librosa.feature.zero_crossing_rate(y=y, frame_length=frame_length, hop_length=hop_length, center=True).T 
#     f3 = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length).T
#     X = np.concatenate((f1, f2, f3), axis=1)
    
#     return np.expand_dims(X, axis=0)

# def is_silent(data, threshold=100):
#     return np.max(np.abs(data)) < threshold

# emotions = {
#     0: 'neutral', 1: 'calm', 2: 'happy', 3: 'sad',
#     4: 'angry', 5: 'fearful', 6: 'disgust', 7: 'surprised'
# }


# def process_audio(input_file):
#     p = pyaudio.PyAudio()
#     wf = wave.open(input_file, 'rb')
    
#     stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                     channels=wf.getnchannels(),
#                     rate=wf.getframerate(),
#                     output=True)

#     total_predictions = []

#     while True:
#         data = wf.readframes(CHUNK)
#         if not data:
#             break

#         audio_chunk = np.frombuffer(data, dtype=np.int16)
        
#         if not is_silent(audio_chunk):
#             with wave.open(WAVE_OUTPUT_FILE, 'wb') as temp_wf:
#                 temp_wf.setnchannels(CHANNELS)
#                 temp_wf.setsampwidth(p.get_sample_size(FORMAT))
#                 temp_wf.setframerate(RATE)
#                 temp_wf.writeframes(data)
            
#             x = preprocess(WAVE_OUTPUT_FILE)
#             print(x.shape)
#             x = x.reshape(-1, 339, 15)
#             predictions = model.predict(x)[0]
#             total_predictions.append(predictions)
            
#             os.remove(WAVE_OUTPUT_FILE)
#         else:
#             if len(total_predictions) > 0:
#                 break

#         stream.write(data)

#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     wf.close()

#     average_predictions = np.mean(total_predictions, axis=0)

#     avg_emotion_probs = {}
#     print("Average emotion probabilities:")
#     for emotion, prob in zip(emotions.values(), average_predictions):
#         print(f"{emotion}: {prob:.4f}")
#         avg_emotion_probs[emotion] = round(prob, 4)

#     return avg_emotion_probs

# # Main execution
# if __name__ == "__main__":
#     input_file = "path/to/your/input/audio/file.wav"
#     process_audio(input_file)

import os
import json
import logging
import tempfile

import numpy as np

import torch

from collections import Counter

from pydub import AudioSegment
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification
from django.core.files.uploadedfile import TemporaryUploadedFile

from .models import AudioEmotions


logger = logging.getLogger('django')

# Path to the local directory containing the model files
local_directory = "users/models/audio_emotion/"
# local_directory = "ravdess_emotion_recognition_model/"
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"

# Load the processor and model from the local directory
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
model = Wav2Vec2ForSequenceClassification.from_pretrained(local_directory).to(device)

emotions = ['angry', 'calm', 'disgust', 'fearful', 'happy', 'neutral', 'sad', 'surprised']

def predict_emotion(audio_array, sampling_rate):
    inputs = feature_extractor(audio_array, sampling_rate=sampling_rate, return_tensors="pt", padding=True)
    
    input_values = inputs["input_values"].to(device)
    attention_mask = inputs["attention_mask"].to(device)
    
    with torch.no_grad():
        logits = model(input_values=input_values, attention_mask=attention_mask).logits
    
    predicted_ids = torch.argmax(logits, dim=-1)
    predicted_emotion = emotions[predicted_ids.item()]
    
    return predicted_emotion


def save_results(results, video_obj):
    json_data = json.dumps(results)

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

    emotions = AudioEmotions()

    emotions.video_id = video_obj.id
    emotions.expressions = temp_uploaded_file

    emotions.save()


def process_audio_file(video_obj):

    logger.info(f"Processing Audio file {video_obj.audio.path} for Emotions.")

    # Load the audio file
    audio = AudioSegment.from_file(video_obj.audio.path)
    
    # Ensure the audio is in the correct format (16kHz, mono)
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    # Convert to numpy array
    audio_array = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
    
    # Process in 1-minute chunks
    chunk_length = 3 * 16000  # 3 seconds at 16kHz

    _emotions = {}

    for i in range(0, len(audio_array), chunk_length):
        chunk = audio_array[i:i+chunk_length]
        
        if len(chunk) > chunk_length:
            chunk = chunk[:chunk_length]
        else:
            padding = np.zeros(chunk_length - len(chunk))
            chunk = np.concatenate([chunk, padding])
        
        emotion = predict_emotion(chunk, 16000)
        # print(f"Minute {i // chunk_length + 1}: {emotion}")
        _emotions[f"{int(i // chunk_length + 1)}"] = emotion

    c = Counter(_emotions.values())
    logger.info(c)
    total = sum(c.values())    
    percent = {emotion: round((count/total) * 100, 2) for emotion, count in c.items()}

    for emotion in emotions:
        if emotion not in percent:
            percent[emotion] = 0

    save_results(percent, video_obj)

    logger.info(f"Emotion Percentages: {percent}")
    return percent


if __name__ == "__main__":
    # Usage
    file_path = "media/audio/24/CAMERA.wav"
    print(process_audio_file(file_path))
