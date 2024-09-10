import os
import json
import logging
import tempfile

import numpy as np
import speech_recognition as sr

import torch

from pydub import AudioSegment
from transformers import pipeline
from django.core.files.uploadedfile import TemporaryUploadedFile

from .models import AudioGrammerCorrections, AudioTranscriptions


__base_path__ = os.getcwd()
# beam_settings =  TTSettings(num_beams=5, min_length=1, max_length=500)
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"
audio2text = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-small",
    chunk_length_s=30,
    device=device
)

# device = "cuda" if torch.cuda.is_available() else "cpu"
grammar = pipeline(
    "text2text-generation", 
    model="hafidikhsan/happy-transformer-t5-base-grammar-correction-ep-v1",
    device=device
)

spelling = pipeline("text2text-generation",model="oliverguhr/spelling-correction-english-base")

logger = logging.getLogger('django')

def save_transcription(transcription, video_obj):
    json_data = json.dumps(transcription)

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

    transcription_obj = AudioTranscriptions()
        
    transcription_obj.video_id = video_obj.id
    transcription_obj.transcription = temp_uploaded_file

    transcription_obj.save()


def split_audio(file_path, segment_length=60000):
    audio = AudioSegment.from_file(file_path)
    segments = [audio[i:i+segment_length] for i in range(0, len(audio), segment_length)]
    return segments

def recognize_audio_segment(audio):
    return audio2text(audio.copy(), batch_size=16, return_timestamps=True)["chunks"]

def convertText(video_obj):

    logger.info(f"Converting audio to text: {video_obj.audio.path}")

    try:
        transcription_obj = AudioTranscriptions.objects.filter(video_id=video_obj.id).latest("modified_at")
        with open(transcription_obj.transcription.path, "r") as reader:
            prediction_with_time = json.load(reader)["data"]

    except AudioTranscriptions.DoesNotExist:
        audio = AudioSegment.from_file(video_obj.audio.path).set_frame_rate(16000).set_channels(1)
        audio = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
        prediction_with_time = recognize_audio_segment(audio)
        
        save_transcription(transcription={"data": prediction_with_time}, video_obj=video_obj)

    new_sentence = ""
    new_sentences = []
    for sentence in prediction_with_time:
        if len(new_sentence) + len(sentence["text"]) < 512:
            new_sentence += sentence["text"]
        else:
            new_sentences.append(new_sentence)
            new_sentence = "" 
    
    return new_sentences

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
    
    correction = AudioGrammerCorrections()
    correction.video_id = video_obj.id
    correction.corrections = temp_uploaded_file

    correction.save()

def grammerchecker(speechText, video_obj=None, ppt=False):
    
    
    if ppt:
        results = []
        if isinstance(speechText, str):
            speechText = speechText.replace(":", "")
            speech_length = len(speechText.split(" ")) + speechText.count(" ")
            if not speech_length:  # Check if the text is empty or only contains whitespace
                results.append(speechText)  # Return the original text or handle it as needed
            elif speech_length == 1:
                result = spelling(speechText, max_length=speech_length)[0]["generated_text"]
                results.append(result)
            else:
                result = grammar(speechText, max_new_tokens=speech_length + 10)[0]["generated_text"] #, args=beam_settings)
                result = spelling(result, max_length=speech_length)[0]["generated_text"]
                results.append(result)
        else:
            for txt in speechText:
                txt = txt.replace(":", "")
                speech_length = len(txt.split(" ")) + txt.count(" ")
                if not speechText.strip():  # Check if the text is empty or only contains whitespace
                    results.append(speechText)  # Return the original text or handle it as needed
                elif len(speechText.split(" ")) == 1:
                    result = spelling(speechText, max_length=speech_length)[0]["generated_text"]
                    results.append(result)
                else:
                    result = grammar(txt, max_new_tokens=speech_length + 10)[0]["generated_text"] #, args=beam_settings)
                    result = spelling(result, max_length=speech_length)[0]["generated_text"]
                    results.append(result)

        return results[0]
    else:
        try:
            audio_grammar_obj = AudioGrammerCorrections.objects.filter(video_id=video_obj.id).latest("modified_at")
            with open(audio_grammar_obj.corrections.path, "r") as reader:
                context = json.load(reader)

        except AudioGrammerCorrections.DoesNotExist:
        
            if ppt:
                logger.info("Performing grammar corrections on PPT")
            else:
                logger.info("Performing grammar corrections")
            
            results = []
            if isinstance(speechText, str):
                speechText = speechText.replace(":", "")
                speech_length = len(speechText.split(" ")) + speechText.count(" ")
                if not speechText.strip():  # Check if the text is empty or only contains whitespace
                    results.append(speechText)  # Return the original text or handle it as needed
                elif len(speechText.split(" ")) == 1:
                    result = spelling(speechText, max_length=speech_length)[0]["generated_text"]
                    results.append(result)
                else:
                    result = grammar(speechText, max_new_tokens=speech_length + 10)[0]["generated_text"] #, args=beam_settings)
                    result = spelling(result, max_length=speech_length)[0]["generated_text"]
                    results.append(result)
            else:
                for txt in speechText:
                    txt = txt.replace(":", "")
                    speech_length = len(txt.split(" ")) + txt.count(" ")
                    if not txt.strip():  # Check if the text is empty or only contains whitespace
                        results.append(speechText)  # Return the original text or handle it as needed
                    elif len(txt.split(" ")) == 1:
                        result = spelling(txt, max_length=speech_length)[0]["generated_text"]
                        results.append(result)
                    else:
                        result = grammar(txt, max_new_tokens=speech_length + 10)[0]["generated_text"] #, args=beam_settings)
                        result = spelling(result, max_length=speech_length)[0]["generated_text"]
                        results.append(result)
            
            context = {
                'result': " ".join(results),
                'stt': " ".join(speechText)
            }
            
            save_results(context, video_obj)
            
            return context


if __name__ == "__main__":
    speechText = convertText()
    result = grammerchecker(speechText)
