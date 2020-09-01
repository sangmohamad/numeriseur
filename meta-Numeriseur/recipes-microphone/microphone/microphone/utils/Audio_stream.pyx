import pyaudio




class AudioStream:

    FRAME_HEADER_LENGTH = 5
    DEFAULT_FPS = 24

    def __init__(self):


        self.rate = 44100
        self.frames_per_buffer = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.device=int(self.mic_hard())
        self._stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      input_device_index=self.device,
                                      frames_per_buffer = self.frames_per_buffer)
        self.audio_frames = []

        self.current_frame_number = -1

    def mic_hard(self):

        
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        device=0
        for i in range(0, numdevices):
            if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                if "USB" in (self.audio.get_device_info_by_host_api_device_index(0, i).get('name')):
                    device=i
                    continue
        return device
    


    def close(self):
        self._stream.stop_stream()
        self._stream.close()
        self.audio.terminate()

    def get_next_frame(self) -> bytes:
       
        frame = self._stream.read(self.frames_per_buffer, exception_on_overflow = False)
        self.current_frame_number += 1
        return bytes(frame)
