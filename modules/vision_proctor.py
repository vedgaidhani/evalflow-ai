import cv2
import threading
import time
import os
import urllib.request

class VisionProctor:
    def __init__(self):
        self.running = False
        self.strikes = 0
        self.face_cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
        self.eye_cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_eye.xml')
        self._download_cascades_if_missing()

    def _download_cascades_if_missing(self):
        if not os.path.exists(self.face_cascade_path):
            print("⏬ PROCTOR: Downloading Face AI model...")
            urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml", self.face_cascade_path)
        if not os.path.exists(self.eye_cascade_path):
            print("⏬ PROCTOR: Downloading Eye AI model...")
            urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml", self.eye_cascade_path)
        print("✅ PROCTOR: All AI models ready.")

    def start_proctoring(self):
        if not self.running:
            print("\n▶️ PROCTOR: Starting advanced OpenCV thread...")
            self.running = True
            self.strikes = 0
            threading.Thread(target=self._camera_loop, daemon=True).start()

    def stop_proctoring(self):
        print("⏹️ PROCTOR: Stopping camera thread...")
        self.running = False
        time.sleep(0.5) 
        return self.strikes // 30 

    def _camera_loop(self):
        print("📷 THREAD: Initializing OpenCV Camera...")
        try:
            cap = cv2.VideoCapture(0)
            face_cascade = cv2.CascadeClassifier(self.face_cascade_path)
            eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)
            
            print("📷 THREAD: Advanced Tracker Active!")
            while self.running and cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break
                    
                frame = cv2.flip(frame, 1) 
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # LOWERED minNeighbors to 4: Makes it much more sensitive to catching a second person
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))
                
                status = "STATUS: FOCUSED"
                color = (0, 255, 0)
                
                if len(faces) == 0:
                    status = "WARNING: NO FACE DETECTED"
                    color = (0, 0, 255)
                    self.strikes += 1
                elif len(faces) > 1:
                    status = "WARNING: MULTIPLE PEOPLE DETECTED"
                    color = (0, 0, 255)
                    self.strikes += 3  # TRIPLE PENALTY for having someone help you
                else:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                        
                        # --- NEW: EYE TRACKING LOGIC ---
                        # We isolate the face area, then search for eyes inside it
                        roi_gray = gray[y:y+h, x:x+w]
                        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))
                        
                        if len(eyes) < 2:
                            status = "WARNING: EYES AVERTED / LOOKING DOWN"
                            color = (0, 0, 255)
                            self.strikes += 1
                        else:
                            # Draw blue boxes around the eyes
                            for (ex, ey, ew, eh) in eyes:
                                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255, 0, 0), 2)

                cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.putText(frame, f"STRIKES: {self.strikes}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                cv2.imshow("EvalFlow Security Feed", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            print("📷 THREAD: Stream finished. Releasing camera...")
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"\n🚨 NATIVE THREAD CRASH: {e}\n")