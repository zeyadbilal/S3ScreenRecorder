import boto3
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# إعدادات AWS
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')
FOLDER_NAME = os.getenv('FOLDER_NAME')

# تهيئة عميل S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def list_s3_contents(bucket_name, folder_name):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        
        if 'Contents' in response:
            print("Contents in folder:", folder_name)
            for obj in response['Contents']:
                print(obj['Key'])
                download_file(bucket_name, obj['Key'])  # Download each file
        else:
            print(f"No contents found in {folder_name}.")
    
    except Exception as e:
        print(f"Error retrieving contents: {e}")

def download_file(bucket_name, object_key):
    local_file_path = os.path.join(os.getcwd(), os.path.basename(object_key))  # Save in current directory
    try:
        s3_client.download_file(bucket_name, object_key, local_file_path)
        print(f"Downloaded: {object_key} to {local_file_path}")
    except Exception as e:
        print(f"Error downloading {object_key}: {e}")

# استدعاء الدالة
list_s3_contents(BUCKET_NAME, FOLDER_NAME)
