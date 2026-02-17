# AI Presentation Assistant

A real-time presentation control system built using computer vision and speech recognition.

This project allows slide navigation, drawing, and interaction through hand gestures and voice commands, with posture monitoring and audio feedback.

---

## Features

- Hand gesture slide navigation (MediaPipe + CVZone)
- Drawing and pointer mode
- Voice commands using OpenAI Whisper
- Real-time posture detection with correction feedback
- Dedicated TTS worker thread for stable audio output
- GPU support for faster speech recognition

---

## How It Works

Webcam → Hand & Pose Detection → Gesture Logic → Slide Control  
Microphone → Whisper → Command Parser → Action  
Pose Data → Posture Monitor → Text-to-Speech Feedback  

Each module runs independently and communicates through a simple state-driven control system.

---

## Project Structure
src/
presentation.py
voice_control.py
posture_monitor.py

assets/
PPT/

requirements.txt

---

## Installation

```bash

git clone https://github.com/Vidit-Singla/Presentation_Assistant.git
cd Presentation_Assistant
pip install -r requirements.txt
python src/presentation.py
```
---

Notes

Requires a webcam and microphone.

Whisper performs better with a GPU but runs on CPU as well.

Sample slides are included for testing.



