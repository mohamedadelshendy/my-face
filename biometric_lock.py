import cv2
import face_recognition
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import threading
import sys
import os
import keyboard

def get_base_path():
    """Returns the base path for local files (where the exe/script is running)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class FaceRegistration:
    def __init__(self, image_path):
        self.image_path = image_path
        self.root = tk.Tk()
        self.root.title("Initial Setup - Face Registration")
        self.root.geometry("700x600")
        self.root.configure(bg="#222")
        
        self.label = tk.Label(
            self.root, 
            text="First Time Setup: Register Your Face\nPlease align your face in the camera and click 'Register'", 
            fg="white", 
            bg="#222", 
            font=("Helvetica", 14)
        )
        self.label.pack(pady=10)
        
        self.video_label = tk.Label(self.root, bg="black")
        self.video_label.pack(expand=True)
        
        self.register_btn = tk.Button(
            self.root, 
            text="Register Face", 
            font=("Helvetica", 14, "bold"), 
            bg="#4CAF50", 
            fg="white", 
            padx=20,
            command=self.capture_face
        )
        self.register_btn.pack(pady=20)
        
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            self.root.destroy()
            sys.exit(1)
            
        self.update_frame()
        self.is_registered = False

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            # Convert BGR to RGB for PIL
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        self.root.after(30, self.update_frame)

    def capture_face(self):
        rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        # Fast location check
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        if len(face_locations) == 0:
            messagebox.showwarning("No Face", "No face detected! Please ensure you are clearly visible and try again.")
        elif len(face_locations) > 1:
            messagebox.showwarning("Multiple Faces", "Multiple faces detected! Please ensure only YOU are in the frame.")
        else:
            # We got exactly one face.
            cv2.imwrite(self.image_path, self.current_frame)
            messagebox.showinfo("Success", "Face registered successfully! The system will now begin monitoring.")
            self.is_registered = True
            self.root.destroy()

    def run(self):
        self.root.mainloop()
        self.video_capture.release()
        return self.is_registered


class FaceLockSystem:
    def __init__(self, reference_image_path="my_face.jpg", tolerance=0.6, grace_period=3.0):
        """
        Initializes the FaceLockSystem.
        """
        self.reference_image_path = os.path.join(get_base_path(), reference_image_path)
        self.tolerance = tolerance
        self.grace_period = grace_period
        
        self.known_face_encoding = None
        self.is_running = True
        self.is_locked = False
        
        self.last_seen_time = time.time()
        
        # Initialize the Tkinter UI
        self.root = tk.Tk()
        self.root.title("System Locked")
        self.root.configure(bg="black")
        
        # Full screen, borderless, topmost
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True) 
        
        # Warning label
        self.label = tk.Label(
            self.root, 
            text="UNAUTHORIZED ACCESS\nDEVICE LOCKED", 
            fg="red", 
            bg="black", 
            font=("Helvetica", 48, "bold"),
            justify="center"
        )
        self.label.pack(expand=True)
        
        # Hide the lock screen initially
        self.root.withdraw()
        
        # Set up keyboard kill switches
        keyboard.add_hotkey('ctrl+alt+q', self.kill_switch)
        keyboard.add_hotkey('esc', self.kill_switch)

    def load_reference_image(self):
        """
        Loads the reference image and generates the face encoding.
        """
        try:
            print(f"Loading reference image from {self.reference_image_path}...")
            image = face_recognition.load_image_file(self.reference_image_path)
            encodings = face_recognition.face_encodings(image, model="small")
            if not encodings:
                print("Error: No face found in reference image.")
                sys.exit(1)
            self.known_face_encoding = encodings[0]
            print("Reference face loaded successfully.")
        except Exception as e:
            print(f"Error loading reference image: {e}")
            sys.exit(1)

    def lock_screen(self):
        if not self.is_locked:
            self.is_locked = True
            self.root.after(0, self._show_window)
            print("Screen locked.")

    def _show_window(self):
        self.root.deiconify() 
        self.root.attributes("-topmost", True)
        if self.is_locked:
            self.root.after(1000, self._keep_on_top)

    def _keep_on_top(self):
        if self.is_locked:
            self.root.attributes("-topmost", True)
            self.root.after(1000, self._keep_on_top)

    def unlock_screen(self):
        if self.is_locked:
            self.is_locked = False
            self.root.after(0, self.root.withdraw)
            print("Screen unlocked.")

    def kill_switch(self):
        print("\nKill switch activated. Exiting...")
        self.is_running = False
        self.root.after(0, self.root.quit)

    def process_video(self):
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            print("Error: Could not open webcam.")
            self.kill_switch()
            return

        process_this_frame = True

        while self.is_running:
            ret, frame = video_capture.read()
            if not ret:
                continue

            if process_this_frame:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, model="small")

                if not face_encodings:
                    if time.time() - self.last_seen_time > self.grace_period:
                        self.lock_screen()
                else:
                    authorized_face_found = False
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces([self.known_face_encoding], face_encoding, tolerance=self.tolerance)
                        if True in matches:
                            authorized_face_found = True
                            break
                    
                    if authorized_face_found:
                        self.last_seen_time = time.time()
                        self.unlock_screen()
                    else:
                        self.lock_screen()

            process_this_frame = not process_this_frame
            time.sleep(0.03)

        video_capture.release()

    def run(self):
        self.load_reference_image()
        
        video_thread = threading.Thread(target=self.process_video)
        video_thread.daemon = True
        video_thread.start()
        
        print("System active. Monitoring webcam...")
        self.root.mainloop()

if __name__ == "__main__":
    target_image = "my_face.jpg"
    image_path = os.path.join(get_base_path(), target_image)

    # 1. Setup Phase: Check if the reference face exists
    if not os.path.exists(image_path):
        print("First time setup: launching registration UI...")
        registration = FaceRegistration(image_path)
        success = registration.run()
        
        if not success:
            print("Registration aborted or failed.")
            sys.exit(0)

    # 2. Main Phase: Start the locking system
    system = FaceLockSystem(reference_image_path=target_image, tolerance=0.6, grace_period=3.0)
    system.run()
