from supabase import create_client
import os

class SupabaseUploader:
    def __init__(self, url: str, key: str, bucket_name: str):
        self.client = create_client(url, key)
        self.bucket_name = bucket_name

    def upload_file(self, file_path: str):
        """Uploads a file to Supabase Storage and returns its public URL."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            res = self.client.storage.from_(self.bucket_name).upload(file_name, f)
        
        if res.status_code in [200, 201]:
            # Generate public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
            return public_url
        else:
            print("Upload failed:", res)
            return None
