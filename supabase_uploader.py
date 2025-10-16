from supabase import create_client
import os

class SupabaseUploader:
    def __init__(self, url: str, key: str, bucket_name: str):
        self.client = create_client(url, key)
        self.bucket_name = bucket_name

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
