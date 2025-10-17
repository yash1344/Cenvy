import requests
from supabase import create_client
import os


class SupabaseManager:
    def __init__(self, url: str, key: str, bucket_name: str):
        self.client = create_client(url, key)
        self.bucket_name = bucket_name

    def download_to_temp(self, url: str, dir: str) -> str:
        """Download a public file URL to `dir` and return its path."""

        # Safely extract filename portion from URL (ex.: https://uwgqchqhoapudghqyxlb.supabase.co/storage/v1/object/public/clipboard_files/IMG_20251015_161055.jpg)
        try:
            filename = os.path.basename(url.split("?")[0])
            if not filename:
                filename = "downloaded"
        except Exception:
            filename = "downloaded"

        local_path = os.path.join(dir, filename)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Downloaded: {local_path}")
        return local_path

    def upload_file(self, file_path: str):
        """Uploads a file to Supabase Storage and returns its public URL."""
        file_name = os.path.basename(file_path)
        # Check file size limit 50MB
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            print(f"File {file_name} exceeds size limit.")
            return None

        try:
            # Correct: pass upsert as keyword argument
            with open(file_path, "rb") as f:
                self.client.storage.from_(self.bucket_name).upload(file_name, f)

            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
            return public_url
        except Exception as e:
            print(f"Upload failed for {file_path}: {e}")
            return None
        
    #clear whole bucket (delete all available files)
    def clear_bucket(self):
        try:
            files = self.client.storage.from_(self.bucket_name).list()
            for file in files:
                self.client.storage.from_(self.bucket_name).remove([file['name']])
        except Exception as e:
            print(f"Failed to clear bucket: {e}")
