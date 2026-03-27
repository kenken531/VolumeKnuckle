# VolumeKnuckle ✊
 
VolumeKnuckle is a gesture-controlled volume adjuster: it uses your webcam and MediaPipe Hands to detect when you make a fist, then raises or lowers your system volume based on how high or low you hold it. Built for the **BUILDCORED ORCAS — Day 03** challenge.
 
## How it works
 
- Uses **OpenCV** to read frames from your webcam in real time.
- Runs **MediaPipe Hands** to track 21 hand landmarks on each frame.
- Detects a **fist** by checking whether all four fingertips are curled closer to the wrist than their knuckle joints.
- Tracks the **vertical position** of the fist center frame-to-frame — raise your fist to increase volume, lower it to decrease volume.
- Uses **pycaw** to directly control the Windows system audio endpoint in real time.
 
## Requirements
 
- Python 3.10.x
- Windows OS
- A working webcam
 
Python packages:
 
```
pip install opencv-python mediapipe numpy pycaw comtypes
```
 
## Setup
 
1. Clone this repository or download the script.
2. Ensure your webcam is connected and not in use by another app.
3. Install the required Python packages (see Requirements section).
 
## Usage
 
From the project folder:
 
```
python volumeknuckle.py
```
 
- A webcam window opens, mirrored like a selfie.
- On-screen overlay shows:
  - A **volume bar** on the right side showing current volume level
  - **FPS counter** in the top left
  - **Status badge** at the bottom: `FIST DETECTED` or `NO FIST`
  - Control instructions
 
| Gesture | Action |
|---|---|
| ✊ Make a fist + raise it | Volume **UP** |
| ✊ Make a fist + lower it | Volume **DOWN** |
| 🖐 Open hand / no hand | Volume unchanged |
| `Q` key | Quit |
 
## Credits
 
- Hand tracking: [MediaPipe Hands](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- Video capture: [OpenCV](https://opencv.org/)
- System volume control: [pycaw](https://github.com/AndreMiras/pycaw)
 
---
 
Built as part of the **BUILDCORED ORCAS — Day 03: VolumeKnuckle** challenge.
