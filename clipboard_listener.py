import win32gui
import win32con
import ctypes
from typing import Callable

# Define WM_CLIPBOARDUPDATE manually
WM_CLIPBOARDUPDATE = 0x031D

class ClipboardListener:
    """Listens for clipboard changes and executes a callback."""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CLIPBOARDUPDATE:
            self.callback()
        elif msg == win32con.WM_DESTROY:
            ctypes.windll.user32.RemoveClipboardFormatListener(hwnd)
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def start(self):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = "ClipboardListenerWindow"
        class_atom = win32gui.RegisterClass(wc)

        # Create hidden window
        self.hwnd = win32gui.CreateWindowEx(
            0, class_atom, "Clipboard Listener",
            0, 0, 0, 0, 0,
            0, 0, 0, None
        )

        ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)

        print("Clipboard listener started...")
        win32gui.PumpMessages()  # Starts message loop
