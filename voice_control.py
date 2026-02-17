import whisper
import sounddevice as sd
import numpy as np
import threading
import time
import re

class VoiceController:
    def __init__(self, model_size = "base", device="cuda", sample_rate=16000, chunk_duration=3):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.voice_command = None
        self.lock = threading.Lock()

        self.model = whisper.load_model(model_size).to(device)
        self.running = False
        self.thread = None

    def start(self):
        #start background listening
        if not self.running:
            self.running = True
            #new thread in bg
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)  #daemon thread closes after program closes
            self.thread.start()
            print("Voice Control started")

    def stop(self):
        self.running = False

    def get_command(self):
        with self.lock:   #only one thread at a time
            command = self.voice_command
            self.voice_command = None    #refresh command
        return command
    
    def _listen_loop(self):
        while self.running:
            recording = sd.rec(int(self.chunk_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
            sd.wait()

            #normalize mic input
            audio = recording.flatten()
            max_val = np.max(np.abs(audio)) + 1e-6
            audio = audio / max_val

            audio = np.pad(audio, (0,1600)) #padding to prevent word cutoff

            result = self.model.transcribe(recording.flatten(), fp16 = True, language = "en", temperature=0)

            # try:
            #     result = self.model.transcribe(audio,fp16=True,language="en",temperature=0)
            # except Exception as e:
            #     print("Whisper Error ", e)
                

            text = result["text"].lower()
            text = re.sub(r'[^a-z\s]', '', text)
            text = text.strip()

            # if text:
            #     print("Heard: ", text)

            detected_command = None

            if "next" in text or "next slide" in text:
                detected_command = "next"

            elif "back" in text or "previous slide" in text or "go back" in text:
                detected_command = "previous"

            elif "red" in text or "red pen " in text:
                detected_command = "red"

            elif "blue" in text or "blue pen " in text:
                detected_command = "blue"

            elif "green" in text or "green pen " in text:
                detected_command = "green"

            elif "start drawing" in text:
                detected_command = "start"

            elif "stop drawing" in text:
                detected_command = "stop"

            elif "resize" in text:
                detected_command = "resize"

            elif "clear" in text:
                detected_command = "clear"

            elif "alert" in text:
                detected_command = "posture"

            if detected_command:
                with self.lock:
                    self.voice_command = detected_command

            

