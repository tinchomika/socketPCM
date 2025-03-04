# SocketPCM

## Introduction

SocketPCM is a Python script for streaming audio between computers using socket connections. It utilizes PyAudio on Linux/macOS and pyaudioWPatch on Windows for audio device access. The pyaudioWPatch library supports WASAPI loopback, simplifying desktop audio sharing.  

I mainly made this script for streaming audio from my laptop to a pc connected to the speakers, so thats the main use case. I was inspired by the VLC http stream feature, wich was my main tool for this purpose, but it was cumbersome to set up every time I had to use it and didn´t have loopback support. With this script I can leave the speakers on and just stream whenever I want in one click thanks to the auto-load feature.  

For any suggestions feel free to open an issue or contact me on [x](https://x.com/tinchotin3)

## Features

- "Mostly©" reliable audio streaming
- Lightweight and user-friendly
- Auto-save last settings
- Multi-language support (English and Spanish)
- WASAPI loopback support on Windows

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
7. Click "Stream" on both computers to start and "Stop Streaming" to end.

**Notes:**

- The script auto-detects the receiver's IP address.
- It auto-saves the last settings in a JSON file, as well as logs in the "logs" folder.
- The script lacks some testing, a few bugs may be: 
    - Low latency mode may be unstable.
    - Stream having an inconsistent audio delay, making it hard to synchronize.
    - There may be some audio cuts here and there.
- This script is intended for local network use, for remote connections a webRTC solution would be best suited.

## Roadmap

- Enhance error handling.
- Strengthen connection for robustness and predictable delay.
- CLI version.
- Bi-directional streaming.
- Internet streaming (?)