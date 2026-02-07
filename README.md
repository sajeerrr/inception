# 🎙️ Translater – Offline Kashmiri Live Speech Translation System

A modern **Python-based AI Desktop Application** that performs **live Kashmiri speech-to-English translation**, running **completely offline**, **free**, and **without any paid API keys**.  
Designed for **college projects, hackathons, research demos, portfolios, and low-connectivity environments**.

---

## 🚀 Features

### 🎧 Users
- Speak Kashmiri through a microphone
- Live Kashmiri transcription
- Live English translation
- Simple, clean desktop interface
- Supports long audio file uploads

### 🧠 AI Capabilities
- Offline Kashmiri Speech Recognition (ASR)
- Kashmiri → English translation
- AI-based English grammar & meaning correction
- No internet required after initial setup
- Fast, private, and secure processing

### ⚙️ Core Functionality
- Real-time audio capture
- Noise reduction & voice activity detection (VAD)
- Chunk-based / streaming transcription
- Post-editing AI for fluent English output
- Fully local AI processing pipeline

---

## 🧠 System Architecture

### 🔹 High-Level Architecture (Text Flow)

Microphone Input  
│  
▼  
Audio Preprocessing  
• Resampling (16kHz)  
• Mono Conversion  
• Noise Reduction / VAD  
│  
▼  
Speech-to-Text (ASR Engine)  
• Meta MMS (facebook/mms-1b-all)  
  OR  
• AI4Bharat IndicConformer (Kashmiri)  
• Fully Offline  
│  
▼  
Kashmiri Text  
│  
▼  
Offline Translation Engine  
• MarianMT / NLLB / Argos Translate  
• Kashmiri → English  
│  
▼  
Raw English Translation  
│  
▼  
AI Grammar & Meaning Correction  
• Flan-T5 (Grammar + Meaning Fix)  
│  
▼  
Final English Output  
• Live Desktop GUI  

---

## 🛠 Tech Stack

### Desktop Application
- Python 3.10+
- Tkinter / CustomTkinter

### Speech Recognition (ASR)
- Meta MMS (Massively Multilingual Speech)
- AI4Bharat IndicConformer (Kashmiri)

### Translation
- MarianMT (Helsinki-NLP)
- NLLB (optional)
- Argos Translate (offline)

### Grammar & Meaning Correction
- Flan-T5 (Base)
- Grammar Error Correction Models

### Audio Processing
- sounddevice
- soundfile
- numpy
- scipy
- noisereduce

### Version Control
- Git
- GitHub

---


