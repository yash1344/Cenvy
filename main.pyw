from clipboard_manager import ClipboardManager
from clipboard_listener import ClipboardListener
import hashlib
from FirebaseRealtimeDB import FirebaseRealtimeDB
import threading
import os
import supabaseSecrets
from supabase_manager import SupabaseManager
import tempfile


TEMP_DIR = os.path.join(tempfile.gettempdir(), "Cenvy Share")
os.makedirs(TEMP_DIR, exist_ok=True)

_last_clipboard_hash = None

supabase = SupabaseManager(
    url=supabaseSecrets.url,
    key=supabaseSecrets.key,
    bucket_name="clipboard_files"
)

# Initialize Firebase
firebase = FirebaseRealtimeDB(
    cred_path="cenvy-7117b-firebase-adminsdk-fbsvc-13b64f68ec.json",  # <-- Your credentials file
    db_url="https://cenvy-7117b-default-rtdb.firebaseio.com/"  # <-- Your DB URL
)

FILE_UPLOAD_IGNORE = threading.Event()  # To prevent self-triggering on uploads
FILE_DOWNLOAD_IGNORE = threading.Event()  # To prevent self-triggering on downloads

def get_clipboard_hash():
    text = ClipboardManager.get_text()
    if text:
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    image = ClipboardManager.get_image()
    if image:
        # Convert image to bytes and hash
        buf = image.tobytes()
        return hashlib.md5(buf).hexdigest()
    return None

def clipboard_changed():
    global _last_clipboard_hash

    if FILE_DOWNLOAD_IGNORE.is_set():
        print("Ignoring clipboard change caused by our own download.")
        FILE_DOWNLOAD_IGNORE.clear()
        return

     # Check for files first
    files = ClipboardManager.get_files()
    if files:
        hash_input = "|".join(files).encode("utf-8")
        current_hash = hashlib.md5(hash_input).hexdigest()
        if current_hash == _last_clipboard_hash:
            return
        _last_clipboard_hash = current_hash

        print("Copied files:", files)
        public_links = []

        supabase.clear_bucket()  # Clear bucket before uploading new files
        for path in files:
            if os.path.isfile(path):
                try:
                    url = supabase.upload_file(path)
                    if url:
                        print(f"Uploaded {path} → {url}")
                        public_links.append(url)
                    else:
                        print(f"Failed to upload {path}")
                except Exception as e:
                    print("Upload error:", e)
            else:
                print("Skipping non-file:", path)

        if public_links:
            # Signal that the next Firebase update(s) were created by our upload
            FILE_UPLOAD_IGNORE.set()
            firebase.set_latest_clipboard({"type": "files", "data": public_links})
        return

    # Then check text
    text = ClipboardManager.get_text()
    if text:
        current_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        if current_hash == _last_clipboard_hash:
            return
        _last_clipboard_hash = current_hash
        print("Clipboard Text Changed:", text)
        firebase.set_latest_clipboard({"type": "text", "data": text})


def on_firebase_update(event):
    data = event.data
    type = event.path

    if not data:
        return
    # If we recently uploaded files, the RTDB will send the same update back; skip it once
    if FILE_UPLOAD_IGNORE.is_set():
        print("Ignoring Firebase update caused by our own upload.")
        FILE_UPLOAD_IGNORE.clear()
        return
    
    # Compare with current clipboard to avoid duplication
    if type == "/data" and isinstance(data, str):
        current_text = ClipboardManager.get_text()
        if current_text == data:
            print("Firebase text matches clipboard, skipping update.")
            return
        ClipboardManager.set_text(data)
        return
    if isinstance(data, dict) and data.get("type") == "text":
        current_text = ClipboardManager.get_text()
        if current_text == data["data"]:
            print("Firebase text matches clipboard, skipping update.")
            return
        ClipboardManager.set_text(data["data"])

    # Handle files
    elif isinstance(data, dict) and data.get("type") == "files":
        file_urls = data["data"]
        local_paths = []
        for url in file_urls:
            try:
                local_path = supabase.download_to_temp(url, TEMP_DIR)
                local_paths.append(local_path)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

        if local_paths:
            FILE_DOWNLOAD_IGNORE.set()
            ClipboardManager.set_clipboard_files(local_paths, cut=True)

if __name__ == "__main__":
    manager = ClipboardManager()

    listener = ClipboardListener(clipboard_changed) 
    print("Listening to clipboard changes...")

    # Start Firebase listener in a thread
    threading.Thread(target=lambda: firebase.listen_latest_clipboard(on_firebase_update), daemon=True).start()

    listener.start()
