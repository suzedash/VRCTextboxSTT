import os
import sys
import json
import logging
from logtofile import LogToFile
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


VERSION = "v0.7"
VRC_INPUT_CHARLIMIT = 144
KAT_CHARLIMIT = 128
VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
AV_LISTENING_PARAM = "/avatar/parameters/stt_listening"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
LOGFILE = get_absolute_path('out.log')
CONFIG_PATH = get_absolute_path('config.json')
CONFIG = json.load(open(CONFIG_PATH))

open(LOGFILE, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = LogToFile(log, logging.INFO, LOGFILE)
sys.stderr = LogToFile(log, logging.ERROR, LOGFILE)


def loadfont(fontpath, private=True, enumerable=False):
    '''
    Makes fonts located in file `fontpath` available to the font system.

    `private`     if True, other processes cannot see this font, and this
                  font will be unloaded when the process dies
    `enumerable`  if True, this font will appear when enumerating fonts

    See https://msdn.microsoft.com/en-us/library/dd183327(VS.85).aspx

    '''
    # This function was taken from
    # https://github.com/ifwe/digsby/blob/f5fe00244744aa131e07f09348d10563f3d8fa99/digsby/src/gui/native/win/winfonts.py#L15
    # "Copyright (c) 2006-2012 Tagged, Inc; All Rights Reserved"
    FR_PRIVATE  = 0x10
    FR_NOT_ENUM = 0x20

    if isinstance(fontpath, bytes):
        pathbuf = create_string_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExA
    elif isinstance(fontpath, str):
        pathbuf = create_unicode_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExW
    else:
        raise TypeError('fontpath must be of type str or bytes')

    flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
    num_fonts_added = add_font_resource_ex(byref(pathbuf), flags, 0)
    return bool(num_fonts_added)


if os.name == 'nt':
    loadfont(get_absolute_path("resources/CascadiaCode.ttf"))


import threading
import time
import keyboard
import numpy as np
from pythonosc import udp_client
import winsound
import speech_recognition as sr
import openvr
import whisper
import torch
import re
from osc import OscHandler
from ui import MainWindow, SettingsWindow
from queue import Queue


osc_client: udp_client.SimpleUDPClient = None
osc: OscHandler = None
use_kat: bool = True
use_textbox: bool = True
use_both: bool = True
model: whisper = "base"
language: str = "english"
use_cpu: bool = False
rec: sr.Recognizer = None
source: sr.Microphone = None
data_queue: Queue = Queue()
ovr_initialized: bool = False
application: openvr.IVRSystem = None
action_set_handle: int = None
button_action_handle: int = None
curr_time: float = 0.0
pressed: bool = False
holding: bool = False
held: bool = False
thread_process: threading.Thread = threading.Thread()
config_ui: SettingsWindow = None
config_ui_open: bool = False
enter_pressed: bool = False


def init():
    global main_window
    global osc_client
    global osc
    global use_textbox
    global use_kat
    global use_both
    global model
    global language
    global use_cpu
    global rec
    global source
    global data_queue
    global ovr_initialized
    global application
    global action_set_handle
    global button_action_handle

    osc_client = udp_client.SimpleUDPClient(CONFIG["osc_ip"], int(CONFIG["osc_port"]))
    use_textbox = bool(CONFIG["use_textbox"])
    use_kat = bool(CONFIG["use_kat"])
    use_both = bool(CONFIG["use_both"])
    if use_kat:
        osc = OscHandler(osc_client, CONFIG["osc_ip"], CONFIG["osc_server_port"])
    else:
        osc = None

    _whisper_model = CONFIG["model"].lower()
    language = CONFIG["language"].lower()
    if language == "":
        language = None
    elif _whisper_model != "large" and language == "english" and ".en" not in _whisper_model:
        _whisper_model = _whisper_model + ".en"

    # Temporarily output stderr to text label for download progress.
    if not os.path.isfile(get_absolute_path(f"whisper_cache/{_whisper_model}.pt")):
        sys.stderr.write = main_window.loading_status
    else:
        print("Whisper model already in cache.")

    main_window.set_status_label(f"LOADING \"{_whisper_model}\" MODEL", "orange")
    # Load Whisper model
    device = "cpu" if bool(CONFIG["use_cpu"]) or not torch.cuda.is_available() else "cuda"
    model = whisper.load_model(_whisper_model, download_root=get_absolute_path("whisper_cache/"), in_memory=True, device=device)
    sys.stderr = LogToFile(log, logging.ERROR, LOGFILE)
    use_cpu = True if str(model.device) == "cpu" else False

    # load the speech recognizer and set the initial energy threshold and pause threshold
    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = bool(CONFIG["dynamic_energy_threshold"])
    rec.energy_threshold = int(CONFIG["energy_threshold"])
    rec.pause_threshold = float(CONFIG["pause_threshold"])

    source = sr.Microphone(sample_rate=16000, device_index=int(CONFIG["microphone_index"]) if CONFIG["microphone_index"] else None)
    data_queue = Queue()

    # Initialize OpenVR
    main_window.set_status_label("INITIALIZING OVR", "orange")
    ovr_initialized = False
    try:
        application = openvr.init(openvr.VRApplication_Utility)
        action_path = get_absolute_path("bindings/textboxstt_actions.json")
        appmanifest_path = get_absolute_path("app.vrmanifest")
        openvr.VRApplications().addApplicationManifest(appmanifest_path)
        openvr.VRInput().setActionManifestPath(action_path)
        action_set_handle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
        button_action_handle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
        ovr_initialized = True
        main_window.set_status_label("INITIALZIED OVR", "green")
    except Exception:
        ovr_initialized = False
        main_window.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "red")

    main_window.set_conf_label(CONFIG["osc_ip"], CONFIG["osc_port"], CONFIG["osc_server_port"], ovr_initialized, use_cpu, _whisper_model)
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


def replace_emotes(text):
    if not text:
        return None

    if CONFIG["emotes"] is None:
        return text

    for i in range(len(CONFIG["emotes"])):
        word = CONFIG["emotes"][str(i)]
        if word == "":
            continue
        tmp = re.compile(word, re.IGNORECASE)
        text = tmp.sub(osc.emote_keys[i], text)

    return text


def replace_words(text):
    if not text:
        return None

    text = text.strip()
    if CONFIG["word_replacements"] == {}:
        return text

    for key, value in CONFIG["word_replacements"].items():
        tmp = re.compile(key, re.IGNORECASE)
        text = tmp.sub(value, text)

    text = re.sub(' +', ' ', text)
    return text


def set_typing_indicator(state: bool, textfield: bool = False):
    global use_textbox
    global use_kat
    global use_both
    global osc

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc_client.send_message(VRC_TYPING_PARAM, state)
    if use_kat and osc.isactive and not textfield:
        osc_client.send_message(AV_LISTENING_PARAM, state)


def clear_chatbox():
    global use_textbox
    global use_kat
    global use_both
    global osc

    main_window.clear_textfield()
    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.textbox_target_text = ""
    if use_kat and osc.isactive:
        osc.clear_kat()
    main_window.set_text_label("- No Text -")


def populate_chatbox(text, cutoff: bool = False):
    global main_window
    global use_textbox
    global use_kat
    global use_both
    global osc

    text = replace_words(text)

    if not text:
        return

    if cutoff:
        _chatbox_text = text[-VRC_INPUT_CHARLIMIT:]
        _kat_text = text[-KAT_CHARLIMIT:]
    else:
        _chatbox_text = text[:VRC_INPUT_CHARLIMIT]
        _kat_text = text[:KAT_CHARLIMIT]

    main_window.set_text_label(_chatbox_text)

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.set_textbox_text(_chatbox_text)

    if use_kat and osc.isactive:
        if CONFIG["enable_emotes"]:
            _kat_text = replace_emotes(_kat_text)
        osc.set_kat_text(_kat_text[-KAT_CHARLIMIT:])

    set_typing_indicator(False)


def listen_once():
    global rec

    with source:
        try:
            audio = rec.listen(source, timeout=float(CONFIG["timeout_time"]))
        except sr.WaitTimeoutError:
            return None

        return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def transcribe(torch_audio):
    global use_cpu
    global language
    global model

    use_gpu = not use_cpu
    options = {"without_timestamps": True}
    result = model.transcribe(torch_audio, fp16=use_gpu, language=language, **options)

    return result['text']


def process_loop():
    global data_queue
    global source
    global rec
    global main_window
    global pressed

    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")

    def record_callback(_, audio:sr.AudioData) -> None:
        _data = audio.get_raw_data()
        data_queue.put(_data)

    _stop_listening = rec.listen_in_background(source, record_callback, phrase_time_limit=CONFIG["phrase_time_limit"])

    _time_last = time.time()
    while True:
        if pressed:
            _time_last = time.time()
            _held = False
            while pressed:
                if time.time() - _time_last > CONFIG["hold_time"]:
                    _held = True
                    break
                time.sleep(0.05)
            if _held:
                main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
                play_sound("clear")
                clear_chatbox()
                break
            elif _last_sample == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                play_sound("timeout")
                break
        elif not data_queue.empty():
            while not data_queue.empty():
                data = data_queue.get()
                _last_sample += data

            torch_audio = torch.from_numpy(np.frombuffer(_last_sample, np.int16).flatten().astype(np.float32) / 32768.0)

            _text = transcribe(torch_audio)
                
            _time_last = time.time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time.time() - _time_last > CONFIG["pause_threshold"]:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            print(_text)
            play_sound("finished")
            break
        elif _last_sample == bytes() and time.time() - _time_last > CONFIG["timeout_time"]:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            play_sound("timeout")
            break
        time.sleep(0.05)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    _stop_listening(wait_for_stop=False)
    data_queue.queue.clear()
    time.sleep(1)


def process_once():
    global main_window
    global pressed

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    _torch_audio = listen_once()
    if _torch_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        set_typing_indicator(False)
    else:
        play_sound("donelisten")
        set_typing_indicator(True)
        print(_torch_audio)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _trans = transcribe(_torch_audio)
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound("timeout")
            elif _trans:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_trans)
                play_sound("finished")
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound("timeout")
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout")

    set_typing_indicator(False)
    main_window.set_button_enabled(True)


def get_ovraction_bstate():
    global action_set_handle
    global button_action_handle
    global application

    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = action_set_handle
    openvr.VRInput().updateActionState(_actionsets)
    return bool(openvr.VRInput().getDigitalActionData(button_action_handle, openvr.k_ulInvalidInputValueHandle).bState)


def get_trigger_state():
    global ovr_initialized

    if ovr_initialized and get_ovraction_bstate():
        return True
    else:
        return keyboard.is_pressed(CONFIG["hotkey"])


def handle_input():
    global thread_process
    global held
    global holding
    global pressed
    global curr_time
    global config_ui_open

    pressed = get_trigger_state()

    if thread_process.is_alive() or config_ui_open:
        return
    elif pressed and not holding and not held:
        holding = True
        curr_time = time.time()
    elif pressed and holding and not held:
        holding = True
        if time.time() - curr_time > CONFIG["hold_time"]:
            clear_chatbox()
            main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
            play_sound("clear")
            held = True
            holding = False
    elif not pressed and holding and not held:
        held = True
        holding = False
        thread_process = threading.Thread(target=process_loop if CONFIG["continuous"] else process_once)
        thread_process.start()
    elif not pressed and held:
        held = False
        holding = False


def entrybox_enter_event(text):
    global main_window
    global enter_pressed

    enter_pressed = True
    if text:
        populate_chatbox(text)
        play_sound("finished")
        main_window.clear_textfield()
    else:
        clear_chatbox()
        play_sound("clear")


def textfield_keyrelease(text):
    global osc
    global use_kat
    global enter_pressed

    if not enter_pressed:
        if len(text) > VRC_INPUT_CHARLIMIT:
            main_window.textfield.delete(VRC_INPUT_CHARLIMIT, len(text))
            main_window.textfield.icursor(VRC_INPUT_CHARLIMIT)
        _is_text_empty = text == ""
        set_typing_indicator(not _is_text_empty, True)
        if _is_text_empty:
            clear_chatbox()
        else:
            populate_chatbox(text)
    
    enter_pressed = False


def main_window_closing():
    global main_window
    global config_ui
    global use_kat
    global osc

    print("Closing...")
    if use_kat:
        osc.stop()
    main_window.on_closing()
    if config_ui:
        config_ui.on_closing()


def settings_closing(save=False):
    global osc
    global config_ui
    global config_ui_open

    if save:
        if use_kat:
            osc.stop()
        config_ui.save()
        try:
            init()
        except Exception as e:
            print(e)
            main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO out.log for more info on the error", "red")
    else:
        main_window.set_status_label("SETTINGS NOT SAVED - WAITING FOR INPUT", "#00008b")
    
    main_window.set_button_enabled(True)
    config_ui_open = False
    config_ui.on_closing()


def open_settings():
    global main_window
    global config_ui
    global config_ui_open

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = SettingsWindow(CONFIG, CONFIG_PATH)
    config_ui.button_refresh.configure(command=determine_energy_threshold)
    config_ui.btn_save.configure(command=(lambda: settings_closing(True)))
    config_ui.tkui.protocol("WM_DELETE_WINDOW", settings_closing)
    main_window.set_button_enabled(False)
    config_ui.open()


def determine_energy_threshold():
    global config_ui

    config_ui.set_energy_threshold("Be quiet for 5 seconds...")
    with source:
        rec.adjust_for_ambient_noise(source, 5)
        value = round(rec.energy_threshold)
        config_ui.set_energy_threshold(str(value))


main_window = MainWindow(VERSION)
try:
    init()
except Exception as e:
    print(e)
    main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO out.log for more info on the error", "red")

main_window.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
main_window.textfield.bind("<Return>", (lambda event: entrybox_enter_event(main_window.textfield.get())))
main_window.textfield.bind("<KeyRelease>", (lambda event: textfield_keyrelease(main_window.textfield.get())))
main_window.btn_settings.configure(command=open_settings)
main_window.create_loop(50, handle_input)
main_window.open()
