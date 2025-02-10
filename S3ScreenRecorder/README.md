# Screen Recorder

This is a Python-based screen recorder that captures audio from the system and microphone while recording the screen. The recordings are then merged and uploaded to an AWS S3 bucket.

## Features
- Records audio from the microphone and system sound.
- Captures screen video.
- Merges audio and video into a single file.
- Uploads the final recording to AWS S3.

## Requirements
- Python 3.x
- Required libraries:
  - sounddevice
  - soundfile
  - numpy
  - pyautogui
  - opencv-python
  - threading
  - boto3
  - soundcard
  - ttkbootstrap
  - getmac
  - ffmpeg (Make sure FFmpeg is installed on your system) & Change Path



You can install the required libraries using pip:

```bash
pip install sounddevice soundfile numpy pyautogui opencv-python boto3 soundcard ttkbootstrap getmac
