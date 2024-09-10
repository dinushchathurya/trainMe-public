from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import TemporaryUploadedFile

from .models import Video, PPTX

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ("caption","video")    

    def clean(self):
        cleaned_data = super().clean()
        video = cleaned_data.get("video")
        
        if video is None:
            raise forms.ValidationError("Video file is required.")
        
        return cleaned_data


class PPTXForm(forms.ModelForm):
    class Meta:
        model = PPTX
        fields = ("caption", "ppt")

    def clean(self):
        cleaned_data = super().clean()
        ppt = cleaned_data.get("ppt")
        
        if ppt is None:
            raise forms.ValidationError("PPT file is required.")
        
        return cleaned_data