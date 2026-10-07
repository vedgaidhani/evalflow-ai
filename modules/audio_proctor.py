import sounddevice as sd
import numpy as np
import threading
import time

class AudioProctor:
    _active_instance = None

    def __init__(self):
        # Singleton cleanup for zombie audio threads
        if AudioProctor._active_instance is not None:
            print("♻️ PROCTOR: Cleaning up zombie audio thread...")
            AudioProctor._active_instance.running = False
            time.sleep(0.5)

        AudioProctor._active_instance = self
        self.running = False
        self.audio_strikes = 0
        
        # Audio Configuration
        self.RATE = 44100
        self.CHUNK = 1024
        
        # Sounddevice measures volume between 0.0 and 1.0 (instead of 0 to 32000)
        # 0.01 is a quiet whisper. 0.05 is normal talking.
        self.SILENCE_THRESHOLD = 0.02 

    def start_proctoring(self):
        if not self.running:
            print("\n▶️ PROCTOR: Starting Audio Monitoring thread (Native SoundDevice)...")
            self.running = True
            self.audio_strikes = 0
            threading.Thread(target=self._audio_loop, daemon=True).start()

    def stop_proctoring(self):
        print("⏹️ PROCTOR: Stopping Audio Monitoring thread...")
        self.running = False
        time.sleep(0.5)
        # roughly 43 chunks = 1 second of audio
        penalty_seconds = self.audio_strikes // 43
        return penalty_seconds

    def _audio_callback(self, indata, frames, time_info, status):
        # This function is called automatically every time the mic captures a chunk of sound
        if self.running:
            # Calculate the volume (Root Mean Square)
            rms_volume = np.sqrt(np.mean(np.square(indata)))
            
            if rms_volume > self.SILENCE_THRESHOLD:
                print(f"⚠️ AUDIO ALERT: Whisper/Speech detected! (Level: {rms_volume:.4f})")
                self.audio_strikes += 1

    def _audio_loop(self):
        print("🎤 THREAD: Initializing Microphone...")
        try:
            # Open the microphone stream in the background
            with sd.InputStream(samplerate=self.RATE, channels=1, callback=self._audio_callback, blocksize=self.CHUNK):
                print("🎤 THREAD: Microphone Active! Listening for whispers...")
                
                # Keep the thread alive while the callback function listens
                while self.running:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"\n🚨 AUDIO THREAD CRASH: {e}\n")
            
        finally:
            print("🎤 THREAD: Releasing Microphone...")