import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
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

# Set Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProcessingPopup(ctk.CTkToplevel):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.title("Processing File")
        self.geometry("400x180")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.lbl_status = ctk.CTkLabel(self, text=f"Loading {filename}...", font=("Roboto", 16, "bold"))
        self.lbl_status.pack(pady=(20, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress = ctk.CTkProgressBar(self, variable=self.progress_var)
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.set(0)
        
        self.lbl_detail = ctk.CTkLabel(self, text="Initializing...", font=("Roboto", 12), text_color="gray")
        self.lbl_detail.pack(pady=5)

    def update_progress(self, percent, status_text):
        self.progress_var.set(percent / 100) # CTk progress is 0.0 to 1.0
        self.lbl_detail.configure(text=status_text)
        if percent >= 100:
            self.lbl_status.configure(text="Complete!")
            self.after(1000, self.destroy)

class TranslaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inception - Advanced Translator")
        self.root.geometry("1100x750")
        
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
        # Main Layout: Grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0) # Header
        self.root.grid_rowconfigure(1, weight=1) # Main Content
        self.root.grid_rowconfigure(2, weight=0) # Status Bar

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#1a1a1a")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_lbl = ctk.CTkLabel(self.header_frame, text="INCEPTION AI", font=("Montserrat", 24, "bold"), text_color="#3498db")
        self.header_lbl.pack(pady=15, padx=20, side="left")
        
        self.subtitle_lbl = ctk.CTkLabel(self.header_frame, text="Kashmiri -> English Real-time Translation", font=("Roboto", 12))
        self.subtitle_lbl.pack(pady=20, padx=10, side="left")

        # 2. Main Content
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0) # Controls
        self.main_frame.grid_rowconfigure(1, weight=1) # Text Areas

        # Controls Area
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Record Button
        self.btn_record = ctk.CTkButton(self.controls_frame, text="Start Recording", command=self.toggle_recording, 
                                      font=("Roboto", 14, "bold"), fg_color="#2ecc71", hover_color="#27ae60",
                                      height=40, state="disabled")
        self.btn_record.pack(side="left", padx=15, pady=15)
        
        # Visualizer Canvas (LED)
        self.viz_canvas = tk.Canvas(self.controls_frame, width=20, height=20, bg=self.controls_frame._apply_appearance_mode(self.controls_frame._fg_color), highlightthickness=0)
        self.viz_canvas.pack(side="left", padx=5)
        self.viz_indicator = self.viz_canvas.create_oval(2, 2, 18, 18, fill="gray", outline="")

        # Upload Button
        self.btn_upload = ctk.CTkButton(self.controls_frame, text="Upload Audio", command=self.upload_file,
                                      font=("Roboto", 14, "bold"), fg_color="#3498db", hover_color="#2980b9",
                                      height=40, state="disabled")
        self.btn_upload.pack(side="left", padx=15, pady=15)
        
        # Threat Indicator
        self.threat_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.threat_frame.pack(side="right", padx=15)
        self.threat_lbl = ctk.CTkLabel(self.threat_frame, text="SAFE", font=("Roboto", 14, "bold"), text_color="#2ecc71")
        self.threat_lbl.pack(side="right")
        self.threat_icon = ctk.CTkLabel(self.threat_frame, text="🛡️", font=("Roboto", 20))
        self.threat_icon.pack(side="right", padx=5)

        # Text Areas (Split)
        
        # Left: Original
        self.frame_ks = ctk.CTkFrame(self.main_frame)
        self.frame_ks.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.frame_ks, text="Original (Kashmiri)", font=("Roboto", 14, "bold")).pack(pady=10)
        self.txt_ks = ctk.CTkTextbox(self.frame_ks, font=("Segoe UI", 16))
        self.txt_ks.pack(fill="both", expand=True, padx=10, pady=10)

        # Right: English
        self.frame_en = ctk.CTkFrame(self.main_frame)
        self.frame_en.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(self.frame_en, text="English Translation", font=("Roboto", 14, "bold")).pack(pady=10)
        self.txt_en = ctk.CTkTextbox(self.frame_en, font=("Segoe UI", 16))
        self.txt_en.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Status Bar
        self.status_bar = ctk.CTkLabel(self.root, textvariable=self.status_var, height=30, anchor="w", padx=10, fg_color="#2c3e50")
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _initialize_modules(self):
        try:
            self.recorder = AudioRecorder(chunk_duration=1.0)
            
            self.status_var.set("Loading Speech Recognition Model...")
            self.stt = SpeechRecognizer(model_size="medium")
            
            self.status_var.set("Loading Threat Detector...")
            self.threat_detector = ThreatDetector()
            
            self.status_var.set("Loading Translator...")
            self.translator = OfflineTranslator()
            
            self.status_var.set("Loading Grammar Corrector...")
            self.corrector = GrammarCorrector()
            
            self.status_var.set("Ready.")
            # Enable buttons on main thread
            self.root.after(0, lambda: self.btn_record.configure(state="normal"))
            self.root.after(0, lambda: self.btn_upload.configure(state="normal"))
            
        except Exception as e:
            self.status_var.set(f"Error initializing: {e}")
            print(f"Init Error: {e}")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.btn_record.configure(text="Stop Recording", fg_color="#e74c3c", hover_color="#c0392b")
        self.status_var.set("Recording...")
        
        # Clear
        self.txt_ks.delete("1.0", "end")
        self.txt_en.delete("1.0", "end")
        
        self.recorder.start()
        
        self.stop_event.clear()
        threading.Thread(target=self._process_queue_loop, daemon=True).start()
        
        self._animate_recording()

    def stop_recording(self):
        self.is_recording = False
        self.btn_record.configure(text="Start Recording", fg_color="#2ecc71", hover_color="#27ae60")
        self.status_var.set("Stopping...")
        
        # Reset LED
        self.viz_canvas.itemconfig(self.viz_indicator, fill="gray")
        
        self.recorder.stop()
        self.stop_event.set()
        self.status_var.set("Ready.")

    def _animate_recording(self):
        if self.is_recording:
            current_color = self.viz_canvas.itemcget(self.viz_indicator, "fill")
            next_color = "#e74c3c" if current_color == "gray" else "gray" # Red pulse
            self.viz_canvas.itemconfig(self.viz_indicator, fill=next_color)
            self.root.after(500, self._animate_recording)
        else:
            self.viz_canvas.itemconfig(self.viz_indicator, fill="gray")

    def _process_queue_loop(self):
        buffer_seconds = 8 # Increased to capture full sentences better
        current_buffer = [] 
        self.full_session_audio = [] 
        
        for audio_chunk in self.recorder.get_audio():
            print(f"DEBUG: Rx chunk {len(audio_chunk)}", flush=True)
            if self.stop_event.is_set() and not self.is_recording:
                break
            
            current_buffer.append(audio_chunk)
            self.full_session_audio.append(audio_chunk)
        
            total_samples = sum(len(c) for c in current_buffer)
            if total_samples >= self.recorder.sample_rate * buffer_seconds:
                full_audio = np.concatenate(current_buffer)
                print(f"DEBUG: Processing buffer size {len(full_audio)}", flush=True)
                self.process_audio_data(full_audio)
                current_buffer = []

        if current_buffer:
             full_audio = np.concatenate(current_buffer)
             self.process_audio_data(full_audio)
             
        # Ask to save
        if self.full_session_audio:
            self.root.after(0, self.prompt_save_recording)

    def prompt_save_recording(self):
        try:
            full_data = np.concatenate(self.full_session_audio)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")],
                title="Save Recording?"
            )
            if save_path:
                import scipy.io.wavfile as wav
                wav.write(save_path, self.recorder.sample_rate, full_data)
                self.status_var.set(f"Saved recording to {os.path.basename(save_path)}")
            self.full_session_audio = []
        except Exception as e:
            print(f"Error saving: {e}")
            messagebox.showerror("Save Error", f"Could not save recording: {e}")

    def upload_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.oga *.ogg *.flac *.m4a *.aac *.wma")])
        if filepath:
            filename = os.path.basename(filepath)
            self.status_var.set(f"Queueing {filename}...")
            
            popup = ProcessingPopup(self.root, filename)
            
            threading.Thread(target=self._process_file, args=(filepath, popup), daemon=True).start()

    def _process_file(self, filepath, popup):
        try:
            popup.update_progress(10, "Reading audio file...")
            data, samplerate = sf.read(filepath)
            
            # Convert to mono 16kHz
            if len(data.shape) > 1:
                data = data.mean(axis=1)
                
            if samplerate != 16000:
                import scipy.signal
                number_of_samples = round(len(data) * float(16000) / samplerate)
                data = scipy.signal.resample(data, number_of_samples)
                
            popup.update_progress(40, "Transcribing Audio...")
            self.root.after(0, lambda: self.txt_ks.delete("1.0", "end"))
            self.root.after(0, lambda: self.txt_en.delete("1.0", "end"))
                
            # Process in 30-second chunks to ensure full transcription
            CHUNK_DURATION_S = 30
            chunk_samples = 16000 * CHUNK_DURATION_S
            total_samples = len(data)
            
            for i in range(0, total_samples, chunk_samples):
                chunk = data[i : i + chunk_samples]
                
                # Update progress
                progress = 40 + int((i / total_samples) * 60)
                popup.update_progress(progress, f"Transcribing {i//16000}s - {(i+len(chunk))//16000}s...")
                
                self.process_audio_data(chunk)
            
            popup.update_progress(100, "Done!")
            self.status_var.set(f"Finished processing {os.path.basename(filepath)}")
            
        except Exception as e:
            print(f"Error processing file: {e}")
            popup.destroy()
            messagebox.showerror("Error", f"Failed to process file: {e}")

    def process_audio_data(self, audio_data):
        if len(audio_data) < 3200:
            return
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 1.0: 
             audio_data = audio_data / 32768.0 
        self.process_from_stream_chunk(audio_data)

    def process_from_stream_chunk(self, audio_data):
        # 1. Recognize Kashmiri
        segments, _ = self.stt.transcribe(audio_data, language=None)
        
        for s in segments:
            text_ks = s.text.strip()
            if text_ks:
                self.update_text(self.txt_ks, text_ks + " ")
                self.check_threats(text_ks)
                
                # 2. Translate to English (NLLB)
                raw_en = self.translator.translate(text_ks, "ks", "en")
                
                # 3. Post-Edit (Grammar)
                final_en = self.corrector.correct(raw_en)
                
                self.update_text(self.txt_en, final_en + " ")
                self.check_threats(final_en)

    def update_text(self, widget, text):
        self.root.after(0, lambda: widget.insert("end", text))
        self.root.after(0, lambda: widget.see("end"))

    def check_threats(self, text):
        is_threat, words = self.threat_detector.detect(text)
        if is_threat:
            self.root.after(0, lambda: self._trigger_alert(words))
        else:
             self.root.after(0, lambda: self._clear_alert())

    def _trigger_alert(self, words):
        self.threat_lbl.configure(text=f"THREAT: {', '.join(words)}", text_color="red")
        self.threat_icon.configure(text="⚠️", text_color="red")
        
    def _clear_alert(self):
        self.threat_lbl.configure(text="SAFE", text_color="#2ecc71")
        self.threat_icon.configure(text="🛡️", text_color="#2ecc71")
