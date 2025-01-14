import tkinter as tk
import json
import whisper
from whisper import tokenizer
import pyaudio
import keyboard
import glob
import shutil
import os

class MainWindow(object):
    def __init__(self, version):

        self.FONT = "Cascadia Code"
        print(version)

        self.tkui = tk.Tk()
        self.tkui.minsize(810, 380)
        self.tkui.maxsize(810, 380)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT")

        self.text_lbl = tk.Label(self.tkui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 27))
        self.text_lbl.place(relx=0.5, rely=0.45, anchor="center")

        self.conf_lbl = tk.Label(self.tkui, text=f"Loading...")
        self.conf_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.conf_lbl.place(relx=0.01, rely=0.935, anchor="w")

        self.ver_lbl = tk.Label(self.tkui, text=f" VRCTextboxSTT {version} by I5UCC")
        self.ver_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.ver_lbl.place(relx=0.99, rely=0.05, anchor="e")

        self.status_lbl = tk.Label(self.tkui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.tkui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=(self.FONT, 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.btn_settings = tk.Button(self.tkui, text="Settings")
        self.btn_settings.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=20, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_settings.place(relx=0.99, rely=0.94, anchor="e")

        self.textfield = tk.Entry(self.tkui)
        self.textfield.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=25, highlightthickness=0, insertbackground="#666666")
        self.textfield.place(relx=0.5, rely=0.845, anchor="center", width=792, height=25)
        self.update()

    def open(self):
        self.tkui.mainloop()

    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def create_loop(self, intervall, func):
        func()
        self.tkui.after(intervall, self.create_loop, *[intervall, func])

    def set_status_label(self, text, color="orange"):
        self.status_lbl.configure(text=text)
        self.color_lbl.configure(bg=color)
        self.update()
        print(text)

    def set_text_label(self, text):
        self.text_lbl.configure(text=text)
        self.update()

    def loading_status(self, s: str):
        try:
            self.set_text_label(f"Downloading Model:{s[s.rindex('|')+1:]}")
        except Exception:
            self.set_text_label("Done.")

    def set_conf_label(self, ip, port, server_port, ovr_initialized, use_cpu, model):
        self.conf_lbl.configure(text=f"OSC: {ip}#{port}:{server_port}, OVR: {'Connected' if ovr_initialized else 'Disconnected'}, Device: {'CPU' if use_cpu else 'GPU'}, Model: {model}")
        self.update()

    def clear_textfield(self):
        self.textfield.delete(0, tk.END)
        self.update()

    def on_closing(self):
        self.tkui.destroy()

    def set_button_enabled(self, state=False):
        if state:
            self.btn_settings.configure(state="normal")
        else:
            self.btn_settings.configure(state="disabled")


class SettingsWindow:
    def __init__(self, config, config_path):
        self.languages = ["Auto Detect"] + sorted(tokenizer.TO_LANGUAGE_CODE.keys())
        
        self.config = config
        self.config_path = config_path
        self.FONT = "Cascadia Code"
        PADX_R = '0'
        PADX_L = '10'
        PADY = '4'
        self.yn_options = ["yes", "no"]
        self.whisper_models = whisper.available_models()
        self.whisper_models = [x for x in self.whisper_models if ".en" not in x]
        self.tooltip_window = None

        self.tkui = tk.Tk()
        self.tkui.minsize(875, 450)
        self.tkui.maxsize(875, 450)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Settings")

        self.label_osc_ip = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC IP', font=(self.FONT, 12))
        self.label_osc_ip.grid(row=0, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_ip.bind("<Enter>", (lambda event: self.show_tooltip("IP to send the OSC information to.")))
        self.label_osc_ip.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_ip = tk.Entry(self.tkui)
        self.entry_osc_ip.insert(0, self.config["osc_ip"])
        self.entry_osc_ip.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_ip.grid(row=0, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_ip.bind("<Enter>", (lambda event: self.show_tooltip("IP to send the OSC information to.")))
        self.entry_osc_ip.bind("<Leave>", self.hide_tooltip)
        

        self.label_osc_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Port', font=(self.FONT, 12))
        self.label_osc_port.grid(row=1, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to send the OSC information to.")))
        self.label_osc_port.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_port = tk.Entry(self.tkui)
        self.entry_osc_port.insert(0, self.config["osc_port"])
        self.entry_osc_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_port.grid(row=1, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to send the OSC information to.")))
        self.entry_osc_port.bind("<Leave>", self.hide_tooltip)

        self.label_osc_server_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Server Port', font=(self.FONT, 12))
        self.label_osc_server_port.grid(row=2, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_server_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to get the OSC information from.\nUsed to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar.\nOnly used if KAT Sync Params is set to 'Auto Detect' and use KAT set to 'Yes'")))
        self.label_osc_server_port.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_server_port = tk.Entry(self.tkui)
        self.entry_osc_server_port.insert(0, self.config["osc_server_port"])
        self.entry_osc_server_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23, disabledbackground="#444444")
        self.entry_osc_server_port.grid(row=2, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_server_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to get the OSC information from.\nUsed to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar.\nOnly used if KAT Sync Params is set to 'Auto Detect' and use KAT set to 'Yes'")))
        self.entry_osc_server_port.bind("<Leave>", self.hide_tooltip)

        self.label_model = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Model', font=(self.FONT, 12))
        self.label_model.grid(row=3, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_model.bind("<Enter>", (lambda event: self.show_tooltip("What model of whisper to use. \nI'd recommend not going over 'tiny,base,small'\n as it will significantly impact the transcription time.")))
        self.label_model.bind("<Leave>", self.hide_tooltip)
        self.value_model = tk.StringVar(self.tkui)
        self.value_model.set(self.config["model"])
        self.opt_model = tk.OptionMenu(self.tkui, self.value_model, *self.whisper_models)
        self.opt_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_model.grid(row=3, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_model.bind("<Enter>", (lambda event: self.show_tooltip("What model of whisper to use. \nI'd recommend not going over 'tiny,base,small'\n as it will significantly impact the transcription time.")))
        self.opt_model.bind("<Leave>", self.hide_tooltip)

        self.label_language = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Language', font=(self.FONT, 12))
        self.label_language.grid(row=4, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_language.bind("<Enter>", (lambda event: self.show_tooltip("Language to use, 'english' will be faster then other languages. \nLeaving it empty will let the program decide what language you are speaking.")))
        self.label_language.bind("<Leave>", self.hide_tooltip)
        self.value_language = tk.StringVar(self.tkui)
        self.value_language.set("Auto Detect" if self.config["language"] == "" else self.config["language"])
        self.value_language.trace("w", self.language_changed)
        self.opt_language = tk.OptionMenu(self.tkui, self.value_language, *self.languages)
        self.opt_language.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_language.grid(row=4, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_language.bind("<Enter>", (lambda event: self.show_tooltip("Language to use, 'english' will be faster then other languages. \nLeaving it empty will let the program decide what language you are speaking.")))
        self.opt_language.bind("<Leave>", self.hide_tooltip)

        self.label_translate = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Translate to English', font=(self.FONT, 12))
        self.label_translate.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.label_translate.bind("<Leave>", self.hide_tooltip)
        self.label_translate.grid(row=5, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_translate = tk.StringVar(self.tkui)
        self.value_translate.set("yes" if bool(self.config["translate_to_english"]) else "no")
        self.opt_translate = tk.OptionMenu(self.tkui, self.value_translate, *self.yn_options)
        self.opt_translate.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_translate.grid(row=5, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_translate.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.opt_translate.bind("<Leave>", self.hide_tooltip)

        self.label_hotkey = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hotkey', font=(self.FONT, 12))
        self.label_hotkey.grid(row=6, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_hotkey.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nKlick on the button and press the button you want to use.")))
        self.label_hotkey.bind("<Leave>", self.hide_tooltip)
        self.set_key = self.config["hotkey"]
        self.button_hotkey = tk.Button(self.tkui, text=self.config["hotkey"], command=self.button_hotkey_pressed)
        self.button_hotkey.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=23, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_hotkey.grid(row=6, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.button_hotkey.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nKlick on the button and press the button you want to use.")))
        self.button_hotkey.bind("<Leave>", self.hide_tooltip)

        self.label_mode = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Transcription Mode', font=(self.FONT, 12))
        self.label_mode.grid(row=7, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_mode.bind("<Enter>", (lambda event: self.show_tooltip("If set to 'realtime' it will show interim results while you are talking until you are done talking.\nIf set to 'once' it will only listen once and then stop listening, like it used to be.")))
        self.label_mode.bind("<Leave>", self.hide_tooltip)
        self.value_mode = tk.StringVar(self.tkui)
        self.options_mode = ["once", "once_continuous", "realtime"]
        self.value_mode.set(self.options_mode[self.config["mode"]])
        self.value_mode.trace("w", self.mode_changed)
        self.opt_mode = tk.OptionMenu(self.tkui, self.value_mode, *self.options_mode)
        self.opt_mode.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mode.grid(row=7, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_mode.bind("<Enter>", (lambda event: self.show_tooltip("If set to 'realtime' it will show interim results while you are talking until you are done talking.\nIf set to 'once' it will only listen once and then stop listening, like it used to be.")))
        self.opt_mode.bind("<Leave>", self.hide_tooltip)
        self.value_mode.trace_add("write", (lambda *args: self.changed()))

        self.label_det = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Dynamic Energy Threshold', font=(self.FONT, 12))
        self.label_det.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.label_det.bind("<Leave>", self.hide_tooltip)
        self.label_det.grid(row=8, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_det = tk.StringVar(self.tkui)
        self.value_det.set("yes" if bool(self.config["dynamic_energy_threshold"]) else "no")
        self.opt_det = tk.OptionMenu(self.tkui, self.value_det, *self.yn_options)
        self.opt_det.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_det.grid(row=8, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_det.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.opt_det.bind("<Leave>", self.hide_tooltip)

        self.label_energy_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Energy Threshold', font=(self.FONT, 12))
        self.label_energy_threshold.grid(row=9, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_energy_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.label_energy_threshold.bind("<Leave>", self.hide_tooltip)
        self.entry_energy_threshold = tk.Entry(self.tkui)
        self.entry_energy_threshold.insert(0, self.config["energy_threshold"])
        self.entry_energy_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_energy_threshold.grid(row=9, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_energy_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.entry_energy_threshold.bind("<Leave>", self.hide_tooltip)
        self.button_refresh = tk.Button(self.tkui, text=" ⭯ ")
        self.button_refresh.configure(bg="#333333", fg="white", highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_refresh.grid(row=9, column=2, padx=2, pady=3, sticky='ws')
        self.button_refresh.bind("<Enter>", (lambda event: self.show_tooltip("Manually refreshes the energy threshold value. \n Be silent for 5 Seconds after pressing this button. \n The Textfield is going to be populated with the new value.")))
        self.button_refresh.bind("<Leave>", self.hide_tooltip)

        self.label_pause_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Pause Threshold', font=(self.FONT, 12))
        self.label_pause_threshold.grid(row=10, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_pause_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Amount of seconds to wait when current energy is under the 'energy_threshold'.")))
        self.label_pause_threshold.bind("<Leave>", self.hide_tooltip)
        self.entry_pause_threshold = tk.Entry(self.tkui)
        self.entry_pause_threshold.insert(0, self.config["pause_threshold"])
        self.entry_pause_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_pause_threshold.grid(row=10, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_pause_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Amount of seconds to wait when current energy is under the 'energy_threshold'.")))
        self.entry_pause_threshold.bind("<Leave>", self.hide_tooltip)

        self.label_enable_overlay = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Enable Overlay', font=(self.FONT, 12))
        self.label_enable_overlay.grid(row=0, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_enable_overlay.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the SteamVR Overlay")))
        self.label_enable_overlay.bind("<Leave>", self.hide_tooltip)
        self.value_enable_overlay = tk.StringVar(self.tkui)
        self.value_enable_overlay.set("yes" if bool(self.config["overlay_enabled"]) else "no")
        self.opt_enable_overlay = tk.OptionMenu(self.tkui, self.value_enable_overlay, *self.yn_options)
        self.opt_enable_overlay.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_enable_overlay.grid(row=0, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_enable_overlay.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the SteamVR Overlay")))
        self.opt_enable_overlay.bind("<Leave>", self.hide_tooltip)
        self.value_enable_overlay.trace_add("write", (lambda *args: self.changed()))
        self.button_settings_overlay = tk.Button(self.tkui, text=" ⚙ ", command=self.open_overlay_window)
        self.button_settings_overlay.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_settings_overlay.grid(row=0, column=6, padx=2, pady=7, sticky='ws')
        self.button_settings_overlay.bind("<Enter>", (lambda event: self.show_tooltip("Edit Overlay Settings")))
        self.button_settings_overlay.bind("<Leave>", self.hide_tooltip)

        self.label_obs_source = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Enable OBS Source', font=(self.FONT, 12))
        self.label_obs_source.grid(row=1, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.label_obs_source.bind("<Leave>", self.hide_tooltip)
        self.value_obs_source = tk.StringVar(self.tkui)
        self.value_obs_source.set("yes" if bool(self.config["enable_obs_source"]) else "no")
        self.opt_obs_source = tk.OptionMenu(self.tkui, self.value_obs_source, *self.yn_options)
        self.opt_obs_source.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_obs_source.grid(row=1, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.opt_obs_source.bind("<Leave>", self.hide_tooltip)
        self.value_obs_source.trace_add("write", (lambda *args: self.changed()))
        self.button_obs_source = tk.Button(self.tkui, text=" ⚙ ", command=self.open_obs_window)
        self.button_obs_source.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_obs_source.grid(row=1, column=6, padx=2, pady=7, sticky='ws')
        self.button_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("Edit OBS Source Settings (Requires Restart)")))
        self.button_obs_source.bind("<Leave>", self.hide_tooltip)

        self.label_timeout_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Timeout Time', font=(self.FONT, 12))
        self.label_timeout_time.grid(row=2, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait for the user to speak before timeout.")))
        self.label_timeout_time.bind("<Leave>", self.hide_tooltip)
        self.entry_timeout_time = tk.Entry(self.tkui)
        self.entry_timeout_time.insert(0, self.config["timeout_time"])
        self.entry_timeout_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_timeout_time.grid(row=2, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait for the user to speak before timeout.")))
        self.entry_timeout_time.bind("<Leave>", self.hide_tooltip)

        self.label_hold_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hold Time', font=(self.FONT, 12))
        self.label_hold_time.grid(row=3, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_hold_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to hold the button to clear the Textbox.")))
        self.label_hold_time.bind("<Leave>", self.hide_tooltip)
        self.entry_hold_time = tk.Entry(self.tkui)
        self.entry_hold_time.insert(0, self.config["hold_time"])
        self.entry_hold_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_hold_time.grid(row=3, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_hold_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to hold the button to clear the Textbox.")))
        self.entry_hold_time.bind("<Leave>", self.hide_tooltip)

        self.label_phrase_time_limit = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Phrase time limit', font=(self.FONT, 12))
        self.label_phrase_time_limit.grid(row=4, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_phrase_time_limit.bind("<Enter>", (lambda event: self.show_tooltip("The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached")))
        self.label_phrase_time_limit.bind("<Leave>", self.hide_tooltip)
        self.entry_phrase_time_limit = tk.Entry(self.tkui)
        self.entry_phrase_time_limit.insert(0, self.config["phrase_time_limit"])
        self.entry_phrase_time_limit.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_phrase_time_limit.grid(row=4, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_phrase_time_limit.bind("<Enter>", (lambda event: self.show_tooltip("The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached")))
        self.entry_phrase_time_limit.bind("<Leave>", self.hide_tooltip)

        self.label_mic = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Microphone', font=(self.FONT, 12))
        self.label_mic.grid(row=5, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_mic.bind("<Enter>", (lambda event: self.show_tooltip("What microphone to use. 'Default' will use your systems default microphone.")))
        self.label_mic.bind("<Leave>", self.hide_tooltip)
        self.option_index = 0 if self.config["microphone_index"] is None else int(self.config["microphone_index"]) + 1
        self.options_mic = self.get_sound_devices()
        self.value_mic = tk.StringVar(self.tkui)
        self.value_mic.set(self.options_mic[self.option_index])
        self.opt_mic = tk.OptionMenu(self.tkui, self.value_mic, *self.options_mic)
        self.opt_mic.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mic.grid(row=5, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_mic.bind("<Enter>", (lambda event: self.show_tooltip("What microphone to use. 'Default' will use your systems default microphone.")))
        self.opt_mic.bind("<Leave>", self.hide_tooltip)

        self.label_word_replacements = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Word Replacement', font=(self.FONT, 12))
        self.label_word_replacements.grid(row=6, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_word_replacements.bind("<Enter>", (lambda event: self.show_tooltip("If you want to enable Word replacements.")))
        self.label_word_replacements.bind("<Leave>", self.hide_tooltip)
        self.value_word_replacements = tk.StringVar(self.tkui)
        self.value_word_replacements.set("yes" if bool(self.config["enable_word_replacements"]) else "no")
        self.opt_enable_replacement = tk.OptionMenu(self.tkui, self.value_word_replacements, *self.yn_options)
        self.opt_enable_replacement.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_enable_replacement.grid(row=6, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_enable_replacement.bind("<Enter>", (lambda event: self.show_tooltip("If you want to enable Word replacements.")))
        self.opt_enable_replacement.bind("<Leave>", self.hide_tooltip)
        self.button_word_replacements = tk.Button(self.tkui, text=" ⚙ ", command=self.open_replacement_window)
        self.button_word_replacements.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_word_replacements.grid(row=6, column=6, padx=2, pady=7, sticky='ws')
        self.button_word_replacements.bind("<Enter>", (lambda event: self.show_tooltip("Edit Word replacements.")))
        self.button_word_replacements.bind("<Leave>", self.hide_tooltip)

        self.label_use_textbox = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Textbox', font=(self.FONT, 12))
        self.label_use_textbox.grid(row=7, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_textbox.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.label_use_textbox.bind("<Leave>", self.hide_tooltip)
        self.value_use_textbox = tk.StringVar(self.tkui)
        self.value_use_textbox.set("yes" if bool(self.config["use_textbox"]) else "no")
        self.opt_use_textbox = tk.OptionMenu(self.tkui, self.value_use_textbox, *self.yn_options)
        self.opt_use_textbox.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_textbox.grid(row=7, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_textbox.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.opt_use_textbox.bind("<Leave>", self.hide_tooltip)
        self.value_use_textbox.trace_add("write", (lambda *args: self.changed()))

        self.label_use_kat = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use KAT', font=(self.FONT, 12))
        self.label_use_kat.grid(row=8, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_kat.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to KillFrenzyAvatarText")))
        self.label_use_kat.bind("<Leave>", self.hide_tooltip)
        self.value_use_kat = tk.StringVar(self.tkui)
        self.value_use_kat.set("yes" if bool(self.config["use_kat"]) else "no")
        self.opt_use_kat = tk.OptionMenu(self.tkui, self.value_use_kat, *self.yn_options)
        self.opt_use_kat.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_kat.grid(row=8, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_kat.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to KillFrenzyAvatarText")))
        self.opt_use_kat.bind("<Leave>", self.hide_tooltip)
        self.value_use_kat.trace_add("write", (lambda *args: self.changed()))

        self.label_use_both = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Both', font=(self.FONT, 12))
        self.label_use_both.grid(row=9, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_both.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to both options above, if both available and set to 'Yes'.\nIf not, the program will prefer sending to KillFrenzyAvatarText if it is available.")))
        self.label_use_both.bind("<Leave>", self.hide_tooltip)
        self.value_use_both = tk.StringVar(self.tkui)
        self.value_use_both.set("yes" if bool(self.config["use_both"]) else "no")
        self.opt_use_both = tk.OptionMenu(self.tkui, self.value_use_both, *self.yn_options)
        self.opt_use_both.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_both.grid(row=9, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_both.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to both options above, if both available and set to 'Yes'.\nIf not, the program will prefer sending to KillFrenzyAvatarText if it is available.")))
        self.opt_use_both.bind("<Leave>", self.hide_tooltip)

        self.label_emotes = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Emotes', font=(self.FONT, 12))
        self.label_emotes.grid(row=10, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_emotes.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use emotes on KAT")))
        self.label_emotes.bind("<Leave>", self.hide_tooltip)
        self.value_emotes = tk.StringVar(self.tkui)
        self.value_emotes.set("yes" if bool(self.config["enable_emotes"]) else "no")
        self.opt_emotes = tk.OptionMenu(self.tkui, self.value_emotes, *self.yn_options)
        self.opt_emotes.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_emotes.grid(row=10, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.button_emotes = tk.Button(self.tkui, text=" ⚙ ", command=self.open_emote_window)
        self.button_emotes.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_emotes.grid(row=10, column=6, padx=2, pady=7, sticky='ws')
        self.opt_emotes.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use emotes on KAT")))
        self.opt_emotes.bind("<Leave>", self.hide_tooltip)
        self.button_emotes.bind("<Enter>", (lambda event: self.show_tooltip("Edit the emotes you want to use on KAT")))
        self.button_emotes.bind("<Leave>", self.hide_tooltip)

        self.button_reset_config = tk.Button(self.tkui, text="Reset OSC config", command=self.reset_osc_config)
        self.button_reset_config.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=26, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_reset_config.place(relx=0.86, rely=0.95, anchor="center")
        self.button_reset_config.bind("<Enter>", (lambda event: self.show_tooltip("Resets OSC config by deleting the all the usr_ folders in %APPDATA%\\..\\LocalLow\\VRChat\\VRChat\\OSC")))
        self.button_reset_config.bind("<Leave>", self.hide_tooltip)

        self.btn_save = tk.Button(self.tkui, text="Save")
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=77, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.37, rely=0.95, anchor="center")

        self.language_changed()
        self.mode_changed()

    def open_emote_window(self):
        _ = EmoteWindow(self.config, self.config_path)

    def open_replacement_window(self):
        _ = ReplacementWindow(self.config, self.config_path)

    def open_overlay_window(self):
        _ = OverlaySettingsWindow(self.config, self.config_path)

    def open_obs_window(self):
        _ = OBSSettingsWindow(self.config, self.config_path)

    def mode_changed(self, *args):
        if self.value_mode.get() == "realtime":
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 5.0)
        elif self.value_mode.get() == "once_continuous":
            self.entry_timeout_time.delete(0, tk.END)
            self.entry_timeout_time.insert(0, 5.0)
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 3.0)
        else:
            self.entry_timeout_time.delete(0, tk.END)
            self.entry_timeout_time.insert(0, 3.0)
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 0.8)

    def language_changed(self, *args):
        if self.value_language.get() == "english":
            self.opt_translate.configure(state="disabled")
        else:
            self.opt_translate.configure(state="normal")

    def get_sound_devices(self):
        res = ["Default"]
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdev = info.get("deviceCount")

        for i in range(0, numdev):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                res.append([i, p.get_device_info_by_host_api_device_index(0, i).get('name')])

        return res

    def get_audiodevice_index(self):
        option = self.value_mic.get()
        if option != "Default":
            return int(option[1:option.index(',')])
        else:
            return None

    def save(self):
        self.config["osc_ip"] = self.entry_osc_ip.get()
        self.config["osc_port"] = int(self.entry_osc_port.get())
        self.config["osc_server_port"] = int(self.entry_osc_server_port.get())
        self.config["model"] = self.value_model.get()
        self.config["language"] = "" if self.value_language.get() == "Auto Detect" else self.value_language.get()
        self.config["translate_to_english"] = True if self.value_translate.get() == "yes" else False
        self.config["hotkey"] = self.set_key
        _realtime = 0
        if self.value_mode.get() == "once_continuous":
            _realtime = 1
        elif self.value_mode.get() == "realtime":
            _realtime = 2
        self.config["mode"] = _realtime
        self.config["dynamic_energy_threshold"] = True if self.value_det.get() == "yes" else False
        self.config["energy_threshold"] = int(self.entry_energy_threshold.get())
        self.config["pause_threshold"] = float(self.entry_pause_threshold.get())
        self.config["timeout_time"] = float(self.entry_timeout_time.get())
        self.config["hold_time"] = float(self.entry_hold_time.get())
        self.config["phrase_time_limit"] = float(self.entry_phrase_time_limit.get())
        self.config["microphone_index"] = self.get_audiodevice_index()
        self.config["use_textbox"] = True if self.value_use_textbox.get() == "yes" else False
        self.config["use_kat"] = True if self.value_use_kat.get() == "yes" else False
        self.config["use_both"] = True if self.value_use_both.get() == "yes" else False
        self.config["enable_emotes"] = True if self.value_emotes.get() == "yes" else False
        self.config["overlay_enabled"] = True if self.value_enable_overlay.get() == "yes" else False
        self.config["enable_word_replacements"] = True if self.value_word_replacements.get() == "yes" else False
        self.config["enable_obs_source"] = True if self.value_obs_source.get() == "yes" else False

        json.dump(self.config, open(self.config_path, "w"), indent=4)

    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def open(self):
        print("OPEN SETTINGS")
        self.tkui.mainloop()

    def on_closing(self):
        self.closed = True
        self.tkui.destroy()

    def button_hotkey_pressed(self):
        self.button_hotkey.configure(text="ESC to cancel...", state="disabled", disabledforeground="white")
        self.update()
        key = keyboard.read_key()
        if key != "esc":
            self.set_key = key
        self.button_hotkey.configure(text=self.set_key, state="normal")
        self.update()

    def show_tooltip(self, text):
        # Create a new top-level window with the tooltip text
        self.tooltip_window = tk.Toplevel(self.tkui, bg="black")
        tooltip_label = tk.Label(self.tooltip_window, text=text, fg="white", bg="black", font=(self.FONT, 10))
        tooltip_label.pack()

        # Use the overrideredirect method to remove the window's decorations
        self.tooltip_window.overrideredirect(True)

        # Calculate the coordinates for the tooltip window
        x = self.tkui.winfo_pointerx() + 10
        y = self.tkui.winfo_pointery()
        self.tooltip_window.geometry("+{}+{}".format(x, y))

    def hide_tooltip(self, event):
        # Destroy the tooltip window
        try:
            self.tooltip_window.destroy()
        except:
            pass
        self.tooltip_window = None

    def changed(self):
        if self.value_use_kat.get() == "no" or self.value_use_textbox.get() == "no":
            self.opt_use_both.configure(state="disabled")
        else:
            self.opt_use_both.configure(state="normal")

    def set_energy_threshold(self, text):
        self.entry_energy_threshold.delete(0, tk.END)
        self.entry_energy_threshold.insert(0, str(text))
        self.update()

    def reset_osc_config(self):
        print("RESET OSC CONFIG")
        appdata_path = os.getenv('APPDATA')
        osc_path = appdata_path + "\\..\\LocalLow\\VRChat\\VRChat\\OSC"
        dirs = glob.glob(osc_path + "\\usr_*\\")
        for dir in dirs:
            shutil.rmtree(dir)

class EmoteWindow:
    def __init__(self, config, config_path):
        self.config_path = config_path
        self.config = config
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        self.tkui.minsize(650, 390)
        self.tkui.maxsize(650, 390)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Emotes")

        self.current_selection = None
        
        self.entry = tk.Entry(self.tkui)
        self.entry.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=55)
        self.entry.place(relx=0.415, rely=0.05, anchor="center")

        self.button = tk.Button(self.tkui, text="Edit")
        self.button.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.edit_entry)
        self.button.place(relx=0.91, rely=0.05, anchor="center")

        self.values = list(self.config["emotes"].items())
        self.lbox = tk.Listbox(self.tkui, font=(self.FONT, 12), width=70, height=15, bg="#333333", fg="#FFFFFF", selectbackground="#777777", selectforeground="#FFFFFF", bd=0, activestyle="none")
        self.lbox.place(relx=0.5, rely=0.53, anchor="center")
        self.lbox.bind('<<ListboxSelect>>', self.item_selected)
        
        self.update_lbox()

        self.tkui.mainloop()

    def item_selected(self, event):
        if self.lbox.curselection():
            self.current_selection = self.lbox.curselection()[0]
            self.set_entry(self.config["emotes"][str(self.current_selection)])
            self.button.configure(state="normal")

    def set_entry(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def edit_entry(self):
        self.config["emotes"][str(self.current_selection)] = self.entry.get()
        self.update_lbox()
        self.button.configure(state="disabled")
        self.entry.delete(0, tk.END)
        json.dump(self.config, open(self.config_path, "w"), indent=4)

    def update_lbox(self):
        self.values = list(self.config["emotes"].items())
        self.lbox.delete(0, tk.END)
        for key, value in self.values:
            self.lbox.insert(tk.END, f"{key}: \"{value}\"")


    def on_closing(self):
        self.tkui.destroy()

class ReplacementWindow:
    def __init__(self, config, config_path):
        self.config_path = config_path
        self.config = config
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        self.tkui.minsize(760, 430)
        self.tkui.maxsize(760, 430)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Word Replacement")

        self.current_selection = None
        self.current_key = None

        self.label_word = tk.Label(self.tkui, text="Word", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_word.grid(row=0, column=1, padx=5, pady=5, sticky='ws')
        self.label_replace = tk.Label(self.tkui, text="Replacement", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_replace.grid(row=1, column=1, padx=5, pady=5, sticky='ws')
        
        self.entry_word = tk.Entry(self.tkui)
        self.entry_word.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=45)
        self.entry_word.grid(row=0, column=2, padx=5, pady=5, sticky='ws')

        self.entry_replace = tk.Entry(self.tkui)
        self.entry_replace.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=45)
        self.entry_replace.grid(row=1, column=2, padx=5, pady=5, sticky='ws')

        self.button_edit = tk.Button(self.tkui, text="Add")
        self.button_edit.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", command=self.add_edit_entry)
        self.button_edit.grid(row=0, column=3, padx=5, pady=5, sticky='ws')

        self.button_deselect = tk.Button(self.tkui, text="Deselect")
        self.button_deselect.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.button_deselect_pressed)
        self.button_deselect.grid(row=1, column=3, padx=5, pady=5, sticky='ws')

        self.button_delete = tk.Button(self.tkui, text="Remove")
        self.button_delete.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.button_delete_pressed)
        self.button_delete.grid(row=1, column=4, padx=5, pady=5, sticky='ws')

        self.lbox = tk.Listbox(self.tkui, font=(self.FONT, 12), width=82, height=15, bg="#333333", fg="#FFFFFF", selectbackground="#777777", selectforeground="#FFFFFF", bd=0, activestyle="none")
        self.lbox.place(relx=0.5, rely=0.58, anchor="center")
        self.lbox.bind('<<ListboxSelect>>', self.item_selected)
        
        self.update_lbox()

        self.tkui.mainloop()

    def item_selected(self, event):
        if self.lbox.curselection():
            self.button_edit.configure(text="Edit")
            self.entry_replace.delete(0, tk.END)
            self.entry_word.delete(0, tk.END)
            
            self.current_selection = self.lbox.curselection()[0]
            self.current_key = list(self.config["word_replacements"])[self.current_selection]

            
            self.entry_word.insert(0, self.current_key)
            self.entry_replace.insert(0, self.config["word_replacements"][self.current_key])
            
            self.button_deselect.configure(state="normal")
            self.button_delete.configure(state="normal")

    def add_edit_entry(self):
        if self.entry_word.get() == "" and self.entry_replace.get() == "":
            return

        if self.button_edit["text"] == "Add":
            self.config["word_replacements"][self.entry_word.get()] = self.entry_replace.get()
        elif self.current_key != self.entry_word.get() or self.config["word_replacements"][self.current_key] != self.entry_replace.get():
            del self.config["word_replacements"][self.current_key]
            self.config["word_replacements"][self.entry_word.get()] = self.entry_replace.get()
        
        self.button_deselect_pressed()
        self.update_lbox()
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        json.dump(self.config, open(self.config_path, "w"), indent=4)
    
    def button_deselect_pressed(self):
        self.button_edit.configure(text="Add")
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        self.lbox.selection_clear(0, tk.END)
        self.button_deselect.configure(state="disabled")
        self.button_delete.configure(state="disabled")

    def button_delete_pressed(self):
        del self.config["word_replacements"][self.current_key]
        json.dump(self.config, open(self.config_path, "w"), indent=4)
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        self.button_deselect_pressed()
        self.update_lbox()
        pass

    def update_lbox(self):
        self.values = list(self.config["word_replacements"].items())
        self.lbox.delete(0, tk.END)
        for key, value in self.values:
            self.lbox.insert(tk.END, f"{key} -> {value}")


class OverlaySettingsWindow:
    def __init__(self, config, config_path):
        self.config_path = config_path
        self.config = config
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        self.tkui.minsize(350, 305)
        self.tkui.maxsize(350, 305)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Overlay Settings")

        self.current_selection = None
        self.current_key = None

        self.label_pos_x = tk.Label(self.tkui, text="Position X", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_pos_x.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.entry_pos_x = tk.Entry(self.tkui)
        self.entry_pos_x.insert(0, self.config["overlay"]["pos_x"])
        self.entry_pos_x.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_pos_x.grid(row=0, column=2, padx=12, pady=5, sticky='ws')

        self.label_pos_y = tk.Label(self.tkui, text="Position Y", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_pos_y.grid(row=1, column=1, padx=12, pady=5, sticky='ws')
        self.entry_pos_y = tk.Entry(self.tkui)
        self.entry_pos_y.insert(0, self.config["overlay"]["pos_y"])
        self.entry_pos_y.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_pos_y.grid(row=1, column=2, padx=12, pady=5, sticky='ws')

        self.label_size = tk.Label(self.tkui, text="Size", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_size.grid(row=2, column=1, padx=12, pady=5, sticky='ws')
        self.entry_size = tk.Entry(self.tkui)
        self.entry_size.insert(0, self.config["overlay"]["size"])
        self.entry_size.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_size.grid(row=2, column=2, padx=12, pady=5, sticky='ws')

        self.label_distance = tk.Label(self.tkui, text="Distance", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_distance.grid(row=3, column=1, padx=12, pady=5, sticky='ws')
        self.entry_distance = tk.Entry(self.tkui)
        self.entry_distance.insert(0, self.config["overlay"]["distance"])
        self.entry_distance.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_distance.grid(row=3, column=2, padx=12, pady=5, sticky='ws')

        self.label_font_color = tk.Label(self.tkui, text="Font Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_font_color.grid(row=4, column=1, padx=12, pady=5, sticky='ws')
        self.entry_font_color = tk.Entry(self.tkui)
        self.entry_font_color.insert(0, self.config["overlay"]["font_color"])
        self.entry_font_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_font_color.grid(row=4, column=2, padx=12, pady=5, sticky='ws')

        self.label_border_color = tk.Label(self.tkui, text="Border Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_border_color.grid(row=5, column=1, padx=12, pady=5, sticky='ws')
        self.entry_border_color = tk.Entry(self.tkui)
        self.entry_border_color.insert(0, self.config["overlay"]["border_color"])
        self.entry_border_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_border_color.grid(row=5, column=2, padx=12, pady=5, sticky='ws')

        self.label_opacity = tk.Label(self.tkui, text="Opacity", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_opacity.grid(row=6, column=1, padx=12, pady=5, sticky='ws')
        self.entry_opacity = tk.Entry(self.tkui)
        self.entry_opacity.insert(0, self.config["overlay"]["opacity"])
        self.entry_opacity.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_opacity.grid(row=6, column=2, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=39, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.92, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config["overlay"]["pos_x"] = float(self.entry_pos_x.get())
        self.config["overlay"]["pos_y"] = float(self.entry_pos_y.get())
        self.config["overlay"]["size"] = float(self.entry_size.get())
        self.config["overlay"]["distance"] = float(self.entry_distance.get())
        self.config["overlay"]["font_color"] = self.entry_font_color.get()
        self.config["overlay"]["border_color"] = self.entry_border_color.get()
        self.config["overlay"]["opacity"] = float(self.entry_opacity.get())

        json.dump(self.config, open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class OBSSettingsWindow:
    def __init__(self, config, config_path):
        self.config_path = config_path
        self.config = config
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        self.tkui.minsize(370, 230)
        self.tkui.maxsize(370, 230)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - OBS Source Settings")

        self.current_selection = None
        self.current_key = None

        self.label_port = tk.Label(self.tkui, text="Port", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_port.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.entry_port = tk.Entry(self.tkui)
        self.entry_port.insert(0, self.config["obs_source"]["port"])
        self.entry_port.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_port.grid(row=0, column=2, padx=12, pady=5, sticky='ws')

        self.label_update_interval = tk.Label(self.tkui, text="Update Interval", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_update_interval.grid(row=1, column=1, padx=12, pady=5, sticky='ws')
        self.entry_update_interval = tk.Entry(self.tkui)
        self.entry_update_interval.insert(0, self.config["obs_source"]["update_interval"])
        self.entry_update_interval.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_update_interval.grid(row=1, column=2, padx=12, pady=5, sticky='ws')

        self.label_font = tk.Label(self.tkui, text="Font", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_font.grid(row=2, column=1, padx=12, pady=5, sticky='ws')
        self.entry_font = tk.Entry(self.tkui)
        self.entry_font.insert(0, self.config["obs_source"]["font"])
        self.entry_font.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_font.grid(row=2, column=2, padx=12, pady=5, sticky='ws')

        self.label_color = tk.Label(self.tkui, text="Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_color.grid(row=3, column=1, padx=12, pady=5, sticky='ws')
        self.entry_color = tk.Entry(self.tkui)
        self.entry_color.insert(0, self.config["obs_source"]["color"])
        self.entry_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_color.grid(row=3, column=2, padx=12, pady=5, sticky='ws')

        self.label_align = tk.Label(self.tkui, text="Align", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_align.grid(row=4, column=1, padx=12, pady=5, sticky='ws')
        self.value_align = tk.StringVar(self.tkui)
        self.value_align.set(self.config["obs_source"]["align"])
        self.opt_align = tk.OptionMenu(self.tkui, self.value_align, *["center", "left", "right"])
        self.opt_align.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_align.grid(row=4, column=2, padx=12, pady=5, sticky='ws')
        

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=43, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.90, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config["obs_source"]["port"] = int(self.entry_port.get())
        self.config["obs_source"]["update_interval"] = int(self.entry_update_interval.get())
        self.config["obs_source"]["font"] = self.entry_font.get()
        self.config["obs_source"]["color"] = self.entry_color.get()
        self.config["obs_source"]["align"] = self.value_align.get()

        json.dump(self.config, open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()
