import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import time
import numpy as np
import soundfile as sf
import os
import gc


# Import our modules
from src.audio import AudioRecorder
from src.stt import SpeechRecognizer
from src.translator import OfflineTranslator
from src.threat import ThreatDetector
from src.corrector import GrammarCorrector

class ProcessingPopup:
    def __init__(self, parent, filename):
        self.top = tk.Toplevel(parent)
        self.top.title("Processing File")
        self.top.geometry("400x150")
        self.top.resizable(False, False)
        # Make it modal-like
        self.top.transient(parent)
        self.top.grab_set()
        
        # Center status
        self.lbl_status = tk.Label(self.top, text=f"Loading {filename}...", font=("Helvetica", 11, "bold"))
        self.lbl_status.pack(pady=(20, 10))
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.top, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=30, pady=10)
        
        # Detail label
        self.lbl_detail = tk.Label(self.top, text="Initializing...", font=("Helvetica", 9), fg="gray")
        self.lbl_detail.pack(pady=5)

    def update_progress(self, percent, status_text):
        self.progress_var.set(percent)
        self.lbl_detail.config(text=status_text)
        if percent >= 100:
            self.lbl_status.config(text="Complete!")
            self.top.after(1000, self.close) # Auto close after 1s
    
    def close(self):
        self.top.destroy()


class TranslaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI4Bharat - Offline AI System")
        self.root.geometry("1000x700")
        
        # Data & State
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.processing_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Initialize Modules
        self.status_var = tk.StringVar(value="Initializing AI Models... Please wait.")
        
        # UI Setup
        self._setup_ui()
        
        # Start initialization thread
        threading.Thread(target=self._initialize_modules, daemon=True).start()

    def _setup_ui(self):
        # Styles
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10)
        style.configure("TLabel", font=("Helvetica", 11))
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_lbl = tk.Label(header_frame, text="AI4BHARAT", font=("Arial", 24, "bold"), bg="#2c3e50", fg="white")
        header_lbl.pack(pady=20)
        
        # Status Bar
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, bg="#ecf0f1", fg="#333")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main Content
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controls
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.btn_record = tk.Button(controls_frame, text="Start Recording", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), command=self.toggle_recording, state=tk.DISABLED)
        self.btn_record.pack(side=tk.LEFT, padx=5)
        
        self.btn_upload = tk.Button(controls_frame, text="Upload Audio", bg="#2980b9", fg="white", font=("Arial", 12, "bold"), command=self.upload_file, state=tk.DISABLED)
        self.btn_upload.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(controls_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Threat Indicator
        self.threat_frame = tk.Frame(controls_frame, bg="green", width=30, height=30)
        self.threat_frame.pack(side=tk.RIGHT, padx=10)
        self.threat_label = tk.Label(controls_frame, text="Safe", font=("Arial", 12, "bold"), fg="green")
        self.threat_label.pack(side=tk.RIGHT)
 
        # Output Areas
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Col 1: Original (Kashmiri)
        frame_ks = ttk.LabelFrame(paned, text="Original (Kashmiri)", padding=5)
        paned.add(frame_ks, weight=1)
        self.txt_ks = scrolledtext.ScrolledText(frame_ks, font=("Segoe UI", 12), height=15)
        self.txt_ks.pack(fill=tk.BOTH, expand=True)

        # Col 2: English
        frame_en = ttk.LabelFrame(paned, text="English Translation", padding=5)
        paned.add(frame_en, weight=1)
        self.txt_en = scrolledtext.ScrolledText(frame_en, font=("Segoe UI", 12), height=15)
        self.txt_en.pack(fill=tk.BOTH, expand=True)
        
        # Col 3: Hindi (REMOVED as per user request)
        # frame_hi = ttk.LabelFrame(paned, text="Hindi Translation", padding=5)
        # paned.add(frame_hi, weight=1)
        # self.txt_hi = scrolledtext.ScrolledText(frame_hi, font=("Segoe UI", 12), height=15)
        # self.txt_hi.pack(fill=tk.BOTH, expand=True)

    def _initialize_modules(self):
        try:
            self.recorder = AudioRecorder(chunk_duration=1.0)
            
            self.status_var.set("Loading Speech Recognition Model (Small)...")
            self.status_var.set("Loading Speech Recognition Model (Medium)...")
            self.stt = SpeechRecognizer(model_size="medium")
            
            self.status_var.set("Loading Threat Detector...")
            self.threat_detector = ThreatDetector()
            
            self.status_var.set("Loading Translator...")
            self.translator = OfflineTranslator()
            
            self.status_var.set("Loading Grammar Corrector...")
            self.corrector = GrammarCorrector()
            
            self.status_var.set("Ready.")
            self.root.after(0, lambda: self.btn_record.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_upload.config(state=tk.NORMAL))
            
        except Exception as e:
            self.status_var.set(f"Error initializing: {e}")
            print(e)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.btn_record.config(text="Stop Recording", bg="#c0392b")
        self.status_var.set("Recording...")
        
        # Clear text areas at start
        self.txt_ks.delete("1.0", tk.END)
        self.txt_en.delete("1.0", tk.END)
        # self.txt_hi.delete("1.0", tk.END)
        
        self.recorder.start()
        
        self.stop_event.clear()
        threading.Thread(target=self._process_queue_loop, daemon=True).start()

    def stop_recording(self):
        self.is_recording = False
        self.btn_record.config(text="Start Recording", bg="#27ae60")
        self.status_var.set("Stopping...")
        self.recorder.stop()
        self.stop_event.set()
        self.status_var.set("Ready.")

    def _process_queue_loop(self):
        """
        Consumes audio from recorder and processes it.
        """
        buffer_seconds = 4
        buffer_size = int(self.recorder.sample_rate * buffer_seconds)
        current_buffer = [] 
        
        for audio_chunk in self.recorder.get_audio():
            # print(f"DEBUG: Rx chunk {len(audio_chunk)}")
            if self.stop_event.is_set() and not self.is_recording:
                break
            
            current_buffer.append(audio_chunk)
            
            total_samples = sum(len(c) for c in current_buffer)
            if total_samples >= buffer_size:
                full_audio = np.concatenate(current_buffer)
                # print(f"DEBUG: Processing buffer size {len(full_audio)}", flush=True)
                self.process_audio_data(full_audio)
                current_buffer = []

        if current_buffer:
             full_audio = np.concatenate(current_buffer)
             self.process_audio_data(full_audio)

    def upload_file(self):
        # Added support for OGA, OGG, FLAC, M4A, AAC as per request
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.oga *.ogg *.flac *.m4a *.aac *.wma")])
        if filepath:
            filename = os.path.basename(filepath)
            self.status_var.set(f"Queueing {filename}...")
            # Start thread
            threading.Thread(target=self._process_file, args=(filepath,), daemon=True).start()

    def _process_file(self, filepath):
        """Starts the file processing pipeline."""
        filename = os.path.basename(filepath)
        self.status_var.set(f"Queueing {filename}...")
        
        # Reset queue
        self.processing_queue = queue.Queue()
        self.stop_event.clear()
        
        # Show Popup
        self.root.after(0, lambda: self._show_popup(filename))
        
        # Start Consumer Thread (AI Processing)
        threading.Thread(target=self._file_consumer_loop, args=(filename,), daemon=True).start()
        
        # Start Producer Thread (File Reading & Resampling)
        threading.Thread(target=self._file_producer, args=(filepath,), daemon=True).start()

    def _file_producer(self, filepath):
        """
        Producer: Reads file, resamples, puts blocks into queue.
        Fast operation, mainly disk I/O and numpy math.
        """
        try:
            filename = os.path.basename(filepath)
            
            # Clear text areas at start
            self.root.after(0, lambda: self.txt_ks.delete("1.0", tk.END))
            self.root.after(0, lambda: self.txt_en.delete("1.0", tk.END))
            # self.root.after(0, lambda: self.txt_hi.delete("1.0", tk.END))

            with sf.SoundFile(filepath) as f:
                samplerate = f.samplerate
                total_frames = f.frames
                
                TARGET_SR = 16000
                seconds_per_block = 5
                frames_per_block = int(samplerate * seconds_per_block)
                
                # Pre-calculate progress reporting interval to avoid flooding UI
                processed_frames = 0
                
                for block in f.blocks(blocksize=frames_per_block, dtype='float32'):
                    if self.stop_event.is_set():
                        break
                        
                    if len(block.shape) > 1:
                        block = block.mean(axis=1)
                    
                    if samplerate != TARGET_SR:
                        number_of_samples = round(len(block) * float(TARGET_SR) / samplerate)
                        # Linear Interpolation (Fast)
                        x_old = np.linspace(0, len(block), num=len(block), endpoint=False)
                        x_new = np.linspace(0, len(block), num=number_of_samples, endpoint=False)
                        block = np.interp(x_new, x_old, block)
                        block = block.astype(np.float32)
                    
                    # Compute progress
                    percent = min(int((f.tell() / total_frames) * 100), 100)
                    
                    # Put data in queue for Consumer
                    self.processing_queue.put((block, percent))
                    
            # Signal end of file
            self.processing_queue.put(None)
            
            # Memory Cleanup for producer resources
            del f
            gc.collect()

        except Exception as e:
            print(f"Producer error: {e}")
            self.status_var.set(f"Read error: {e}")
            # Ensure consumer stops
            self.processing_queue.put(None)

    def _file_consumer_loop(self, filename):
        """
        Consumer: Takes blocks from queue, runs STT (Slow).
        """
        try:
            self.status_var.set(f"Processing {filename}...")
            
            while True:
                if self.stop_event.is_set():
                    break
                    
                item = self.processing_queue.get()
                
                if item is None:
                    break # End of file
                
                audio_block, percent = item
                
                # Update Status
                self.status_var.set(f"Translating {filename}... {percent}%")
                self.root.after(0, lambda p=percent: self.progress_var.set(p))
                self.root.after(0, lambda p=percent: self._update_popup(p, f"Processed {p}%"))
                
                # Heavy Processing
                self.process_from_array(audio_block)
                
                # Minor cleanup after each chunk
                gc.collect()
            
            self.status_var.set("File processing complete.")
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self._update_popup(100, "Done"))

        except Exception as e:
            print(f"Consumer error: {e}")
            self.status_var.set(f"Process error: {e}")

    # GUI Helpers
    def _show_popup(self, filename):
        self.processing_popup = ProcessingPopup(self.root, filename)

    def _update_popup(self, percent, text):
        if hasattr(self, 'processing_popup') and self.processing_popup.top.winfo_exists():
            self.processing_popup.update_progress(percent, text)

    def process_from_array(self, audio_data):
        if len(audio_data) < 3200:
            return

        # 1. Kashmiri (AI4Bharat ASR)
        segments, _ = self.stt.transcribe(audio_data, language=None)
        
        full_ks = []
        full_en = []
        full_hi = []

        for s in segments:
            text_ks = s.text.strip()
            if not text_ks:
                continue
                
            full_ks.append(text_ks)
        
            # 2. English (NLLB Translation from Kashmiri)
            text_en = self.translator.translate(text_ks, "ks", "en")
            full_en.append(text_en)
            
            # 3. Hindi (NLLB Translation from Kashmiri) - REMOVED
            # text_hi = self.translator.translate(text_ks, "ks", "hi")
            # full_hi.append(text_hi)

            self.check_threats(text_en)

        if full_ks:
            self.update_text(self.txt_ks, " ".join(full_ks) + "\n")
            self.update_text(self.txt_en, " ".join(full_en) + "\n")
            # self.update_text(self.txt_hi, " ".join(full_hi) + "\n")
            
            self.check_threats(" ".join(full_ks))


    def process_audio_data(self, audio_data):
        if len(audio_data) < 3200:
            return

        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 1.0: 
             audio_data = audio_data / 32768.0 
        
        # print(f"DEBUG: calling process_from_stream_chunk max={np.max(np.abs(audio_data))}", flush=True)
        self.process_from_stream_chunk(audio_data)

    def process_from_stream_chunk(self, audio_data):
        if len(audio_data) < 3200:
            return

        # 1. Recognize Kashmiri
        segments, _ = self.stt.transcribe(audio_data, language=None)
        
        for s in segments:
            text_ks = s.text.strip()
            if text_ks:
                self.update_text(self.txt_ks, text_ks + " ")
                self.check_threats(text_ks)
                
                # 2. Translate to English (NLLB)
                raw_en = self.translator.translate(text_ks, "ks", "en")
                
                # 3. Post-Edit for Grammar & Flow (T5)
                final_en = self.corrector.correct(raw_en)
                
                self.update_text(self.txt_en, final_en + " ")
                self.check_threats(final_en)
                
                # 3. Translate to Hindi (NLLB) - REMOVED
                # text_hi = self.translator.translate(text_ks, "ks", "hi")
                # self.update_text(self.txt_hi, text_hi + " ")

    def update_text(self, widget, text):
        self.root.after(0, lambda: widget.insert(tk.END, text))
        self.root.after(0, lambda: widget.see(tk.END))

    def check_threats(self, text):
        is_threat, words = self.threat_detector.detect(text)
        if is_threat:
            self.root.after(0, lambda: self._trigger_alert(words))
        else:
             self.root.after(0, lambda: self._clear_alert())

    def _trigger_alert(self, words):
        self.threat_frame.config(bg="red")
        self.threat_label.config(text=f"THREAT DETECTED: {', '.join(words)}", fg="red")
        
    def _clear_alert(self):
        pass
