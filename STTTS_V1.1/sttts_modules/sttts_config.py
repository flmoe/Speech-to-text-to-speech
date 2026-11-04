import os
import json
from tkinter import messagebox
from textwrap import dedent

# default config
DEFAULTS_JSON = '''{"model_path": "model",
                  "voice": "Zira",
                  "volume": 100,
                  "speed": 0,
                  "threshold": 0.1,
                  "audio_input": "",
                  "audio_output": "",
                  "replace": {},
                  "mute_key": "<ctrl>+m"}'''

config_path = 'config.json'

params = {"model_path", "voice", "volume", "speed", "threshold",
          "audio_input", "audio_output", "replace", "mute_key"}


def get_config(err_dialog_parent):
    config = None
    err_dtl = ''
    if os.path.exists(config_path):
        try:
            with open(config_path) as cf:
                config = json.load(cf)
            # check if file contains all required parameters
            if params > set(config):
                config = None
        except Exception as e:
            err_dtl = '\n' + str(e)
            config = None
    if config is None:
        # file not found or invalid
        # show warning and load defaults
        msg = '''\
              Configuration file missing or invalid.
              Using default values.'''
        messagebox.showwarning(title='Invalid Configuration',
                               message=dedent(msg)+err_dtl,
                               parent=err_dialog_parent)
        config = json.loads(DEFAULTS_JSON)
    return config


def save_config(config):
    with open(config_path, 'w') as cf:
        json.dump(config, cf, indent=4)


# TODO docstrings
