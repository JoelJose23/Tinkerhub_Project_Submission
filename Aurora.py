import sounddevice as sd
import numpy as np
import scipy.signal as sps
from groq import Groq
import speech_recognition as sr
import subprocess
from subprocess import *
import time
import pyaudio
import openwakeword
import os
import pywhatkit
from pathlib import Path
import wave
from piper import PiperVoice
import datetime

# === CONFIG ===
DEVICE_INDEX = 4         
TARGET_RATE = 16000        # OpenWakeWord expects 16 kHz

# === INITIALIZE ===
client = Groq(api_key="API_KEY")

# Initialize Piper TTS
VOICE_MODEL_PATH = Path(r"/home/joeljose2306/Work/en_GB-jenny_dioco-medium.onnx") 
voice = PiperVoice.load(VOICE_MODEL_PATH)

# === Helper function to query Groq AI for terminal commands ===
def groq_response(prompt: str):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant responsible for helping do things in an Omarchy distro. "
                    "Provide ONLY a Python list of terminal commands, no explanations, no python written on the top, and no triple quotes, just a list in python. Write one command and only one, as one item in the list. If a command for connecting to a wifi is given always use iwctl for that and copy the exact same name for the wifi in the user prompt do not change it and always put it in double quotes. Whenever there is a prompt to install anything you have to add '--noconfirm' string at the end "
                )
            },
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile"
    )
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content

# === Recognize speech ===
def recognize_speech_optimized():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 1
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Listening... (Speak clearly, timeout in 20 seconds)")
        
        try:
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=10)
            try:
                print("Recognizing..")
                text = recognizer.recognize_google(audio, language="en-in")
                print("You said:", text)
                return text
            except sr.UnknownValueError:
                print("Could not understand audio.")
                return None
            except sr.RequestError as e:
                print(f"API error: {e}. Check your internet connection.")
                return None
        except sr.WaitTimeoutError:
            print("No speech detected within 20 seconds.")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

# === Write commands to terminal ===
def write_in_terminal(commands):
    commands = eval(commands)
    for command in commands:
        print(f"Executing command: {command}")
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                if output == '' and process.poll() is not None:
                    break

            stderr_output = process.stderr.read()
            if stderr_output:
                print("Error:", stderr_output.strip())
            
            print(f"Command finished with exit code {process.returncode}")
        except Exception as e:
            print(f"An error occurred while executing '{command}': {e}")
        print("-" * 20)

# === Speak using Piper ===
def speake(sentence: str):
    with wave.open("reply.wav", "wb") as wav_file:
        voice.synthesize_wav(sentence, wav_file)
    filename = "reply.wav"
    subprocess.run(["aplay", filename])

def churn_out_requests(query: str):
    if "play" in query:
        song = query.replace("play", "")
        speake("Playing"+song)
        pywhatkit.playonyt(song)
    else:
        speake("Let me handle that for you.")
        commands = groq_response(query)
        write_in_terminal(commands)
        speake("All done, Joel!")
        return

def wish_user():
    hour = datetime.datetime.now().hour

    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    elif 18 <= hour < 22:
        greeting = "Good evening"
    else:
        greeting = "Good Night"

    speake(f" {greeting} , Joel! Hope you're having a great day!")

def listen_for_hotword(hotword="aurora"):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎧 Listening for hotword...")

        while True:
            try:
                # Adjust to background noise and listen
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=None)

                # Convert speech to text
                text = recognizer.recognize_google(audio).lower()
                print(f"🗣️ Heard: {text}")

                # Check for the hotword
                if hotword.lower() in text:
                    print(f"✨ Hotword '{hotword}' detected!")
                    return True  # Trigger your assistant

            except sr.UnknownValueError:
                # Speech unintelligible — ignore
                continue
            except sr.RequestError:
                print("⚠️ Network error with Google Speech API")
                break
            except KeyboardInterrupt:
                print("🛑 Stopped listening.")
                break

def aurora_loop():
    """Main continuous conversation loop after hotword detection."""
    wish_user()
    speake("I'm listening, Joel. How can I help you?")

    while True:
        query = recognize_speech_optimized()
        if not query:
            continue

        query = query.lower()
        print(f"🎤 Heard: {query}")

        if "stop" in query or "exit" in query or "goodbye" in query:
            speake("Alright, going silent now. Say 'Aurora' again when you need me.")
            break  # exit to return to hotword detection

        churn_out_requests(query)


# === Main loop for hotword detection ===
if __name__ == "__main__":
    while True:
        print("🎧 Waiting for hotword...")
        if listen_for_hotword("arora"):  # triggers Aurora
            aurora_loop()
