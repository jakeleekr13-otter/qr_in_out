# QR In/Out System Setup Guide

## System Requirements

- Python 3.9+
- Streamlit
- `zbar` library (System dependency for QR scanning)

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies (QR Scanning Support)
The `pyzbar` library requires the `zbar` shared library to be installed on your system.

**macOS (Homebrew):**
```bash
brew install zbar
```

**Ubuntu / Debian:**
```bash
sudo apt-get install libzbar0
```

**Windows:**
Usually, `pip install pyzbar` includes the necessary DLLs, but if you encounter issues, you may need to install the Visual C++ Redistributable Packages.

### 3. Run the Application
```bash
streamlit run app.py
```

## Troubleshooting

### "pyzbar library is not available" Error
If you see this warning on the Guest page, it means the `zbar` system library is missing. Please follow step 2 above to install it for your operating system.
