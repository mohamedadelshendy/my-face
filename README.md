# Biometric Lock

A Python script that locks your Windows screen if your face is not detected in the webcam for a specified grace period. 

## Features
- First-time setup UI to capture your face.
- Locks the screen with an overlay when your face is absent or an intruder is detected.
- Easy to escape with `ESC` or `Ctrl+Alt+Q` shortcuts.
- Continuous Integration via GitHub Actions to automatically build a standalone executable (`.exe`).

## Usage

1. Go to the **Actions** tab on GitHub.
2. Download the artifact from the latest successful run.
3. Extract and run `BiometricLock.exe`.
4. The first time you run it, a setup window will ask you to register your face.

> **Warning:** This program is for educational/demonstrative purposes. A physical kill switch (Ctrl+Alt+Q) is implemented to prevent getting locked out permanently.
