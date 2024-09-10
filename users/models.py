import os
import uuid

from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile

from names_generator import generate_name

from .validator import file_size, convert_to_pdf, video2audio

# Create your models here.
class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caption = models.CharField(max_length=100, default=generate_name)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video = models.FileField(upload_to="video/%y",validators=[file_size])
    audio = models.FileField(upload_to="audio/%y",validators=[file_size])
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.video and not self.audio:
            # Convert PPTX to PDF
            audio_path = video2audio(self)
            
            # Save the PDF file
            with open(audio_path, 'rb') as pdf_file:
                self.audio.save(os.path.basename(audio_path), ContentFile(pdf_file.read()))

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
    
    def __str__(self) -> str:
        return f"{self.caption}: {self.video.name}"

    
class PPTX(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    caption = models.CharField(max_length=100, default=generate_name)
    ppt = models.FileField(upload_to="ppt/%y",validators=[file_size])
    pdf = models.FileField(upload_to="pdf/%y", blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.ppt and not self.pdf:
            # Convert PPTX to PDF
            pdf_path = convert_to_pdf(self)
            
            # Save the PDF file
            with open(pdf_path, 'rb') as pdf_file:
                self.pdf.save(os.path.basename(pdf_path), ContentFile(pdf_file.read()))
        
    def to_dict(self):
        fields = {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
    
    def __str__(self) -> str:
        return f"{self.caption}: {self.ppt.name}"
    

class FacialExpressions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video_id = models.UUIDField(primary_key=False, editable=False, null=True)
    expressions = models.FileField(upload_to="video_emotions/%y", validators=[file_size])
    max_expression = models.CharField(max_length=10, name="max_expression")

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
    
    def __str__(self) -> str:
        return f"{self.id}"
    
class AudioTranscriptions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video_id = models.UUIDField(primary_key=False, editable=False, null=True)
    transcription = models.FileField(upload_to="transcriptions/%y", validators=[file_size])

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }

    def __str__(self) -> str:
        return f"{self.id}"

class AudioEmotions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video_id = models.UUIDField(primary_key=False, editable=False, null=True)
    expressions = models.FileField(upload_to="audio_emotions/%y", validators=[file_size])

    def to_dict(self):
        return {
            'field1': self.field1,
            'field2': self.field2,
            # add other fields
        }

    def __str__(self) -> str:
        return f"{self.id}"
    

class AudioGrammerCorrections(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video_id = models.UUIDField(primary_key=False, editable=False)
    corrections = models.FileField(upload_to="corrections/%y", validators=[file_size])

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }

    def __str__(self) -> str:
        return self.id
    
class AudioPronounciationQuality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    video_id = models.UUIDField(primary_key=False, editable=False, null=True)
    qualities = models.FileField(upload_to="pronounciations/%y", validators=[file_size])
    quality_with_timestamp = models.FileField(upload_to="pronounciations/%y", validators=[file_size])

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
    
    def __str__(self) -> str:
        return f"{self.id}"
    
class GrammerCorrectionsPPTX(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    pptx_id = models.UUIDField(primary_key=False, editable=False)
    corrected = models.FileField(upload_to="corrected_ppt/%y", validators=[file_size])

    def to_dict(self):
        return {
            field.name: field.value_from_object(self) for field in self._meta.fields
        }
    
    def __str__(self) -> str:
        return self.id