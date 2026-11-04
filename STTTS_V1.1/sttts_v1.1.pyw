# GUI
from tkinter import messagebox
# AUDIO
import sounddevice as sd
# ETC
import numpy as np
from textwrap import dedent
import queue
import os
from threading import Thread
# My Modules
import sttts_modules.sttts_config as conf
import sttts_modules.sttts_gui as gui
import sttts_modules.sttts_etc as etc
import sttts_modules.sttts_sttproc as sttmod
import sttts_modules.sttts_tts as ttsmod

audio_queue = None


def audio_cb(indata, frames, time, status):
    audio_queue.put(bytes(indata))


def try_get_nb(q):
    try:
        return q.get_nowait()
    except queue.Empty:
        return None
    

def audio_run(win, stt, tts, audio_queue, control_queue, bval, sval):
    threshold = 0.0
    def slider_cb(var, index, mode):
        nonlocal threshold
        threshold = sval.get()
    sval.trace_add('write', slider_cb)
    devs = sd.query_devices()
    bar_visible = False
    muted = False
    in_dev = sd.default.device[0]
    while True:
        # set sample rate
        samplerate = devs[in_dev]['default_samplerate']
        # check if device supports format
        try:
            sd.check_input_settings(device=in_dev, channels=1,
                                    dtype='int16', samplerate=samplerate)
        except sd.PortAudioError as e:
            # show error dialog
            msg = 'Error opening device:\n'+devs[in_dev]['name']\
                  + '\nSwitched back to default.'
            messagebox.showerror(title='IO Error', message=msg,
                                 detail=e.args[0], parent=win.root)
            # fall back to default
            in_dev = sd.default.device[0]
            samplerate = devs[in_dev]['default_samplerate']
            # set combobox
            win.aud_tab.inp.event_generate('<<SrcBoxReset>>')
        # open audio input stream
        try:
            with sd.RawInputStream(samplerate=samplerate, blocksize=4096,
                                   device=in_dev, dtype='int16',
                                   channels=1, callback=audio_cb):
                # init recogniser
                stt.set_rate(samplerate)
                lastmean = 0.0
                ctrl = try_get_nb(control_queue)
                while ctrl is None:
                    rawdata = audio_queue.get(timeout=0.5)
                    data = np.frombuffer(rawdata, dtype=np.int16)
                    mean_vol = np.mean(abs(data))
                    mean_vol = np.log(1 + mean_vol) * 0.126591
                    
                    valid = mean_vol > threshold
                    
                    if not muted:
                        # pass audio to recogniser
                        stt.pass_audio(rawdata, valid)
                        # get text and speak
                        text = stt.get_text()
                        if text:
                            tts.say(text)
                    if bar_visible:
                        # bar display
                        # slow decay filter
                        if mean_vol < lastmean:
                            mean_vol = lastmean * 0.95
                        bval.set(value=mean_vol)
                        lastmean = mean_vol
                    ctrl = try_get_nb(control_queue)
                # got ctrl message
                if ctrl[0] == 'bar':
                    # bar visibility changed
                    bar_visible = ctrl[1]
                elif ctrl[0] == 'term':
                    # termintion signal
                    return
                elif ctrl[0] == 'dev':
                    # input device changed
                    in_dev = ctrl[1]
                elif ctrl[0] == 'mute':
                    muted = ctrl[1]
        except queue.Empty:
            # show error dialog
            msg = 'Device not responding.\nSwitched back to default.'
            messagebox.showerror(title='IO Error', message=msg,
                                 detail=devs[in_dev]['name'], parent=win.root)
            # fall back to default
            in_dev = sd.default.device[0]
            # set combobox
            win.aud_tab.inp.event_generate('<<SrcBoxReset>>')


def terminate_win(stt, root):
    # stop stt process
    if stt is not None and stt.proc.is_alive():
        stt.terminate()
    # close window
    root.destroy()


def terminate_wait(at, stt, root):
    # wait for audio thread to terminate
    # without blocking the tk mainloop
    if not at.is_alive():
        terminate_win(stt, root)
    root.after(50, lambda: terminate_wait(at, stt, root))


def terminate(root, stt, athrd, ctrl, hk_man):
    # stop keyboard
    if hk_man is not None:
        hk_man.stop_listening()
    # stop audio thread
    if ctrl is not None and athrd.is_alive():
        ctrl.put(('term',))
        terminate_wait(athrd, stt, root)
    else:
        terminate_win(stt, root)


def main_func():
    # start tts process
    tts = ttsmod.TTS()

    # setup root window
    window = gui.Window(tts)
    # return for cleanup in case of an error
    yield window.root

    # read and check config file
    config = conf.get_config(window.root)

    # initialize text filter
    tts.init_filter(config['replace'])

    # fill voices combobox
    window.tts_tab.fill_vcs(config['voice'])
    # fill outputs combobox
    window.tts_tab.fill_devs(config['audio_output'])
    # set default tts volume and speed, confine to allowed values
    default_volume = max(0, min(100, config['volume']))
    window.tts_tab.set_volume(default_volume)
    default_speed = max(-10, min(10, config['speed']))
    window.tts_tab.set_speed(default_speed)

    # check for language model
    if not os.path.exists(config['model_path']):
        # model not found, continue without speech to text
        msg = '''\
              Please download a model from
              https://alphacephei.com/vosk/models
              and set "model_path" in config.json.'''
        messagebox.showwarning(title='Model not found',
                               message='Missing language model\n',
                               detail=dedent(msg), parent=window.root)
        # disable input device selection, toggle mute off
        # activate text field, show tab with text field
        window.aud_tab.disable_in()
        window.txt_tab.toggle_mute()
        window.txt_tab.toggle_text()
        window.nbk.select(1)
        # bug causes text field to be unresponsive until a
        # combobox is clicked. fixed by minimising the window
        window.root.iconify()
        window.root.deiconify()
        stt = None
        control_queue = None
        audio_thread = None
        # return for cleanup in case of an error
        yield stt, audio_thread, control_queue
    else:
        # start stt process
        stt = sttmod.STT(config['model_path'])
        stt.proc.start()
        # start audio thread
        global audio_queue
        audio_queue = queue.Queue()
        control_queue = queue.Queue()
        audio_thread = Thread(target=audio_run,
                              args=(window, stt, tts,
                                    audio_queue, control_queue,
                                    window.aud_tab.bar_val,
                                    window.aud_tab.sld_val))
        audio_thread.start()
        # return for cleanup in case of an error
        yield stt, audio_thread, control_queue
        # bind progressbar updates
        window.aud_tab.bar.bind('<Visibility>',
                                lambda e: control_queue.put(('bar', True)))
        window.aud_tab.bar.bind('<Unmap>',
                                lambda e: control_queue.put(('bar', False)))
        # pass control queue to gui, fill inputs combobox
        window.aud_tab.ctrl = control_queue
        window.txt_tab.ctrl = control_queue
        window.aud_tab.fill_devs(config['audio_input'])
        window.aud_tab.set_threshold(config['threshold'])

    # hotkeys
    hk_man = etc.HotkeyManager(config, window.txt_tab.toggle_mute)
    hk_man.start_listening()
    # return for cleanup in case of an error
    yield hk_man

    # start tk mainloop
    window.root.protocol('WM_DELETE_WINDOW',
                         lambda: terminate(window.root, stt,
                                           audio_thread,
                                           control_queue, hk_man))
    window.root.mainloop()
    yield None


if __name__ == '__main__':
    root = None
    stt = None
    athrd = None
    ctrlq = None
    hk_man = None
    try:
        main_gen = main_func()
        root = main_gen.__next__()
        stt, athrd, ctrlq = main_gen.__next__()
        hk_man = main_gen.__next__()
        main_gen.__next__()
    except Exception as e:
        # show dialog
        if root is not None:
            messagebox.showerror(title='ERROR',
                                 message='An error occurred\n',
                                 detail=e, parent=root)
        # cleanup
        terminate(root, stt, athrd,
                  ctrlq, hk_man)
