# VRCTextboxSTT
A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) to transcribe audio and send that information to VRChats textbox system over OSC.

To make the program listen, you either have to press the button that is configured in the ***config.json*** file. ***F1 by default*** <br>
In VR, press the Left Controllers ***A Button*** for **Valve Index**, and the ***X-Button*** on **Oculus/Meta** respectively. <br>
Holding that button for 1.5 seconds will clear the chatbox.

First startup will take longer, as it will download the configured language model. After that it will start up faster. <br>
More to that under [#Configuration](https://github.com/I5UCC/VRCTextboxSTT#configuration)

# [Download Here](https://github.com/I5UCC/VRCTextboxSTT/releases/download/v0.1/TextboxSTTv0.1.7z)

# Demo

[soon TM]

# Configuration
Configuration of this program is located in the ***config.json*** file:

| Option | Values | Default | Explanation |
|:------:|:------:|:-------:|:-----------:|
| "IP" | Any IP-Adress | "127.0.0.1" | IP to send the OSC information to. |
| "Port" | Any Port | 9000 | Port to send the OSC information to. |
| "model" | "tiny", "base", "small", "medium", "large" | base | What model of whisper to use. I'd recommend not going over "base" as it will significantly impact the performance |
| "language" | "english", "german", "spanish", "" | english | Language to use, "english" will be faster then other languages. Leaving it empty "", will let the program decide what language you are speaking. |
| "dynamic_energy_threshold" | true, false | false | With dynamic_energy_threshold set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time. I'd recommend setting the 'energy_threshold' value high when enabling this setting. |
| "energy_threshold" | 0-3500 | 200 | Under 'ideal' conditions (such as in a quiet room), values between 0 and 100 are considered silent or ambient, and values 300 to about 3500 are considered speech. |
| "pause_threshold" | 0.0-10.0 | 0.8 | Amount of seconds to wait when current energy is under the 'energy_threshold' |
| "record_hotkey" | Any key supported by the [python keyboard library](https://github.com/boppreh/keyboard) | F1 | The key that is used to trigger listening. |
| "clear_hotkey" | Any key supported by the [python keyboard library](https://github.com/boppreh/keyboard) | F2 | The key that is used to trigger clearning the chatbox. |

# Modifying the bind for SteamVR
You can set the boolean "sttlisten" in the Binding UI of SteamVR. Anyone who has set up OpenVR-Advanced-Settings might be familiar with that.
You can set it to any action that supports a boolean input. By default it is the left A button (X button on Oculus/Meta respectively).
![image](https://user-images.githubusercontent.com/43730681/210201138-d60d0936-22e5-4845-bbc1-4d1b0c412c43.png)

# Automatic launch with SteamVR
On first launch of the program, it registers as an Overlay app on SteamVR just like other well known programs like XSOverlay or OVRAdvancedSettings and can be launched on startup:
![Screenshot 2022-12-04 184629](https://user-images.githubusercontent.com/43730681/205506892-0927ed45-69c6-480f-b4b3-bc02d89c151e.png) <br>
![Screenshot 2023-01-02 084823](https://user-images.githubusercontent.com/43730681/210209107-746196dd-7e19-47c4-a668-221824d44a4e.png)

After setting the option to ON it will launch the program on SteamVR startup.
