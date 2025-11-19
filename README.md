 Hand Gesture Volume Control

Control your Windows system volume using hand gestures through your webcam!
This project uses OpenCV, MediaPipe, and PyCAW to detect your hand and adjust system audio in real time.

Features

Real-time hand tracking

 Smooth, gesture-based volume control

 MediaPipe hand landmark detection

 Windows system volume integration (PyCAW)

 Live webcam preview with UI indicators

 Flicker-free volume smoothing

 Requirements

Install all the required Python packages:

pip install opencv-python mediapipe pycaw==20230407 comtypes

How It Works

Webcam captures your hand in real time

MediaPipe identifies hand landmarks

Distance between Thumb Tip (ID 4) and Index Finger Tip (ID 8) is measured

Distance → Mapped to Volume Scalar (0.0 to 1.0)

PyCAW updates the system volume

Smooth interpolation prevents flickering


How to Run

Open terminal inside your project folder:
cd hand_gesture

Run the program:
python app.py

Show your hand in front of the camera

Move thumb & index finger:

| Gesture       | Volume         |
| ------------- | -------------- |
| Fingers close | 🔉 Volume Down |
| Fingers far   | 🔊 Volume Up   |


Important Notes

Works only on Windows (PyCAW is Windows-only)

Ensure the project folder is NOT inside OneDrive (prevents COM errors)

Close apps using your camera (Zoom, Teams, Chrome) if webcam doesn’t open

Adjust MIN_DIST and MAX_DIST for your camera distance

Author

Radhika R J Nair
GitHub: https://github.com/Radhikarjnair
