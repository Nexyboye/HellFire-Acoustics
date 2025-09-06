import os
import ctypes
from ctypes import wintypes


# Win32 constants
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
FILE_ATTRIBUTE_HIDDEN        = 0x0002
FILE_ATTRIBUTE_SYSTEM        = 0x0004

GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
GetFileAttributesW.restype  = wintypes.DWORD


def list_valid_files(path):
    out = []
    with os.scandir(path) as it:
        for entry in it:
            full = entry.path
            attrs = GetFileAttributesW(full)
            if attrs == 0xFFFFFFFF:
                continue
            if attrs & (  FILE_ATTRIBUTE_REPARSE_POINT
                        | FILE_ATTRIBUTE_HIDDEN
                        | FILE_ATTRIBUTE_SYSTEM):
                continue
            if entry.is_dir(follow_symlinks=False) \
               or entry.name.lower().endswith((".mp3", ".wav")):
                out.append(entry.name)
    return out
    

# I had some access problems which I solved by not listing questionable elements
# might take a look at this problem later