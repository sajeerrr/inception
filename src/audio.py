import queue
import sounddevice as sd
import numpy as np
import noisereduce as nr
import threading
import wave
import os

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk_duration=1.0):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration)
        self.queue = queue.Queue()
        self.running = False
        self.stream = None
        self.noise_profile = None
        
        # We'll use a small buffer to estimate noise profile initially or just use stationary noise reduction
        # For better performance, we'll assume a standard noise reduction strength
        
    def callback(self, indata, frames, time, status):
        """Callback for sounddevice."""
        if status:
            print(status)
        if self.running:
            # Copy the data to avoid issues
            self.queue.put(indata.copy())

    def start(self):
        """Starts the audio recording stream."""
        if self.running:
            return
        
        self.running = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.callback,
            blocksize=self.chunk_size
        )
        self.stream.start()
        print("Audio recording started.")

    def stop(self):
        """Stops the audio recording stream."""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("Audio recording stopped.")

    def get_audio(self):
        """
        Generator that yields available audio chunks.
        This is where we can apply noise reduction.
        """
        while self.running or not self.queue.empty():
            try:
                # Wait for audio, but with a timeout so we can check self.running
                audio_chunk = self.queue.get(timeout=0.5) 
                
                # Apply noise reduction
                # Note: noisereduce is computationally intensive. 
                # Doing it on every chunk might introduce latency.
                # We'll use a fast method or skip if it causes lag.
                # For this demo, let's try stationary noise reduction on the chunk content itself.
                # Ideally, we would capture a 'noise only' profile at startup.
                
                # 1. Volume Gate: DISABLED (Was causing data loss)
                # max_amp = np.max(np.abs(audio_chunk))
                # if max_amp < 0.005: 
                #    reduced_noise_chunk = np.zeros_like(audio_chunk)
                #    yield reduced_noise_chunk
                #    continue

                # 2. Noise Reduction: DISABLED (Was cutting off speech)
                # reduced_noise_chunk = nr.reduce_noise(
                #    y=audio_chunk.flatten(), 
                #    sr=self.sample_rate,
                #    prop_decrease=0.4, 
                #    n_fft=1024,
                #    stationary=True, 
                #    n_jobs=1 
                # )
                
                # yield reduced_noise_chunk
                
                # Pass RAW audio directly to ensure nothing is lost
                yield audio_chunk
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")
                continue

    def save_to_file(self, audio_data, filename="recorded.wav"):
        """Helper to save raw audio data to a file."""
        import scipy.io.wavfile as wav
        wav.write(filename, self.sample_rate, audio_data)
