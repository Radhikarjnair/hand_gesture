# app.py
import os
# hide TF/TFLite logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import mediapipe as mp
import math
import time

# --- pycaw imports for Windows volume control ---
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# -----------------------
# Setup MediaPipe
# -----------------------
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
mpDraw = mp.solutions.drawing_utils

# -----------------------
# Setup audio (pycaw)
# -----------------------
try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    audio = cast(interface, POINTER(IAudioEndpointVolume))
    # Try using scalar (0.0 - 1.0). If not available, we fall back to level mapping.
    supports_scalar = hasattr(audio, "SetMasterVolumeLevelScalar")
    if supports_scalar:
        print("Audio control: SetMasterVolumeLevelScalar available.")
    else:
        print("Audio control: SetMasterVolumeLevelScalar NOT available, will use level mapping.")
    vol_range = audio.GetVolumeRange()  # (min, max, step) for SetMasterVolumeLevel
    min_vol_level, max_vol_level = vol_range[0], vol_range[1]
    print(f"Volume range: {min_vol_level:.2f} .. {max_vol_level:.2f}")
except Exception as e:
    print("ERROR: Could not initialize system audio control (pycaw).")
    print("Exception:", e)
    print("Make sure pycaw==20230407 is installed and project is NOT in OneDrive.")
    raise

# -----------------------
# Webcam
# -----------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("ERROR: Could not open webcam. Close other apps using camera and try again.")

# Smoothing parameters
prev_distance = 0.0
prev_volume = 0.0
alpha_dist = 0.75   # smoothing for distance (higher = smoother but slower)
alpha_vol = 0.65    # smoothing for volume scalar (higher = smoother)
# Distance to volume mapping (tune if needed)
MIN_DIST = 20    # when fingers very close
MAX_DIST = 220   # when fingers far apart (adjust to camera & hand size)

print("Starting Hand-to-Volume Control. Press 'q' to quit.")

# small helper
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

while True:
    success, img = cap.read()
    if not success:
        print("Failed to read from camera.")
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    h, w, _ = img.shape

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            # draw landmarks
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            # collect landmark positions
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((id, cx, cy))

            # Ensure we have the two landmarks we need
            try:
                # thumb tip = 4, index tip = 8
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
            except Exception:
                continue

            # draw indicators
            cv2.circle(img, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

            # raw distance
            distance = math.hypot(x2 - x1, y2 - y1)

            # smooth the measured distance
            smoothed_dist = alpha_dist * prev_distance + (1 - alpha_dist) * distance
            prev_distance = smoothed_dist

            # map distance to volume scalar 0.0 - 1.0
            norm = (smoothed_dist - MIN_DIST) / (MAX_DIST - MIN_DIST)
            norm = clamp(norm, 0.0, 1.0)  # 0..1
            vol_scalar_target = norm  # when fingers apart -> higher volume

            # smooth the volume changes (avoids rapid jumps)
            vol_scalar = alpha_vol * prev_volume + (1 - alpha_vol) * vol_scalar_target
            prev_volume = vol_scalar

            # apply to system volume
            try:
                if supports_scalar:
                    audio.SetMasterVolumeLevelScalar(vol_scalar, None)
                else:
                    # fallback: map scalar to volume level
                    level = vol_scalar * (max_vol_level - min_vol_level) + min_vol_level
                    audio.SetMasterVolumeLevel(level, None)
            except Exception as e:
                # do not crash if audio call fails; print once
                print("Warning: setting system volume failed:", e)
                # continue without raising

            # draw volume bar & percent
            vol_percent = int(vol_scalar * 100)
            # volume bar outline
            cv2.rectangle(img, (50, 120), (85, 320), (50, 50, 50), 2)
            # filled bar
            bar_height = int(200 * vol_scalar)
            cv2.rectangle(img, (52, 320 - bar_height), (83, 318), (0, 255, 0), cv2.FILLED)
            # percent text
            cv2.putText(img, f'Volume: {vol_percent}%', (40, 360),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # display smoothed distance too (for debug)
            cv2.putText(img, f'Dist: {int(smoothed_dist)}', (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    else:
        # if no hand detected, optionally keep previous volume (do nothing)
        cv2.putText(img, "No hand detected", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Hand Volume Control", img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
