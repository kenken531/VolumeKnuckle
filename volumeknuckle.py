"""
VolumeKnuckle  —  Windows Edition
==================================
Control your system volume with your fist via webcam.

Install dependencies:
    pip install opencv-python mediapipe numpy pycaw comtypes
"""

import time
import threading
import sys
import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ── Console UI helpers ──────────────────────────────────────────────────────

CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

def clear():
    print("\033[2J\033[H", end="")

def banner():
    print(f"{BOLD}{CYAN}")
    print("  ██╗   ██╗ ██████╗ ██╗     ██╗   ██╗███╗   ███╗███████╗")
    print("  ██║   ██║██╔═══██╗██║     ██║   ██║████╗ ████║██╔════╝")
    print("  ██║   ██║██║   ██║██║     ██║   ██║██╔████╔██║█████╗  ")
    print("  ╚██╗ ██╔╝██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══╝  ")
    print("   ╚████╔╝ ╚██████╔╝███████╗╚██████╔╝██║ ╚═╝ ██║███████╗")
    print("    ╚═══╝   ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝")
    print(f"  {DIM}KNUCKLE{RESET}{BOLD}{CYAN}                        Day 03 — BUILDCORED ORCAS{RESET}")
    print()

def instructions_panel():
    print(f"  {BOLD}── HOW TO USE ──────────────────────────────────────────{RESET}")
    print(f"  {GREEN}✊  Raise your fist{RESET}   →  Volume UP")
    print(f"  {RED}✊  Lower your fist{RESET}   →  Volume DOWN")
    print(f"  {DIM}🖐  Open hand         →  Volume unchanged{RESET}")
    print(f"  {YELLOW}  Webcam window: press  Q  to stop{RESET}")
    print(f"  {BOLD}────────────────────────────────────────────────────────{RESET}")
    print()

def print_status(running: bool, volume: float, fist: bool):
    status_str = f"{GREEN}{BOLD}● RUNNING{RESET}" if running else f"{RED}{BOLD}■ STOPPED{RESET}"
    fist_str   = f"{GREEN}✊ FIST DETECTED{RESET}" if fist  else f"{DIM}✋ no fist{RESET}"

    # Volume bar (20 chars wide)
    filled = int(volume / 5)
    bar    = f"{GREEN}{'█' * filled}{DIM}{'░' * (20 - filled)}{RESET}"

    print(f"\r  Status : {status_str}   Hand : {fist_str}   "
          f"Volume : {bar} {YELLOW}{BOLD}{int(volume):3d}%{RESET}   ", end="", flush=True)

# ── Volume setup ────────────────────────────────────────────────────────────

def _init_volume():
    speakers   = AudioUtilities.GetSpeakers()
    raw_device = getattr(speakers, "_dev", speakers)
    interface  = raw_device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

volume_obj = _init_volume()

def get_volume() -> float:
    return volume_obj.GetMasterVolumeLevelScalar() * 100

def set_volume(v: float):
    volume_obj.SetMasterVolumeLevelScalar(float(np.clip(v, 0, 100)) / 100, None)

# ── MediaPipe setup ─────────────────────────────────────────────────────────

mp_hands  = mp.solutions.hands
mp_draw   = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)

# ── Fist detection ──────────────────────────────────────────────────────────

FINGERTIP_IDS = [8, 12, 16, 20]
MCP_IDS       = [5,  9, 13, 17]
WRIST_ID      = 0

def is_fist(lms) -> bool:
    wrist = np.array([lms[WRIST_ID].x, lms[WRIST_ID].y])
    for tip_id, mcp_id in zip(FINGERTIP_IDS, MCP_IDS):
        tip = np.array([lms[tip_id].x, lms[tip_id].y])
        mcp = np.array([lms[mcp_id].x, lms[mcp_id].y])
        if np.linalg.norm(tip - wrist) > np.linalg.norm(mcp - wrist):
            return False
    return True

def fist_center_y(lms, frame_h: int) -> float:
    return np.mean([lms[i].y for i in MCP_IDS + [WRIST_ID]]) * frame_h

# ── Webcam overlay drawing ──────────────────────────────────────────────────

def draw_volume_bar(frame, volume: float, h: int, w: int):
    bar_x, bar_top, bar_bot = w - 60, 80, h - 80
    fill_h = int((bar_bot - bar_top) * volume / 100)

    cv2.rectangle(frame, (bar_x, bar_top), (bar_x + 30, bar_bot), (40, 40, 40), -1)
    cv2.rectangle(frame, (bar_x, bar_top), (bar_x + 30, bar_bot), (80, 80, 80), 2)
    if fill_h > 0:
        r = int(255 * volume / 100)
        g = int(255 * (1 - abs(volume - 50) / 50))
        b = int(255 * (1 - volume / 100))
        cv2.rectangle(frame, (bar_x, bar_bot - fill_h), (bar_x + 30, bar_bot), (b, g, r), -1)

    cv2.putText(frame, f"{int(volume)}%", (bar_x - 5, bar_bot + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)
    cv2.putText(frame, "VOL", (bar_x + 2, bar_top - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

def draw_hud(frame, fist_detected: bool, fps: float, h: int):
    cv2.putText(frame, f"FPS {fps:.0f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 160), 1)
    for i, line in enumerate([
        "Raise fist  ->  Volume UP",
        "Lower fist  ->  Volume DOWN",
        "Press  Q    ->  Quit",
    ]):
        cv2.putText(frame, line, (12, 58 + i * 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    label = "  FIST DETECTED  " if fist_detected else "  NO FIST  "
    color = (0, 200, 60)        if fist_detected else (80, 80, 80)
    (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
    cv2.rectangle(frame, (10, h - 42), (16 + tw, h - 14), color, -1)
    cv2.putText(frame, label, (12, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (10, 10, 10), 2)

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    # ── Draw console UI ──
    clear()
    banner()
    instructions_panel()

    print(f"  {BOLD}── CONTROLS ─────────────────────────────────────────────{RESET}")
    print(f"  Press {GREEN}{BOLD}ENTER{RESET} to start   |   Press {RED}{BOLD}Q{RESET} in the webcam window to stop")
    print(f"  {BOLD}────────────────────────────────────────────────────────{RESET}")
    print()
    input(f"  {YELLOW}  Press ENTER to launch VolumeKnuckle...{RESET} ")
    print()

    # ── Open webcam ──
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print(f"\n  {RED}ERROR: Cannot open webcam.{RESET}\n")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  720)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

    print(f"  {GREEN}Webcam opened successfully.{RESET}")
    print(f"  {DIM}Watching for your fist...{RESET}\n")

    current_vol     = get_volume()
    prev_fist_y     = None
    last_update     = 0.0
    VOL_SENSITIVITY = 150
    UPDATE_INTERVAL = 0.05
    prev_time       = time.time()
    fist_detected   = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame   = cv2.flip(frame, 1)
        h, w    = frame.shape[:2]
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        fist_detected = False

        if results.multi_hand_landmarks:
            lms = results.multi_hand_landmarks[0].landmark

            mp_draw.draw_landmarks(
                frame, results.multi_hand_landmarks[0],
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )

            if is_fist(lms):
                fist_detected = True
                cy = fist_center_y(lms, h)

                if prev_fist_y is not None and (now - last_update) >= UPDATE_INTERVAL:
                    delta_vol   = ((prev_fist_y - cy) / VOL_SENSITIVITY) * 100
                    current_vol = float(np.clip(current_vol + delta_vol, 0, 100))
                    set_volume(current_vol)
                    last_update = now

                prev_fist_y = cy

                for mid in MCP_IDS:
                    cv2.circle(frame,
                               (int(lms[mid].x * w), int(lms[mid].y * h)),
                               10, (0, 255, 100), -1)
            else:
                prev_fist_y = None
        else:
            prev_fist_y = None

        draw_volume_bar(frame, current_vol, h, w)
        draw_hud(frame, fist_detected, fps, h)

        # ── Update console status line ──
        print_status(running=True, volume=current_vol, fist=fist_detected)

        cv2.imshow("VolumeKnuckle", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    # ── Final console message ──
    print(f"\n\n  {RED}{BOLD}■ VolumeKnuckle stopped.{RESET}")
    print(f"  Final volume: {YELLOW}{BOLD}{int(current_vol)}%{RESET}\n")


if __name__ == "__main__":
    main()