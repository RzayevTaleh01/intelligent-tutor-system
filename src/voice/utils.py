import os
import uuid
import shutil

def save_upload_file(upload_file, destination_folder="tmp_media"):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    file_ext = os.path.splitext(upload_file.filename)[1]
    if not file_ext:
        file_ext = ".wav" # default
        
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(destination_folder, unique_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path

def get_media_url(filename: str, request) -> str:
    # Build full URL based on request base URL
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/media/{filename}"
