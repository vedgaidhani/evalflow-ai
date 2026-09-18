import cv2
import mediapipe as mp
import threading

class VisionProctor:
    def __init__(self):
        self.running = False
        self.strikes = 0

    def start_proctoring(self):
        self.running = True
        self.strikes = 0
        # Daemon=True ensures the camera turns off if Streamlit is closed
        threading.Thread(target=self._camera_loop, daemon=True).start()

    def stop_proctoring(self):
        self.running = False
        # Calculate approximate penalty seconds (camera runs at ~30 frames per sec)
        return self.strikes // 30 

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(max_num_faces=2, min_detection_confidence=0.5)
        
        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            frame = cv2.flip(frame, 1) # Flip for selfie-view
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            h, w, _ = frame.shape
            color = (0, 255, 0) # Default Green
            status = "STATUS: FOCUSED"
            
            if results.multi_face_landmarks:
                if len(results.multi_face_landmarks) > 1:
                    status = "WARNING: MULTIPLE PERSONS DETECTED"
                    color = (0, 0, 255) # Red
                    self.strikes += 1
                else:
                    # Head Pose Tracking Math
                    face = results.multi_face_landmarks[0]
                    nose = face.landmark[1]
                    left_eye = face.landmark[33]
                    right_eye = face.landmark[263]
                    
                    left_dist = abs(nose.x - left_eye.x)
                    right_dist = abs(nose.x - right_eye.x)
                    
                    # If nose shifts too close to either eye, the head is turned
                    if left_dist < 0.04 or right_dist < 0.04:
                        status = "WARNING: LOOKING AWAY (CHEATING)"
                        color = (0, 0, 255)
                        self.strikes += 1
                        
                    # Draw a bounding box tracking the face
                    x_min = int(min([lm.x for lm in face.landmark]) * w)
                    x_max = int(max([lm.x for lm in face.landmark]) * w)
                    y_min = int(min([lm.y for lm in face.landmark]) * h)
                    y_max = int(max([lm.y for lm in face.landmark]) * h)
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
            else:
                status = "WARNING: NO FACE IN FRAME"
                color = (0, 0, 255)
                self.strikes += 1

            # Render the UI on the security feed
            cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imshow("EvalFlow Security Feed", frame)
            
            # Allow cv2 to render the frame (1ms)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()