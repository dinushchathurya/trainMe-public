import time
import json
import logging

from django.core import serializers
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import TemporaryUploadedFile

from . import myprosody
from . import grammerchecker
from . import grammercorrectionppt
from . import emotiondetectionvideo
from . import emotiondetectionaudio
from . import pronunciationchecker

from .models import Video, PPTX, AudioGrammerCorrections, AudioEmotions, FacialExpressions, AudioPronounciationQuality, GrammerCorrectionsPPTX
from .forms import UserRegisterForm
from .video2audio import video2audio
from .forms import VideoForm, PPTXForm

logger = logging.getLogger('django')


def test(request, data):
    
    print(data)
    p="publicspeech" 
    c="trainme/users/myprosody" 
    var2= myprosody.myspgend(p,c)
    var1= myprosody.myprosody(p,c)
    context= {
        'var1': var1,
        'var2': var2
    }
    
    time.sleep(10)
    
    return JsonResponse(context)
    
    # return render(request, 'users/test.html',context)

def test_async(request):
    
    context = {
        "data": request.POST,
    }
    
    return render(request, 'users/loading.html', context)

def home(request):
    if request.method == "POST":
        video_form = VideoForm(data=request.POST,files=request.FILES)
        ppt_form = PPTXForm(data=request.POST, files=request.FILES)
        if video_form.is_valid():
            video_form.save()
            messages.success(request, f'Your video was successfully uploaded')
            # video2audio(video)
            return JsonResponse({
                'success': True,
                'redirect_url': request.build_absolute_uri(reverse('feedback'))
            })
        elif ppt_form.is_valid():
            ppt_form.save()
            messages.success(request, f'Your presentation was successfully uploaded')
            json_res = JsonResponse({
                'success': True,
                'redirect_url': request.build_absolute_uri(reverse('slidecheckerdashboard'))
            })
            return json_res
        else:
            return JsonResponse({'success': False})
    else:
        video_form=VideoForm()
        ppt_form = PPTXForm()
    return render(request, 'users/home.html',{"video_form": video_form, "ppt_form": ppt_form})

def contactus(request):
    return render(request, 'users/contactus.html')

def aboutus(request):
    return render(request, 'users/aboutus.html')

def pronuciation(request):

    if request.method == "POST":
        try:
            latest_video = Video.objects.latest("modified_at")
            context = {
                "grammar": None,
                "pronounciations": None
            }
            try:
                grammar = AudioGrammerCorrections.objects.filter(video_id=latest_video.id).latest("modified_at")
                
                with open(grammar.corrections.path, "r") as reader:
                    context['grammar'] = json.load(reader)

            except AudioGrammerCorrections.DoesNotExist:
                logger.info("Grammer Corrections data does not exist")
                speechText = grammerchecker.convertText(latest_video)
                context['grammar'] = grammerchecker.grammerchecker(speechText, latest_video)
            except Exception as ex:
                logger.error(ex, exc_info=True)
                
            try:
                pronounciations = AudioPronounciationQuality.objects.filter(video_id=latest_video.id).latest("modified_at")
                
                with open(pronounciations.qualities.path, "r") as reader:
                    context['pronounciations'] = json.load(reader)

            except AudioPronounciationQuality.DoesNotExist:
                logger.info("Pronountiation Evaluation data does not exist")
                quality = pronunciationchecker.check_pronounciation_quality(latest_video)
                context['pronounciations'] = quality
            except Exception as ex:
                logger.error(ex, exc_info=True)
                
            context["success"] = True
            return JsonResponse(context)

        except Video.DoesNotExist:
            logger.warn("Video does not exist")
            return JsonResponse({
                "success": False
            })
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return JsonResponse({
                "success": False
            })
        
    elif request.method == "GET":
        return render(request, 'users/pronuciation.html')
        
    else:
        return redirect('feedback')
    

def warningemotionsaudio(request):
    return render(request, 'users/unusualemotionswarning.html')  

def slidecheckerdashboard(request):
    return render(request, 'users/slidecheckerdashboard.html') 

def colorcubechecker(request):
    return render(request, 'users/colourcube.html')  

def grammercheckerslides(request):
    if request.method == "POST":
        try:
            latest_ppt = PPTX.objects.latest("modified_at")
            checked = grammercorrectionppt.check_grammer_pptx(latest_ppt)
            checked["success"] = True
            return JsonResponse(checked)
        except PPTX.DoesNotExist:
            logger.warn("PPT does not exist")
            return JsonResponse({
                "success": False
            })
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return JsonResponse({
                "success": False
            })

    elif request.method == "GET":
        return render(request, 'users/grammerchecker.html')
        
    else:
        return redirect('slidecheckerdashboard')    

def feedback(request):
    try:
        latest_video=Video.objects.latest("modified_at") #.all()
        return render(request, 'users/feedback.html') 
    except Video.DoesNotExist:
        logger.warn("Video does not exist")
    except Exception as ex:
        logger.error(ex, exc_info=True)
    return redirect('home')

def emotionaudio(request):
    if request.method == "POST":
        try:
            latest_video = Video.objects.latest("modified_at")

            try:
                emotions_obj = AudioEmotions.objects.filter(video_id=latest_video.id).latest("modified_at")
                with open(emotions_obj.expressions.path, "r") as reader:
                    audio_emotions = json.load(reader)
                
                # return render(request, 'users/emotionaudio.html',{"video":latest_video, "emotions": audio_emotions})
            
            except AudioEmotions.DoesNotExist as ex:

                logger.error(ex, exc_info=True)

                audio_emotions = emotiondetectionaudio.process_audio_file(latest_video)

                # return render(request, 'users/emotionaudio.html',{"video":latest_video, "emotions": audio_emotions})
        
            except Exception as ex:
                logger.error(ex, exc_info=True)
                latest_video = None
                audio_emotions = {}

            return JsonResponse({
                "success": True,
                "data": {
                    "video": {
                        "caption": latest_video.caption,
                        "video": {
                            "path": latest_video.video.path,
                            "url": latest_video.video.url
                        }
                    },
                    "emotions": audio_emotions
                }
            })
        
        except Video.DoesNotExist:
            logger.warn("Video does not exist")
            return JsonResponse({
                "success": False
            })
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return JsonResponse({
                "success": False
            })

    elif request.method == "GET":
        return render(request, 'users/emotionaudio.html')
        
    else:
        return redirect('feedback')

def emotionvideo(request):
    if request.method == "POST":
        try:
            latest_video=Video.objects.latest("modified_at")
            try:
                emotions = FacialExpressions.objects.filter(video_id=latest_video.id).latest("modified_at")
                context= {
                    'maxemotion': emotions.max_expression
                }

                with open(emotions.expressions.path, "r") as reader:
                    context['predictions'] = json.load(reader)

                # return render(request, 'users/emotionvideo.html', context)
                
            except FacialExpressions.DoesNotExist:
                context = emotiondetectionvideo.detect_emotions(latest_video)

                # return render(request, 'users/emotionvideo.html', context)

            return JsonResponse({
                "success": True,
                "data": context
            })

        except Video.DoesNotExist:
            logger.warn("Video does not exist")
            return redirect('feedback')
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return redirect('feedback')
    elif request.method == "GET":
        # try:
        #     latest_video=Video.objects.latest("modified_at")
        #     try:
        #         emotions = FacialExpressions.objects.filter(video_id=latest_video.id).latest("modified_at")
        #         context= {
        #             'maxemotion': emotions.max_expression
        #         }

        #         with open(emotions.expressions.path, "r") as reader:
        #             context['predictions'] = json.load(reader)

        #         return render(request, 'users/emotionvideo.html', context)
                
        #     except FacialExpressions.DoesNotExist:
        #         context = emotiondetectionvideo.detect_emotions(latest_video)

        #         return render(request, 'users/emotionvideo.html', context)

        # except Video.DoesNotExist:
        #     logger.warn("Video does not exist")
        #     return redirect('feedback')
        # except Exception as ex:
        #     logger.error(ex, exc_info=True)
        #     return redirect('feedback')
        return render(request, 'users/emotionvideo.html')
        
    else:
        return redirect('feedback')


def emotionaudioprosody(request):
    latest_video=Video.objects.latest("modified_at")
    p=latest_video.audio.path
    c="trainme/users/myprosody" 
    myspsyl= myprosody.myspsyl(p,c)
    mysppaus= myprosody.mysppaus(p,c)
    myspsr= myprosody.myspsr(p,c)
    myspatc= myprosody.myspatc(p,c)
    myspst= myprosody.myspst(p,c)
    myspod= myprosody.myspod(p,c)
    myspbala= myprosody.myspbala(p,c)
    myspf0mean= myprosody.myspf0mean(p,c)
    myspf0sd= myprosody.myspf0sd(p,c)
    myspf0med= myprosody.myspf0med(p,c)
    myspf0min= myprosody.myspf0min(p,c)
    myspf0max= myprosody.myspf0max(p,c)
    myspf0q25= myprosody.myspf0q25(p,c)
    myspf0q75= myprosody.myspf0q75(p,c)
    myspgend= myprosody.myspgend(p,c)
    mysppron= myprosody.mysppron(p,c)
    prosody= myprosody.myprosody(p,c)
    
    context= {
        'myspsyl': myspsyl,
        'mysppaus': mysppaus,
        'myspsr': myspsr,
        'myspatc': myspatc,
        'myspst': myspst,
        'myspod': myspod,
        'myspbala': myspbala,
        'myspf0mean': myspf0mean,
        'myspf0sd': myspf0sd,
        'myspf0med': myspf0med,
        'myspf0min': myspf0min,
        'myspf0max': myspf0max,
        'myspf0q25': myspf0q25,
        'myspf0q75': myspf0q75,
        'myspgend': myspgend,
        'mysppron': mysppron,
        'prosody': prosody
    }
    return render(request, 'users/prosody.html',context)  

def history(request):
    all_videos = list(Video.objects.all())
    ppts = list(PPTX.objects.all())
    return render(request, 'users/history.html', {"videos": all_videos, "ppts": ppts})

def compare_videos(request):
    video_ids = request.GET.getlist('video_id')
    # Fetch the videos based on the IDs and pass them to the template
    videos = Video.objects.filter(id__in=video_ids)
    facial_expressions = FacialExpressions.objects.filter(video_id=videos[0].id)[0],
    if isinstance(facial_expressions, (tuple, list)):
        facial_expressions = facial_expressions[0]
    audio_emotion = AudioEmotions.objects.filter(video_id=videos[0].id),
    if isinstance(audio_emotion, (tuple, list)):
        audio_emotion = audio_emotion[0]
    pronounciation = AudioPronounciationQuality.objects.filter(video_id=videos[0].id)[0],
    if isinstance(pronounciation, (tuple, list)):
        pronounciation = pronounciation[0]
    grammar = AudioGrammerCorrections.objects.filter(video_id=videos[0].id)[0]
    if isinstance(grammar, (tuple, list)):
        grammar = grammar[0]

    with open(facial_expressions.expressions.path, "r") as reader:
        facial_expressions = json.load(reader)

    with open(audio_emotion.expressions.path, "r") as reader:
        audio_emotion = json.load(reader)

    with open(pronounciation.qualities.path, "r") as reader:
        pronounciation = json.load(reader)

    with open(grammar.corrections.path, "r") as reader:
        grammar = json.load(reader)
    
    column_1 = {
        "video": videos[0].caption,
        "facial_expressions": facial_expressions,
        "audio_emotion": audio_emotion,
        "pronounciation": pronounciation,
        "grammar": grammar
    }

    facial_expressions = FacialExpressions.objects.filter(video_id=videos[1].id)[0],
    if isinstance(facial_expressions, (tuple, list)):
        facial_expressions = facial_expressions[0]
    audio_emotion = AudioEmotions.objects.filter(video_id=videos[1].id)[0],
    if isinstance(audio_emotion, (tuple, list)):
        audio_emotion = audio_emotion[0]
    pronounciation = AudioPronounciationQuality.objects.filter(video_id=videos[1].id)[0],
    if isinstance(pronounciation, (tuple, list)):
        pronounciation = pronounciation[0]
    grammar = AudioGrammerCorrections.objects.filter(video_id=videos[1].id)[0]
    if isinstance(grammar, (tuple, list)):
        grammar = grammar[0]

    with open(facial_expressions.expressions.path, "r") as reader:
        facial_expressions = json.load(reader)

    with open(audio_emotion.expressions.path, "r") as reader:
        audio_emotion = json.load(reader)

    with open(pronounciation.qualities.path, "r") as reader:
        pronounciation = json.load(reader)

    with open(grammar.corrections.path, "r") as reader:
        grammar = json.load(reader)
    
    column_2 = {
        "video": videos[1].caption,
        "facial_expressions": facial_expressions,
        "audio_emotion": audio_emotion,
        "pronounciation": pronounciation,
        "grammar": grammar
    }
    
    return render(request, 'users/compare.html', {"data": json.dumps({"column_1": column_1, "column_2": column_2})})

def compare_ppts(request):
    ppt_ids = request.GET.getlist('ppt_id')
    # Fetch the ppts based on the IDs and pass them to the template
    ppts = PPTX.objects.filter(id__in=ppt_ids)

    grammar_1 = GrammerCorrectionsPPTX.objects.filter(pptx_id=ppts[0].id)[0]

    with open(grammar_1.corrected.path, "r") as reader:
        grammar_1 = json.load(reader)["corrected"]

    column_1 = {
        "pptx": ppts[0].caption,
        "grammar": grammar_1
    }

    grammar_2 = GrammerCorrectionsPPTX.objects.filter(pptx_id=ppts[1].id)[0]

    with open(grammar_2.corrected.path, "r") as reader:
        grammar_2 = json.load(reader)["corrected"]

    column_2 = {
        "pptx": ppts[1].caption,
        "grammar": grammar_2
    }
    
    return render(request, 'users/compare.html', {"data": json.dumps({"column_1": column_1, "column_2": column_2})})

def overallfeedback(request):
    return render(request, 'users/overallfeedback.html')                 

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hi {username}, your account was created successfully')
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


@login_required()
def profile(request):
    return render(request, 'users/profile.html') 

