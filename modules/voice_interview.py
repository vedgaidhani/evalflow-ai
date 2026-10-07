import pyttsx3
import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import os

class VoiceInterview:
    def __init__(self):
        # We only initialize the Speech-to-Text recognizer here now.
        # We DO NOT initialize pyttsx3 here to avoid cross-threading crashes.
        self.recognizer = sr.Recognizer()

    def speak(self, text):
        """Makes your laptop speak safely across Streamlit threads."""
        print(f"🔊 AI SPEAKING: {text}")
        
        # --- THE FIX: Localized Engine Initialization ---
        # By creating the engine inside the function, it binds safely 
        # to Streamlit's current active thread.
        engine = pyttsx3.init()
        engine.setProperty('rate', 160) 
        
        try:
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            # If Streamlit UI refreshes and tries to trigger a double-loop, 
            # this catches the crash and keeps the app running smoothly.
            pass 

    def record_audio_to_file(self, duration=10, filename="temp_interview.wav"):
        """Records from the microphone without PyAudio, using sounddevice."""
        print(f"🎤 RECORDING for {duration} seconds... SPEAK NOW!")
        fs = 44100  # Standard audio sample rate
        
        # Record audio array
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until the recording time is finished
        
        print("✅ RECORDING COMPLETE.")
        # Save array to a .wav file using scipy
        write(filename, fs, recording) 
        return filename

    def transcribe_audio(self, filename="temp_interview.wav"):
        """Reads the .wav file and converts the speech to text."""
        print("🧠 TRANSCRIBING audio...")
        try:
            with sr.AudioFile(filename) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                print(f"📝 TRANSCRIBED: {text}")
                return text
                
        except sr.UnknownValueError:
            return "ERROR: No speech detected or audio was too muffled."
        except sr.RequestError as e:
            return f"ERROR: Could not connect to Google Speech API; {e}"
        finally:
            if os.path.exists(filename):
                os.remove(filename)