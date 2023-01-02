import speech_recognition as sr
import whisper
import torch
import numpy as np
from pythonosc import udp_client
import json
import winsound
import warnings
import os
import sys
import openvr
import time
import traceback
from colorama import Fore

warnings.filterwarnings("ignore", category=UserWarning)

VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/STTListen"

def cls():
    """Clears Console"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def play_ping():
    """Plays a ping sound."""
    winsound.PlaySound('ping.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

config = json.load(open(get_absolute_path('config.json')))

oscClient = udp_client.SimpleUDPClient(config["IP"], int(config["Port"]))

model = config["model"].lower()
lang = config["language"].lower()
is_english = lang == "english"

if model != "large" and is_english:
        model = model + ".en"
audio_model = whisper.load_model(model);

#load the speech recognizer and set the initial energy threshold and pause threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = bool(config["dynamic_energy_threshold"])
r.energy_threshold = int(config["energy_threshold"])
r.pause_threshold = float(config["pause_threshold"])

application = openvr.init(openvr.VRApplication_Utility)
action_path = get_absolute_path("textboxstt_actions.json")
appmanifest_path = get_absolute_path("app.vrmanifest")

openvr.VRApplications().addApplicationManifest(appmanifest_path)
openvr.VRInput().setActionManifestPath(action_path)
actionSetHandle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
buttonactionhandle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)


def record_and_transcribe():
    with sr.Microphone(sample_rate=16000) as source:
        print(Fore.LIGHTCYAN_EX + "RECORDING")
        play_ping()
        audio = r.listen(source)

        torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)

        print(Fore.LIGHTCYAN_EX + "TRANSCRIBING")
        if lang:
            result = audio_model.transcribe(torch_audio, language=lang)
        else:
            result = audio_model.transcribe(torch_audio)

        return result["text"]


def send_message():
    oscClient.send_message(VRC_TYPING_PARAM, True)
    trans = record_and_transcribe()
    print(Fore.YELLOW + "-" + trans)
    print(Fore.LIGHTCYAN_EX + "POPULATING TEXTBOX")
    oscClient.send_message(VRC_INPUT_PARAM, [trans, True, True])
    oscClient.send_message(VRC_TYPING_PARAM, False)


def clear_chatbox():
    print(Fore.LIGHTCYAN_EX + "CLEARING OSC TEXTBOX")
    oscClient.send_message(VRC_INPUT_PARAM, ["", True])
    oscClient.send_message(VRC_TYPING_PARAM, False)


def get_action_bstate():
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(_actionsets)
    return bool(openvr.VRInput().getDigitalActionData(buttonactionhandle, openvr.k_ulInvalidInputValueHandle).bState)


def handle_input():
    """Handles the OpenVR Input"""
    global held
    # Set up OpenVR events and Action sets
    
    pressed = get_action_bstate()
    curr_time = time.time()

    if pressed and not held:
        while pressed:
            if time.time() - curr_time > 1.5:
                clear_chatbox()
                print(Fore.LIGHTBLUE_EX + "WAITING")
                held = True
                break
            pressed = get_action_bstate()
            time.sleep(0.05)
        if not held:
            send_message()
            print(Fore.LIGHTBLUE_EX + "WAITING")
    elif held and not pressed:
        held = False


held = False
print(Fore.GREEN + "-INITIALZIED-")
print(Fore.LIGHTBLUE_EX + "WAITING")
# Main Loop
while True:
    try:
        handle_input()
        time.sleep(0.05)
    except KeyboardInterrupt:
        cls()
        sys.exit()
    except Exception:
        cls()
        print("UNEXPECTED ERROR\n")
        print("Please Create an Issue on GitHub with the following information:\n")
        traceback.print_exc()
        input("\nPress ENTER to exit")
        sys.exit()