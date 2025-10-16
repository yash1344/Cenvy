from clipboard_manager import ClipboardManager
from clipboard_listener import ClipboardListener
from PIL import Image
import hashlib
from FirebaseRealtimeDB import FirebaseRealtimeDB
import threading
import os
from supabase_uploader import SupabaseUploader

_last_clipboard_hash = None


supabase = SupabaseUploader(
    url="https://uwgqchqhoapudghqyxlb.supabase.co",
    key="sb_secret_ZfsWQaPxoPWozqxpNM24ZA_Tb_o0ZcX",
    bucket_name="clipboard_files"
)

# Initialize Firebase
firebase = FirebaseRealtimeDB(
    cred_path="cenvy-7117b-firebase-adminsdk-fbsvc-80b03bfe86.json",  # <-- Your credentials file
    db_url="https://cenvy-7117b-default-rtdb.firebaseio.com/"  # <-- Your DB URL
)

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


def on_firebase_update(data):
    if not data:
        return
    # Compare with current clipboard to avoid duplication
    if isinstance(data, str):
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
    # Image sync removed
    # elif isinstance(data, dict) and data.get("type") == "image":
    #     try:
    #         img_b64 = data["data"]
    #         img_bytes = base64.b64decode(img_b64)
    #         img = Image.open(io.BytesIO(img_bytes))
    #         img.load()
    #         # Compare image hashes
    #         current_image = ClipboardManager.get_image()
    #         if current_image:
    #             buf1 = io.BytesIO()
    #             current_image.save(buf1, format="PNG")
    #             current_hash = hashlib.md5(buf1.getvalue()).hexdigest()
    #             buf2 = io.BytesIO()
    #             img.save(buf2, format="PNG")
    #             new_hash = hashlib.md5(buf2.getvalue()).hexdigest()
    #             if current_hash == new_hash:
    #                 print("Firebase image matches clipboard, skipping update.")
    #                 return
    #         ClipboardManager.set_image(img)
    #         print("Image set to clipboard successfully.")
    #     except Exception as e:
    #         print("Error decoding image from Firebase:", e)

if __name__ == "__main__":
    manager = ClipboardManager()

    listener = ClipboardListener(clipboard_changed) 
    print("Listening to clipboard changes...")

    # Start Firebase listener in a thread
    threading.Thread(target=lambda: firebase.listen_latest_clipboard(on_firebase_update), daemon=True).start()

    listener.start()
