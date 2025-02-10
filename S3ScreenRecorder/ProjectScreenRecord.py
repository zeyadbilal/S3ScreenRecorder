import sounddevice as sd
import soundfile as sf
import numpy as np
import pyautogui
import cv2
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
import os
import subprocess
import soundcard as sc  # لتسجيل صوت النظام
import boto3  # مكتبة Boto3 لرفع الملفات إلى S3
import io  # للتعامل مع الذاكرة كملف
from ttkbootstrap.dialogs import Messagebox  # لإظهار رسائل للمستخدم
import getmac  # للحصول على عنوان MAC للجهاز
from dotenv import load_dotenv  # لتحميل المتغيرات من ملف .env

# تحميل المتغيرات من ملف .env
load_dotenv()

# إعدادات AWS من ملف .env
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')
folder_name = os.getenv('FOLDER_NAME')  # اسم المجلد الرئيسي

# تهيئة عميل S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def get_device_id():
    """
    إنشاء معرف جهاز ثابت باستخدام عنوان MAC.
    """
    try:
        mac_address = getmac.get_mac_address()
        if mac_address:
            return mac_address.replace(":", "")  # إزالة النقطتين من عنوان MAC
        else:
            raise Exception("Could not get MAC address.")
    except Exception as e:
        Messagebox.show_error(f"Error getting device ID: {e}")
        return "unknown_device"  # استخدام معرف افتراضي في حالة الخطأ

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []
        self.start_time = None

    def start(self):
        self.recording = True
        self.audio_data = []
        self.start_time = datetime.now()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate, 
            channels=self.channels,
            callback=self._audio_callback
        )
        self.stream.start()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.audio_data.append(indata.copy())

    def stop(self):
        self.recording = False
        self.stream.stop()
        return self.audio_data, self.start_time

    def save_to_memory(self):
        audio_data = np.concatenate(self.audio_data, axis=0)
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, self.sample_rate, format='wav')
        buffer.seek(0)
        return buffer

class SystemAudioRecorder:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self.start_time = None

    def start(self):
        self.recording = True
        self.audio_data = []
        self.start_time = datetime.now()
        self.mic = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)

    def capture_audio(self):
        with self.mic.recorder(samplerate=self.sample_rate) as recorder:
            while self.recording:
                data = recorder.record(numframes=self.sample_rate)
                self.audio_data.append(data)

    def stop(self):
        self.recording = False
        return self.audio_data, self.start_time

    def save_to_memory(self):
        audio_data = np.concatenate(self.audio_data, axis=0)
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, self.sample_rate, format='wav')
        buffer.seek(0)
        return buffer

class VideoRecorder:
    def __init__(self, fps=9):
        self.fps = fps
        self.recording = False
        self.frames = []
        self.start_time = None

    def start(self):
        self.recording = True
        self.frames = []
        self.start_time = datetime.now()

    def capture_frame(self):
        if not self.recording:
            return

        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        self.frames.append(frame)

    def stop(self):
        self.recording = False
        return self.frames, self.start_time

    def save_to_memory(self):
        if not self.frames:
            return None

        height, width, _ = self.frames[0].shape

        # حفظ الفيديو في ملف مؤقت
        temp_file = "temp_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_file, fourcc, self.fps, (width, height))
        
        for frame in self.frames:
            out.write(frame)
        out.release()

        # قراءة الملف المؤقت إلى الذاكرة
        with open(temp_file, "rb") as f:
            video_buffer = io.BytesIO(f.read())

        # حذف الملف المؤقت
        os.remove(temp_file)

        video_buffer.seek(0)
        return video_buffer

class ScreenRecorder:
    def __init__(self, device_id=None):
        self.root = ttk.Window(themename="darkly")
        self.root.title("Screen Recorder")
        self.root.geometry("400x200")
        
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.system_audio_recorder = SystemAudioRecorder()
        self.video_recorder = VideoRecorder()
        self.device_id = device_id if device_id else get_device_id()  # استخدام device_id ثابت
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        title_label = ttk.Label(
            main_frame, 
            text="Screen Recorder", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # زر تشغيل/إيقاف التسجيل
        self.record_btn = ttk.Button(
            main_frame,
            text="Start Recording",
            style="success.TButton",
            command=self.toggle_recording,
            width=20
        )
        self.record_btn.pack(pady=10)
        
        # مؤشر الحالة
        self.status_label = ttk.Label(
            main_frame, 
            text="Ready to record", 
            bootstyle="info"
        )
        self.status_label.pack(pady=10)

    def log_status(self, message):
        self.status_label.config(text=message)
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.record_btn.configure(text="Stop Recording", style="danger.TButton")
        self.log_status("Recording started...")

        # بدء تسجيل الصوت من الميكروفون
        self.audio_recorder.start()

        # بدء تسجيل صوت النظام
        self.system_audio_recorder.start()
        self.system_audio_thread = threading.Thread(target=self.system_audio_recorder.capture_audio)
        self.system_audio_thread.start()

        # بدء تسجيل الفيديو
        self.video_recorder.start()
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.start()
    
    def stop_recording(self):
        self.is_recording = False
        self.record_btn.configure(text="Start Recording", style="success.TButton")
        self.log_status("Recording stopped. Merging audio and video...")

        # إيقاف تسجيل الصوت من الميكروفون وحفظه في الذاكرة
        audio_data, audio_start = self.audio_recorder.stop()
        mic_audio_buffer = self.audio_recorder.save_to_memory()

        # إيقاف تسجيل صوت النظام وحفظه في الذاكرة
        system_audio_data, system_audio_start = self.system_audio_recorder.stop()
        system_audio_buffer = self.system_audio_recorder.save_to_memory()

        # إيقاف تسجيل الفيديو وحفظه في الذاكرة
        video_frames, video_start = self.video_recorder.stop()
        video_buffer = self.video_recorder.save_to_memory()

        # دمج الفيديو مع صوت النظام والميكروفون
        self.merge_audio_video(video_buffer, mic_audio_buffer, system_audio_buffer)

    def upload_to_s3(self, buffer, file_name):
        current_date = datetime.now().strftime('%Y-%m-%d')
        s3_path = f"{folder_name}team-recordings/{current_date}/{self.device_id}/all-recordings/{file_name}"
        
        try:
            s3_client.upload_fileobj(buffer, BUCKET_NAME, s3_path)
            self.log_status(f"File uploaded successfully to: {s3_path}")
        except Exception as e:
            self.log_status(f"Error uploading file: {e}")

    def _record_video(self):
        while self.is_recording:
            self.video_recorder.capture_frame()
            pyautogui.sleep(1/self.video_recorder.fps)
    
    def merge_audio_video(self, video_buffer, mic_audio_buffer, system_audio_buffer):
        try:
            ffmpeg_path = self._find_ffmpeg()
            
            if not ffmpeg_path:
                self.log_status("FFmpeg not found")
                return
            
            # حفظ البيانات في ملفات مؤقتة
            temp_video = "temp_video.mp4"
            temp_mic_audio = "temp_mic_audio.wav"
            temp_system_audio = "temp_system_audio.wav"
            temp_mixed_audio = "temp_mixed_audio.wav"
            output_file = f"merged_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            # حفظ الفيديو في ملف مؤقت
            with open(temp_video, "wb") as f:
                f.write(video_buffer.getbuffer())

            # حفظ صوت الميكروفون في ملف مؤقت
            with open(temp_mic_audio, "wb") as f:
                f.write(mic_audio_buffer.getbuffer())

            # حفظ صوت النظام في ملف مؤقت
            with open(temp_system_audio, "wb") as f:
                f.write(system_audio_buffer.getbuffer())

            # دمج صوت النظام والميكروفون في ملف صوت واحد
            subprocess.run([
                ffmpeg_path, 
                '-i', temp_mic_audio, 
                '-i', temp_system_audio, 
                '-filter_complex', 'amix=inputs=2:duration=longest', 
                temp_mixed_audio
            ], check=True)

            # دمج الفيديو مع الصوت المدمج
            subprocess.run([
                ffmpeg_path, 
                '-i', temp_video, 
                '-i', temp_mixed_audio, 
                '-c:v', 'copy', 
                '-c:a', 'aac', 
                '-shortest', 
                output_file
            ], check=True)

            # رفع الفيديو المدمج إلى S3
            with open(output_file, "rb") as f:
                output_buffer = io.BytesIO(f.read())
            self.upload_to_s3(output_buffer, output_file)

            # حذف الملفات المؤقتة
            for temp_file in [temp_video, temp_mic_audio, temp_system_audio, temp_mixed_audio, output_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            self.log_status(f"Recording saved and uploaded: {output_file}")
        
        except subprocess.CalledProcessError as e:
            self.log_status(f"Error merging recordings: {e}")
        except Exception as e:
            self.log_status(f"Unexpected error: {e}")
    
    def _find_ffmpeg(self):
        possible_paths = [
            r'D:\ffmpeg.exe',
            r'C:\ffmpeg.exe',
            os.path.join(os.getcwd(), 'ffmpeg.exe')
        ]
        
        path_env = os.environ.get('PATH', '').split(os.pathsep)
        possible_paths.extend([os.path.join(path, 'ffmpeg.exe') for path in path_env])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    device_id = get_device_id()  # الحصول على device_id ثابت
    app = ScreenRecorder(device_id=device_id)
    app.run()