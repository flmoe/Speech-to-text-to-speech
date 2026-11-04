import tkinter as tk
from tkinter import ttk
import sounddevice as sd


# combined slider and bargraph display
class BargraphSlider(tk.Canvas):

    BORDER = 5

    def __init__(self, parent, dvar, svar, **kwargs):
        # dvar variable for display bar
        # svar variable for slider
        super().__init__(parent, **kwargs)
        self.dvar = dvar
        self.dvar.trace_add('write', self.var_cb)
        self.svar = svar
        # variables
        self.disp_val = 0.0
        self.sldr_val = 0.0
        # draw rectangles
        self.bg_rect = self.create_rectangle(0, 0, 0, 0, fill='#808080',
                                             outline='#808080', tags='sldr')
        self.dval_rect = self.create_rectangle(0, 0, 0, 0, fill='#0078D7',
                                               outline='#0078D7', tags='sldr')
        self.sval_rect = self.create_rectangle(0, 0, 0, 0, fill='#F08000',
                                               outline='#F08000', tags='sldr',
                                               stipple='gray25')
        self.shdl_rect = self.create_rectangle(0, 0, 0, 0, fill='#808080',
                                               outline='#FFFFFF', tags='sldr')
        # bind configure event (widget size change)
        self.bind('<Configure>', self.size_chg)
        # bind mouse events
        self.tag_bind('sldr', '<Button-1>', self.draw_slider)
        self.tag_bind('sldr', '<B1-Motion>', self.draw_slider)

    def draw_hdl(self, xend, yend):
        # draw slider handle and bar
        s_end = int(xend*self.sldr_val)
        self.coords(self.sval_rect, self.BORDER, self.BORDER, s_end, yend)
        h_start = max(self.BORDER, s_end-5)
        h_end = min(xend, s_end+5)
        self.coords(self.shdl_rect, h_start, self.BORDER, h_end, yend)

    def size_chg(self, event):
        # size changed, redraw everything
        width = event.width
        height = event.height
        xend = width - self.BORDER
        yend = height - self.BORDER
        self.coords(self.bg_rect, self.BORDER, self.BORDER, xend, yend)
        self.coords(self.dval_rect, self.BORDER, self.BORDER,
                    int(xend*self.disp_val), yend)
        self.draw_hdl(xend, yend)

    def draw_slider(self, event):
        # slider moved, update value and redraw slider
        minv = self.coords(self.bg_rect)[0]
        maxv = self.coords(self.bg_rect)[2]
        sldv = max(min(event.x, maxv), minv)
        self.sldr_val = float(sldv) / (maxv-minv)
        self.sldr_val = round(min(1, self.sldr_val), 3)
        xend = self.winfo_width() - self.BORDER
        yend = self.winfo_height() - self.BORDER
        self.draw_hdl(xend, yend)
        self.svar.set(value=self.sldr_val)

    def set_slider(self, val):
        # slider value set, update value and redraw slider
        self.sldr_val = round(min(1, val), 3)
        xend = self.winfo_width() - self.BORDER
        yend = self.winfo_height() - self.BORDER
        self.draw_hdl(xend, yend)
        self.svar.set(value=self.sldr_val)

    def set_val(self, val):
        # update bar value
        self.disp_val = val
        xend = self.winfo_width() - self.BORDER
        yend = self.winfo_height() - self.BORDER
        self.coords(self.dval_rect, self.BORDER, self.BORDER,
                    int(xend*self.disp_val), yend)

    def var_cb(self, var, index, mode):
        self.set_val(self.dvar.get())


# root window and notebook
class Window():

    def __init__(self, tts):
        self.tts = tts        
        self.root = tk.Tk()
        self.root.title('STTTS V01.1')
        self.nbk = ttk.Notebook(self.root)
        self.nbk.grid(row=0, column=0, sticky='nswe')
        self.root.columnconfigure(0, weight=1)
        self._fill_nb()

    def _fill_nb(self):
        self.aud_tab = Tab1(self.nbk)
        self.nbk.add(self.aud_tab.frame, text='audio settings')

        self.txt_tab = Tab2(self.nbk, self.tts)
        self.nbk.add(self.txt_tab.frame, text='text input')

        self.tts_tab = Tab3(self.nbk, self.tts)
        self.nbk.add(self.tts_tab.frame, text='text to speech')


def fill_c_box(box, values, init):
    box['values'] = values
    # fit size to contents
    max_len = max(map(len, values)) + 1
    box.config(width=max_len)
    # initial selection
    box.current(init)


# audio tab
class Tab1():

    def __init__(self, parent):
        self.ctrl = None
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.create_dev()
        self.create_bar()

    def disable_in(self):
        self.inp.config(state=tk.DISABLED)

    def select_default(self, event):
        # select default input device in combobox
        in_dev = sd.default.device[0]
        vals = list(self.inputs.values())
        _, idxs = tuple(zip(*vals))
        self.inp.current(idxs.index(in_dev))

    def fill_devs(self, default_device_name):
        # list audio src, fill select box
        apis = sd.query_hostapis()
        devs = sd.query_devices()
        # dict: <device_name>:(<device_index>,<combobox_index>)
        self.inputs = {}
        # device index
        in_dev = None
        # config string
        default_input = default_device_name.lower()
        # combobox index
        input_idx = 0
        for i, dev in enumerate(devs):
            if dev['max_input_channels'] > 0:
                # combine api and device name
                api_name = apis[dev['hostapi']]['name']
                dev_name = dev['name']
                full_name = api_name + ' | ' + dev_name
                self.inputs[full_name] = (i, input_idx)
                # choose device containing string in device name
                # or default device if string empty / not found
                if (in_dev is None and i == sd.default.device[0]) or\
                   (default_input and default_input in full_name.lower()):
                    in_dev = i
                    in_idx = input_idx
                input_idx += 1
        fill_c_box(self.inp, tuple(self.inputs), in_idx)
        if self.ctrl is not None:
            self.ctrl.put(('dev', in_dev))

    def set_input_cb(self, event):
        in_dev = self.inputs[event.widget.get()][0]
        if self.ctrl is not None:
            self.ctrl.put(('dev', in_dev))

    def create_dev(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='n', text='select input device')
        lframe.grid(row=2, column=0, pady=5)
        # Combobox for selecting input device
        self.inp = ttk.Combobox(lframe)
        self.inp.state(['readonly'])
        self.inp.grid(row=1, column=0, pady=5)
        self.inp.bind('<<ComboboxSelected>>', self.set_input_cb)
        self.inp.bind('<<SrcBoxReset>>', self.select_default)

    def set_bar_vis(self, visible):
        if self.ctrl is not None:
            self.ctrl.put(('bar', visible))
    
    def set_threshold(self, val):
        self.bar.set_slider(val)

    def create_bar(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='nw', text='Level:')
        lframe.grid(row=4, column=0, pady=5)
        # Input level and threshold BargraphSlider
        self.bar_val = tk.DoubleVar()
        self.sld_val = tk.DoubleVar()
        self.bar = BargraphSlider(lframe, self.bar_val, self.sld_val,
                                  height=20, background='gray75')
        self.bar.grid(row=3, column=0, pady=5, sticky='we')
        self.frame.bind('<Visibility>', lambda e: self.set_bar_vis(True))
        self.frame.bind('<Unmap>', lambda e: self.set_bar_vis(False))


# text tab
class Tab2():

    def __init__(self, parent, tts):
        self.muted = False
        self.tts = tts
        self.ctrl = None
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.create_mute_btn()
        self.create_text_btn()
        self.create_text_field()

    def toggle_mute(self, event=None):
        self.muted = not self.muted
        if self.muted:
            self.mbtn.config(bg='red', text='unmute mic')
            if self.ctrl is not None:
                self.ctrl.put(('mute', True))
        else:
            self.mbtn.config(bg='green', text='mute mic')
            if self.ctrl is not None:
                self.ctrl.put(('mute', False))

    def create_mute_btn(self):
        # Mute toggle button
        self.mbtn = tk.Button(self.frame, text='mute mic',
                              bg='green', command=self.toggle_mute)
        self.mbtn.grid(row=2, column=0, pady=5)

    def toggle_text(self, event=None):
        if self.text['state'] == tk.NORMAL:
            self.text.config(state=tk.DISABLED, bg='#ddd')
            self.tbtn.config(bg='red', text='activate text')
        else:
            self.text.config(state=tk.NORMAL, bg='#fff')
            self.tbtn.config(bg='green', text='deactivate text')

    def create_text_btn(self):
        # Text field toggle button
        self.tbtn = tk.Button(self.frame, text='activate text',
                              bg='red', command=self.toggle_text)
        self.tbtn.grid(row=4, column=0, pady=5)

    def send_text(self, event):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            if event.keysym == 'Return':
                text = self.text.get(1.0, tk.END)
                self.tts.say(text)
                self.text.delete(1.0, tk.END)

    def create_text_field(self):
        # Text field for direct tts text input
        self.text = tk.Text(self.frame, width=40, height=10,
                            wrap=tk.WORD, state=tk.DISABLED, bg='#ddd')
        self.text.grid(row=6, column=0, pady=5)
        self.text.bind('<KeyRelease>', self.send_text)


# tts tab
class Tab3():

    def __init__(self, parent, tts):
        self.tts = tts
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.create_vol()
        self.create_spd()
        self.create_vc()
        self.create_dev()

    def set_volume(self, vol):
        vol = int(float(vol))
        self.cvol['text'] = f"{vol}%"
        self.volsc.config(value=vol)
        self.tts.set_volume(vol)

    def create_vol(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='nw', text='tts volume')
        lframe.grid(row=2, column=0, pady=5)
        # Label showing current volume
        self.cvol = ttk.Label(lframe)
        self.cvol.grid(row=1, column=0, pady=5)
        # Scale for setting volume
        self.volsc = ttk.Scale(lframe, command=self.set_volume,
                               from_=0, to=100, orient=tk.HORIZONTAL)
        self.volsc.grid(row=3, column=0, pady=5)

    def set_speed(self, speed):
        spd = round(float(speed), 2)
        self.tts.set_speed(spd)
        self.cspd['text'] = f"{spd}"

    def reset_speed(self, event):
        self.set_speed(0)
        self.spdsc['value'] = 0

    def create_spd(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='nw', text='tts speed')
        lframe.grid(row=4, column=0, pady=5)
        # Label showing current relative talking speed
        self.cspd = ttk.Label(lframe)
        self.cspd.grid(row=1, column=0, pady=5)
        # Scale for setting relative talking speed
        self.spdsc = ttk.Scale(lframe, command=self.set_speed,
                               from_=-10, to=10, orient=tk.HORIZONTAL)
        self.spdsc.grid(row=3, column=0, pady=5)
        # Reset speed on double click
        self.spdsc.bind('<Double-Button-1>', self.reset_speed)

    def fill_vcs(self, default_voice_name):
        # list voices, fill select box
        self.voice_names, def_vc_idx = self.tts.list_voices()
        # choose voice containing string in voice name
        default_voice = default_voice_name.lower()
        for i, name in enumerate(self.voice_names):
            if default_voice and default_voice in name.lower():
                vc_default = i
                break
        else:
            # voice not found, use current one
            vc_default = def_vc_idx
        fill_c_box(self.vcs, self.voice_names, vc_default)
        self.tts.set_voice(vc_default)

    def set_voice_cb(self, event):
        vc_str = event.widget.get()
        vc_idx = self.voice_names.index(vc_str)
        self.tts.set_voice(vc_idx)
        # say example sentence
        self.tts.say(vc_str+' voice selected.')

    def create_vc(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='n', text='set tts voice')
        lframe.grid(row=6, column=0, pady=5)
        # Combobox for selecting tts voice
        self.vcs = ttk.Combobox(lframe)
        self.vcs.state(['readonly'])
        self.vcs.grid(row=1, column=0, pady=5)
        self.vcs.bind('<<ComboboxSelected>>', self.set_voice_cb)

    def fill_devs(self, default_device_name):
        # list audio outputs, fill select box
        self.output_names, def_out_idx = self.tts.list_outputs()
        # choose device containing string in device name
        default_output = default_device_name.lower()
        for i, name in enumerate(self.output_names):
            if default_output and default_output in name.lower():
                out_default = i
                break
        else:
            # device not found, use current one
            out_default = def_out_idx
        fill_c_box(self.out, self.output_names, out_default)
        self.tts.set_output(out_default)

    def set_output_cb(self, event):
        out_str = event.widget.get()
        out_idx = self.output_names.index(out_str)
        self.tts.set_output(out_idx)

    def create_dev(self):
        # Label frame
        lframe = ttk.LabelFrame(self.frame, padding=10,
                                labelanchor='n', text='select output device')
        lframe.grid(row=8, column=0, pady=5)
        # Combobox for selecting tts output device
        self.out = ttk.Combobox(lframe)
        self.out.state(['readonly'])
        self.out.grid(row=1, column=0, pady=5)
        self.out.bind('<<ComboboxSelected>>', self.set_output_cb)
        # listed output devices may change during runtime
        # refresh list everytime it becomes visible
        self.out.bind('<Visibility>', lambda e: self.fill_devs(''))


# TODO document
