import os
import sys
import time
import pyaudio
import wave
import hashlib
import datetime
import requests
import subprocess
import configparser
import json
from periphery import GPIO
#from denoise import Denoiser
#from noiseProfiler import NoiseProfiler





class SpeechDetector:

    def __init__(self,pc_sevac,chan,rate,data_not_sent):

        # Microphone stream config.
        
        self.CHUNK = 1024  # CHUNKS of bytes to read each time from mic
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = chan
        self.RATE = rate
        self.MODELDIR = "/usr/bin/numeriseur/stm32/speech_data/"
        self.frames = []
        self.HTTP_Host=pc_sevac
        self.JSONFILEDATA=data_not_sent

        self.config = configparser.ConfigParser()
        self.config.read('/usr/bin/numeriseur/stm32/Config.ini')

    
    def find_usb_mic(self,name,audio):

        
        info = audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
                if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    if audio.get_device_info_by_host_api_device_index(0, i).get('name').__contains__(name):
                        return i
                   
        return False


    def record(self,stream):
        
        data = stream.read(self.CHUNK, exception_on_overflow = False)  
        return data
        
    def creat_wav_file(self,output,pyaudio,frames_data):
        
        p=pyaudio
        filename = output+"_"+(datetime.datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")
        out = os.path.join(self.config['Cab_Radio']['Data_folder'], filename)  
        wf = wave.open(out + '.wav', 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)  # TODO make this value a function parameter?
        wf.writeframes(b''.join(frames_data))
        wf.close() 

        return filename

    def write_to_json_log_file(self,old_file,file_to_send,code_error):

        config = configparser.SafeConfigParser()
        config.read('/usr/bin/numeriseur/stm32/Config.ini')

        data=int(config['Cab_Radio']['Nbres_not_send'])+1
        config.set('Cab_Radio', 'Nbres_not_send', str(data))
        size=int(config['Cab_Radio']['Nbres_not_send'])+os.stat(old_file).st_size
        config.set('Cab_Radio', 'Total_size_not_sent', str(size))
        
        with open('/usr/bin/numeriseur/stm32/Config.ini', "w+") as configfile:
                config.write(configfile)

        file_spl=file_to_send
        file_info=file_spl.split('_')


        data_dict = {
                'Code': file_info[1],
                'Date': file_info[2],
                'Nom ': file_to_send,
                'code_error' : code_error
            }
        with open(self.JSONFILEDATA, 'ab+') as f:
            f.seek(0,2)                                #Go to the end of file    
            if f.tell() == 0 :                         #Check if file is empty
                f.write(json.dumps([data_dict]).encode())  #If empty, write an array
            else :
                f.seek(-1,2)           
                f.truncate()                           #Remove the last character, open the array
                f.write(' , '.encode())                #Write the separator
                f.write(json.dumps(data_dict).encode())    #Dump the dictionary
                f.write(']'.encode())                  #Close the array


        return 0
   
    

    def decode_phrase2(self, raw_file,text_file):

        try:
            import speech_recognition as sr
            r=sr.Recognizer()
            Audio = sr.AudioFile(os.path.join(self.config['Cab_Radio']['Data_folder'], raw_file))
            with Audio as source:
                r.adjust_for_ambient_noise(source, duration=0.1)
                audio = r.record(source)
            
            value = r.recognize_sphinx(audio)

            
            filename=os.path.join(self.config['Cab_Radio']['Data_folder'], text_file) 
            with open(filename,"w") as f:
                f.write(value.encode('ascii', 'ignore').decode('ascii'))
             
            return text_file

        except AssertionError as error:
          print(error) 
       

    def send_data(self, file_to_send):

        old_file = os.path.join(self.config['Cab_Radio']['Data_folder'], file_to_send)
       
        
        url = self.HTTP_Host
        fin = open(old_file, 'rb')
        files = {'file': fin}
        retries = 5
        success = False
        succes_reponse_l=[200,201,204]
        code_error=0

        while not success and retries>0:
           
            try:
                r = requests.put(url, files=files)
                code_error=r.status_code
                if(r.status_code in succes_reponse_l):
                    os.remove(old_file)
                    success = True
                else:
                    retries= retries-1
                    
                    
            except Exception as e:
                retries= retries-1


        if(retries<=0 and not success):

            
            self.write_to_json_log_file(old_file,file_to_send,code_error)
            new_file = os.path.join(self.config['Cab_Radio']['Data_folder'], "nod_sent_"+file_to_send)
            os.rename(old_file,new_file)

        return 0

    def run(self,pyaudio,stream_audio):

        
        i=0
        record=False
        print("wait CB from Cab_Radio..........")
        gpio_in = GPIO(71, "in") #combiné
        gpio_out = GPIO(65, "out") #Led combiné

        
       

        while True:
            
            
            if(gpio_in.read()):
                
                gpio_out.write(True)
                (self.frames).append(self.record(stream_audio))
                
                if i==1:
                    record=True
                    self.filename="cabradio_{}".format(hashlib.md5(str(datetime.datetime.now()).encode('utf-8')).hexdigest()+"_"+ (datetime.datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"))
                    print("* recording...................")
                   
                i=i+1
                gpio_out.write(False)
                time.sleep(0.05)
                 #combine

            elif(record):
                gpio_out.write(False)
                print("* done recording........ok")

                audio_file=self.creat_wav_file(self.filename,pyaudio,self.frames)
                text_file=self.decode_phrase2(audio_file+'.wav',audio_file+ '.txt')

                self.send_data(audio_file+ '.wav')
                self.send_data(text_file)

                i=0
                record=False
                self.frames = []
                print("wait CB from Cab_Radio..........")
               
        gpio_in.close()
        gpio_out.close()






if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read('/usr/bin/numeriseur/stm32/Config.ini')
    
    HTTP_HOST = config['Cab_Radio']['HTTP_HOST']
    CHUNK = 1024  # CHUNKS of bytes to read each time from mic
    FORMAT = pyaudio.paInt16
    CHANNELS=int(config['Cab_Radio']['CHANNELS'])
    RATE=int(config['Cab_Radio']['RATE'])
    json_not_sent=config['Cab_Radio']['Data_not_sent_json']

    os.system("amixer -c STM32MP1DK cset name='PGA-ADC Mux Left' '3'")
    os.system("amixer -c STM32MP1DK cset name='Mic Boost Volume' '1','1'")

    if not os.path.exists("/tmp/cab_radio/"):
        os.makedirs("/tmp/cab_radio/")
    

    #devnull = os.open(os.devnull, os.O_WRONLY)
    #old_stderr = os.dup(2)
    #sys.stderr.flush()
    #os.dup2(devnull, 2)
    #os.close(devnull)
       
    sd = SpeechDetector(HTTP_HOST,CHANNELS,RATE,json_not_sent)
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, 
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index =sd.find_usb_mic("record_codec",p),
        frames_per_buffer=CHUNK)
    
    sd.run(p,stream)

    stream.stop_stream()
    stream.close()
    p.terminate()
