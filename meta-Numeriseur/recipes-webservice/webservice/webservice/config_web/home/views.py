from django.shortcuts import render
from django.http import HttpResponse
from subprocess import Popen, PIPE, STDOUT
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse



import speech_recognition as sr
from periphery import GPIO


from django.shortcuts import redirect


import pyaudio
import wave
from django.conf import settings as conf_settings
import platform
import psutil
import configparser
import subprocess as sp
import json
import os
import sys


from django.views.decorators.csrf import csrf_exempt
# Create your views here.

     
def home(request):
    """ Exemple de page non valide au niveau HTML pour que l'exemple soit concis """
    try:
        config = configparser.ConfigParser()
        config.read('/usr/bin/numeriseur/stm32/Config.ini')
        #config.read('/home/sanogo/Bureau/numeriseur/stm32/Config.ini')

        fan = psutil.disk_usage("/")
        uname = platform.uname()

        #software==================
        
        osr=sp.check_output(['uname', '-mrs'])


        Version=str(uname.version).strip().replace('#', ' ')
        app_version=config['Commun']['Logiciel_version']

        #hardware=================

        Processor=uname.processor
        memory_Total=str(fan.total/(1024.0 **3)) +" GB"
        Machine =config['Commun']['Machine'] 
        #Autres===================

        audio_format=config['Commun']['AUDIO_FORMAT'] 
        server=config['Microphone_amb']['RTP_HOST']
        send_echec_nbres=config['Cab_Radio']['Nbres_not_send']
        total_size_not_sent=str(int(config['Cab_Radio']['Total_size_not_sent'])/(1024.0 **3))+" GB"
        


        list_not_sent=config['Cab_Radio']['Data_not_sent_json']

        with open(list_not_sent, 'r') as f:
            my_json_obj = json.load(f)
        
        
        Software={
            'OS': osr,
            'OS version' :Version,
            'App version' :app_version
        }
       
        Hardware={
             'Machine' : Machine, 
             'Processeur':Processor,
             'Memoire': memory_Total
             }

        Autres={

            'Audio format' : audio_format,
            'Adresse du server' : server,
            "Nombres d'envoie echoué" : send_echec_nbres,
            "Taille Totale d'envoie echoué" : total_size_not_sent
            }
            
       


        return render(request, 'home/home.html',{'Software': Software,'Hardware': Hardware, 'Autres' : Autres, 'array' :my_json_obj})

    except Exception as e:

        print(e)
        config = configparser.ConfigParser()
     
        fan = psutil.disk_usage("/")
        uname = platform.uname()
        #software==================
        osr=sp.check_output(['uname', '-mrs'])
        Version=str(uname.version).strip().replace('#', ' ')
        #hardware=================
        Processor=uname.processor
        memory_Total=str(fan.total/(1024.0 **3)) +" GB"
        #Autres===================

        

        
        Software={
            'OS': osr,
            'OS version' :Version,
        }
       
        Hardware={
             'Processeur':Processor,
             'Memoire': memory_Total
             }
       


        return render(request, 'home/home.html',{'Software': Software,'Hardware': Hardware})



def config(request):

    if request.is_ajax():

        CHANNELS = request.POST.get('CHANNELS', None) 
        AUDIO_FORMAT = request.POST.get('AUDIO_FORMAT', None)  
        HTTP_HOST = request.POST.get('HTTP_HOST', None)
        RTP_HOST = request.POST.get('RTP_HOST', None)  

       
        config = configparser.SafeConfigParser()
       
        config.read('/usr/bin/numeriseur/stm32/Config.ini')

        if CHANNELS or AUDIO_FORMAT or HTTP_HOST or RTP_HOST:

            if CHANNELS :

                config.set('Cab_Radio', 'CHANNELS', (CHANNELS))
                config.set('Microphone_amb', 'CHANNELS', (CHANNELS))
                
            if AUDIO_FORMAT :
                config.set('Commun', 'AUDIO_FORMAT', (AUDIO_FORMAT))
            if HTTP_HOST :
                config.set('Cab_Radio', 'HTTP_HOST', (HTTP_HOST))
            if RTP_HOST :
                config.set('Microphone_amb', 'RTP_HOST', (RTP_HOST))

            with open("/usr/bin/numeriseur/stm32/Config.ini", "w+") as configfile:
                config.write(configfile)

            response = {
                         'msg':'Paramètres modifiés avec succès !' # response message
            }
            return JsonResponse(response) # return response as JSON             

    return render(request, 'home/config.html')


def debug(request): 


   
    if request.is_ajax():
        
        command=request.POST.get('command', None)
        process = Popen(command.split(), stdout=PIPE, stderr=STDOUT)
        output = process.stdout.read()

        if output : #cheking if first_name and last_name have value
            response=output
        else :
            response=" "

        return HttpResponse(response) # return response as JSON
   
   
    return render(request, 'home/debug_mic.html')


def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('user_login'))

def cab_debug(request):
    return render(request, 'home/debug_cab_radio.html')

def mic_debug(request):
    return render(request, 'home/debug_mic.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request,user)
                return redirect(home)
            else:
                return HttpResponse("Your account was inactive.")
        else:
            return HttpResponse("Invalid login details given")
    else:
        return render(request, 'registration/login.html', {})



def audio_cab_record(request):

    if request.method == 'POST':
        command = request.POST.get('command')
        if command=="record_start":
            gpio_in = GPIO(71, "in") #combiné
            response=gpio_in.read()
            gpio_in.close()
            if response==True:
                return JsonResponse({"success":True}, status=200)
            else:
                return JsonResponse({"success":False}, status=200)


def audio_mic_record(request):
    
    if request.method == 'POST':
        command = request.POST.get('command')
        if command=="record_start":
            min_info=find_usb_mic("USB",index=True)
            if min_info !=False:
                return JsonResponse({"success":True}, status=200)
            else:
                
                return JsonResponse({"success":False}, status=200)
    
         

                
def record(request):

    if  request.is_ajax():
        command = request.POST.get('command')
        recognition=request.POST.get('recognition')
        if command=="recording":
            gpio_in = GPIO(71, "in") #combiné
            response=gpio_in.read()
            gpio_in.close()
            if response==True:
                min_info=find_usb_mic("record_codec",index=True)

                CHUNK = 1024
                FORMAT = pyaudio.paInt16
                CHANNELS = 2
                RATE = 44100
                RECORD_SECONDS = 21
                WAVE_OUTPUT_FILENAME =os.path.join(conf_settings.STATIC_ROOT, "upload/voice.wav") 

                devnull = os.open(os.devnull, os.O_WRONLY)
                old_stderr = os.dup(2)
                sys.stderr.flush()
                os.dup2(devnull, 2)
                os.close(devnull)


                p = pyaudio.PyAudio()

                stream = p.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            input_device_index = min_info,
                                            frames_per_buffer=CHUNK,output=False)
                frames = []

                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK, exception_on_overflow = False)
                    frames.append(data)
                stream.stop_stream()
                stream.close()
                p.terminate()

                wf = wave.open( WAVE_OUTPUT_FILENAME, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                if recognition=="true":
                    r=sr.Recognizer()
                    Audio = sr.AudioFile(WAVE_OUTPUT_FILENAME)
                    with Audio as source:
                        r.adjust_for_ambient_noise(source, duration=0.1)
                        audio = r.record(source)
                    
                    value = (r.recognize_sphinx(audio)).encode('ascii', 'ignore').decode('ascii')
                    return JsonResponse({"success":True,"data":value}, status=200)



                else:
                    return JsonResponse({"success":True}, status=200)

            else:
                return JsonResponse({"success":False}, status=200)

           

def install_mic(request):

    if request.is_ajax():
        if request.method == 'GET':
            min_info=find_usb_mic("USB")
            print(min_info)
            if min_info==False:
                print(min_info)
                return JsonResponse({"success":'False'}, status=500)
            else:
                response = min_info
                return JsonResponse(response)
        elif request.method == 'POST':

            CHANNELS = request.POST.get('CHANNELS', None) 
            Rate = request.POST.get('Rate', None)  
            config = configparser.SafeConfigParser()

            #config.read('/usr/bin/numeriseur/stm32/Config.ini')
            config.read('/home/sanogo/Bureau/numeriseur/stm32/Config.ini')

            if CHANNELS and Rate:

                config.set('Microphone_amb', 'channels', (CHANNELS))
                config.set('Microphone_amb', 'rate', (Rate))

                #with open("/usr/bin/numeriseur/stm32/Config.ini", "w+") as configfile:
                with open("/home/sanogo/Bureau/numeriseur/stm32/Config.ini", "w+") as configfile:
                    config.write(configfile)

                response = {
                             'msg':'microphone installé avec succès !' 
                }
                return JsonResponse(response)        

    return render(request, 'home/install_mic.html', {})

            
def mic_record(request):

    if  request.is_ajax():
        command = request.POST.get('command')
        if command=="recording":
            min_info=find_usb_mic("USB",index=True)
            print(min_info!=False)
            if min_info!=False:
                print(min_info)
                
                CHUNK = 1024
                FORMAT = pyaudio.paInt16
                CHANNELS = 1
                RATE = 44100
                RECORD_SECONDS = 21
                WAVE_OUTPUT_FILENAME =os.path.join(conf_settings.STATIC_ROOT, "upload/voice.wav") 
               
                p = pyaudio.PyAudio()

                stream = p.open(format=FORMAT,channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            input_device_index = min_info,
                                            frames_per_buffer=CHUNK,output=False)
                frames = []

                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK, exception_on_overflow = False)
                    frames.append(data)
                
                print(WAVE_OUTPUT_FILENAME)
                stream.stop_stream()
                stream.close()
                p.terminate()

                print(WAVE_OUTPUT_FILENAME)
                wf = wave.open( WAVE_OUTPUT_FILENAME, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                print("fini")
                
                return JsonResponse({"success":True}, status=200)

            else:
                return JsonResponse({"success":False}, status=200)
    return render(request, 'home/debug_mic.html')

  

def find_usb_mic(name,index=False):

    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    audio = pyaudio.PyAudio()

    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
            if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                if audio.get_device_info_by_host_api_device_index(0, i).get('name').__contains__(name):
                    if index!=False:
                        audio.terminate()
                        return i
                    else :
                        audio.terminate()
                        return audio.get_device_info_by_host_api_device_index(0, i)
    audio.terminate()
    return False
