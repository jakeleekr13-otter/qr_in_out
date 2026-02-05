import os
import sys

# Attempt 1: Add to DYLD_LIBRARY_PATH (might not work if process already started)
# os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib' 

# Attempt 2: Monkey patch ctypes.util.find_library?
import ctypes.util
original_find_library = ctypes.util.find_library

def patched_find_library(name):
    if name == 'zbar':
        # Check homebrew path
        if os.path.exists('/opt/homebrew/lib/libzbar.dylib'):
            return '/opt/homebrew/lib/libzbar.dylib'
    return original_find_library(name)

ctypes.util.find_library = patched_find_library

try:
    from pyzbar.pyzbar import decode
    print("Success with patch!")
except ImportError as e:
    print(f"Failed with patch: {e}")
