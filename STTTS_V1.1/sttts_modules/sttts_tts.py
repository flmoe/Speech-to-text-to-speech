import win32com.client as wincom
from pywintypes import com_error
import sttts_modules.sttts_etc as etc

class TTS():

    def __init__(self):
        self.spkr = wincom.Dispatch('SAPI.SpVoice')
        self.vcs = self.spkr.GetVoices()
        self.outs = self.spkr.GetAudioOutputs()
        self.filter = None
        self.text = ''
    
    def say(self, text):
        text = self.text + text  # TODO add space inbetween???
        if self.filter:
            text = self.filter.filter_text(text)
        try:
            self.spkr.Speak(text, 1)
            self.text = ''
        except com_error:
            # an error will occur if a previously
            # selected output becomes unavailable
            # continue and keep text
            self.text = text
    
    def init_filter(self, dict):
        self.filter = etc.TextFilter(dict)

    def set_voice(self, voice):
        # set voice
        self.spkr.Voice = self.vcs.Item(voice)

    def set_speed(self, speed):
        # set relative talking speed
        self.spkr.Rate = speed

    def set_volume(self, volume):
        # set volume
        self.spkr.Volume = volume

    def set_output(self, output):
        # set audio output
        self.spkr.AudioOutput = self.outs.Item(output)

    def list_voices(self):
        # list voices
        voice_names = ()
        for i in range(len(self.vcs)):
            vc_item = self.vcs.Item(i)
            vc_name = vc_item.GetAttribute('name')
            voice_names = *voice_names, vc_name
            if vc_item.Id == self.spkr.Voice.Id:
                current_voice = i
        return (voice_names, current_voice)

    def list_outputs(self):
        # list audio outputs
        self.outs = self.spkr.GetAudioOutputs()
        output_names = ()
        for i in range(len(self.outs)):
            out_item = self.outs.Item(i)
            out_name = out_item.GetDescription()
            output_names = *output_names, out_name
            if out_item.Id == self.spkr.AudioOutput.Id:
                current_output = i
        return (output_names, current_output)
