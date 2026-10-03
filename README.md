# VoiceFlow MVP

A minimal Linux GNOME/Wayland voice dictation utility.

## Behavior

- Global shortcut starts recording.
- The same shortcut starts a second, tiny control invocation that tells the running process to stop.
- Only one VoiceFlow process can exist.
- The Whisper model is loaded once in the recording process.
- Audio is kept in RAM only.
- No audio file is written.
- The tiny waveform overlay reacts to microphone loudness.
- `ydotoold` is started only for text injection and terminated immediately afterward.
- VoiceFlow exits after injection.
- No permanent VoiceFlow daemon is used.

## Ubuntu/GNOME/Wayland setup

Install system packages:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev portaudio19-dev xwayland libxcb-cursor0 ydotool ydotoold
```

Give the user access to uinput:

```bash
sudo usermod -aG input "$USER"
echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/80-uinput.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo chgrp input /dev/uinput
sudo chmod 660 /dev/uinput
```

Log out and back in once after adding the user to `input`.

Then:

```bash
cd ~/Documents/voiceflow
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
chmod +x run.sh
```

## GNOME shortcut

Create a custom keyboard shortcut:

Command:

```text
/home/abhinav/Documents/voiceflow/run.sh
```

For example:

```text
Alt+V
```

The shortcut is a TOGGLE:

1. Press once -> recording starts.
2. Press again -> recording stops.
3. Transcription is inserted into the focused application.
4. VoiceFlow exits.

You can use another shortcut if desired.

## Cleanup check

After dictation:

```bash
pgrep -af launcher.py
pgrep -af ydotoold
```

Both should normally produce no output.

## Important

Do not enable a permanent `ydotoold` service. VoiceFlow launches it only during text injection.
