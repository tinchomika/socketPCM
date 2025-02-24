# SocketPCM

## Introduction

SocketPCM is a Python script for streaming audio between computers using socket connections. It utilizes PyAudio on Linux/macOS and pyaudioWPatch on Windows for audio device access. The pyaudioWPatch library supports WASAPI loopback, simplifying desktop audio sharing. The use of raw PCM audio ensures reliability and efficiency.

## Features

- "Mostly©" reliable audio streaming
- Lightweight and user-friendly
- Configurable audio chunk size
- Auto-save last settings
- Multi-language support (English and Spanish)
- WASAPI loopback support on Windows
- Configurable port

## Installation and Usage

**Installation:**

1. **Python:** Ensure Python is installed (preferably Python 3.x).
2. **PyAudio:** Install PyAudio via pip:
   - Windows: `pip install pyaudiowpatch`
   - Linux/macOS: `pip install pyaudio`

**Usage:**

1. Run `socketPCM.py`: `python socketPCM.py` on both computers.
2. Select mode: "Sender" or "Receiver".
3. Choose input/output device from dropdown menus.
4. Enter the receiver's IP address.
5. Enter the port number, ensure it's open on the receiver.
6. Select the sample rate.
7. Toggle low latency mode.
8. Click "Stream" on both computers to start or "Stop Streaming" to end.
9. Logs are displayed in the "Logs" section.

**Notes:**

- The script auto-detects the receiver's IP address.
- It auto-saves the last settings in a JSON file, as well as logs in the "logs" folder.
- The script lacks some testing, a few bugs may be: 
    - Low latency mode may be unstable.
    - Stream having an inconsistent audio delay, making it hard to synchronize.
    - There may be some audio cuts here and there.

## Roadmap

- Enhance error handling.
- Strengthen connection for robustness and predictable delay.
- Implement a CLI version.
- Adding a the option to stream through UDP.