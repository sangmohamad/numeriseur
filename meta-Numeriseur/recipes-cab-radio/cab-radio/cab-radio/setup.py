import sys
from setuptools import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


setup(
    name = "cab-radio",
    version = "0.1",
    packages=["utils"],
    author="Sanogo Mohamadou",
    author_email = "sanogomohamad9@gmail.com",
    license = "MIT",
    keywords= "microphone",
    ext_modules=[Extension("speech_recognition",["utils/speech_recognition.pyx"])],
    cmdclass={
            'build_ext': build_ext,
        },
)



