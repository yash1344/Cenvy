from pandas import cut
import win32clipboard
import win32con
from PIL import Image
import io
import time
import threading
import struct


MAX_CLIPBOARD_SIZE = 1024 * 1024  # 1 MB

GMEM_MOVEABLE = 0x0002

class ClipboardManager:
    """Handles reading/writing text and images to the clipboard."""
    _clipboard_lock = threading.Lock()

    @staticmethod
    def set_text(text: str):
        with ClipboardManager._clipboard_lock:
            win32clipboard.OpenClipboard(0)  # 0 means current window
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            finally:
                win32clipboard.CloseClipboard()

    @staticmethod
    def get_text() -> str:
        with ClipboardManager._clipboard_lock:
            win32clipboard.OpenClipboard(0)  # 0 means current window
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except TypeError:
                return ""
            finally:
                win32clipboard.CloseClipboard()
            return ""

    @staticmethod
    def set_image(image: Image.Image):
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Function to convert image to DIB bytes
        def image_to_dib_bytes(img: Image.Image) -> bytes:
            output = io.BytesIO()
            img.save(output, format="BMP")
            bmp_data = output.getvalue()
            output.close()
            # Remove BMP file header (14 bytes) for DIB
            return bmp_data[14:]

        # Get initial DIB bytes
        dib_data = image_to_dib_bytes(image)

        # If image too large, resize proportionally
        while len(dib_data) > MAX_CLIPBOARD_SIZE:
            w, h = image.size
            # Reduce size by 90%
            image = image.resize((int(w*0.9), int(h*0.9)), Image.LANCZOS)
            dib_data = image_to_dib_bytes(image)

        # Set to clipboard
        with ClipboardManager._clipboard_lock:
            win32clipboard.OpenClipboard(0)  # 0 means current window
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
            finally:
                win32clipboard.CloseClipboard()
                time.sleep(2)



        # if image.mode != "RGB":
        #     image = image.convert("RGB")

        # # Save image to BMP in memory
        # output = io.BytesIO()
        # image.save(output, format="BMP")
        # data = output.getvalue()
        # output.close()

        # # Remove BMP file header (first 14 bytes)
        # dib_data = data[14:]

        # # Set clipboard
        # win32clipboard.OpenClipboard()
        # try:
        #     win32clipboard.EmptyClipboard()
        #     win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
        # except Exception as e:
        #     print(f"Clipboard error: {e}")
        # finally:
        #     win32clipboard.CloseClipboard()
        #     time.sleep(10)


    @staticmethod
    def get_image() -> Image.Image | None:
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                image = Image.open(io.BytesIO(data))
                return image
        except Exception:
            return None
        finally:
            win32clipboard.CloseClipboard()

    @staticmethod
    def get_files():
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                return list(files)
        except Exception:
            pass
        finally:
            win32clipboard.CloseClipboard()
        return None
    
    #provided file paths in argument "file_paths" will be Cut or Copied to clipboard
    @staticmethod
    def set_clipboard_files(file_paths, cut=False):
        """Place file paths into clipboard (cut or copy)."""
        # CF_HDROP requires double-null terminated string
        files_str = "\0".join(file_paths) + "\0\0"
        data = files_str.encode("utf-16le")

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)

        # Add "Preferred DropEffect" — tells Windows if it's a Cut or Copy
        drop_effect = struct.pack("I", 2 if cut else 1)  # 2=cut, 1=copy
        win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat("Preferred DropEffect"), drop_effect)

        win32clipboard.CloseClipboard()

        print(f"Clipboard set with {len(file_paths)} files ({'cut' if cut else 'copy'})")