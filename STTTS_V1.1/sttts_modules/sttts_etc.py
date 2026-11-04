from pynput import keyboard
import re


class TextFilter():

    def __init__(self, dict):
        # compile regular expressions
        self.regexes = {}
        for word, replacement in dict.items():
            self.regexes[replacement] = re.compile(word, re.I)

    def filter_text(self, text):
        # replace words
        for replacement, c_regex in self.regexes.items():
            text = c_regex.sub(replacement, text)
        return text


class HotkeyManager():

    def __init__(self, config, callback):
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(config['mute_key']),
            callback)
        self.listener = keyboard.Listener(
            on_press=self.for_canonical(hotkey.press),
            on_release=self.for_canonical(hotkey.release))

    def for_canonical(self, f):
        return lambda k: f(self.listener.canonical(k))

    def start_listening(self):
        self.listener.start()

    def stop_listening(self):
        self.listener.stop()


# TODO document
