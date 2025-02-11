# Screen Recorder  

This is a Python-based screen recorder that captures audio from both the system and the microphone while recording the screen. After recording, the audio and video are merged and uploaded to an AWS S3 bucket.  

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
  - ffmpeg (Ensure FFmpeg is installed on your system and update the path)  

---

## Download Content from S3  

### Purpose  
The `DownloadContent.py` script allows you to list and download files from a specific AWS S3 folder.  

### Functionality  
- List all files in a specified S3 folder.  
- Download all files from the folder to the local machine.  

### Requirements  
- AWS S3 access credentials.  
- Boto3 library.  
- python-dotenv (for secure credential management).  

### Usage Example  
```python
# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# List and download contents of a specific folder
list_s3_contents(BUCKET_NAME, FOLDER_NAME)
```

---

## Install Required Libraries  
You can install the required libraries using pip:  
```bash
pip install sounddevice soundfile numpy pyautogui opencv-python boto3 soundcard ttkbootstrap getmac
```
