import sys
from setuptools import setup
from Cython.Build import cythonize


setup(
    name = "microphone",
    version = "0.1",
    packages=["utils"],
    author="Sanogo Mohamadou",
    author_email = "sanogomohamad9@gmail.com",
    license = "MIT",
    keywords= "microphone",
    ext_modules=cythonize(["utils/Audio_stream.pyx","utils/directives.pyx","utils/rtsp_packet.pyx","utils/rtp_packet.pyx","utils/message.pyx","utils/result_codes.pyx" ,"utils/Server.pyx"]),
)



