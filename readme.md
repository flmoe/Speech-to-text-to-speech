# Speech-to-Text to Speech Converter

This application alters a person's voice by combining voice recognition and text-to-speech technology.

## Featues

* Speech-to-speech by speech-to-text and text-to-speech conversion
* Direct text input Text-to-speech function
* Adjustable audio input noise gate
* Selectable audio inputs and outputs
* Selectable TTS voice and talking speed
* Default setting configurable through config file
* Word filter: remove or replace certain words before speaking
* configurable mute keyboard shortcut

## Technology

* Voice recognition is handled locally through [Vosk](https://alphacephei.com/vosk/)
* TTS is handled by the built-in MS Windows TTS

## Installation

Due to the use of the Windows TTS system, this program is only supported on Windows.

This program requires a Python installation with version 3.10 or newer and the Tkinter GUI framework installed.

The required Python packages can be installed with `pip install -r requirements.txt`

The voice recognition model must be downloaded from the Vosk website. Adjust `model_path` in config.json to point to the model.
