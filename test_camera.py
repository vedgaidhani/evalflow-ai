import cv2

print("Attempting to connect to the webcam...")
# Try to open the default camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("🚨 ERROR: Python cannot access the camera.")
    print("Fix: Go to Windows Settings -> Privacy & security -> Camera. Ensure 'Let desktop apps access your camera' is turned ON.")
else:
    print("✅ Camera connected! A window should pop up. Press 'q' to close it.")
    while True:
        success, frame = cap.read()
        if not success:
            print("🚨 ERROR: Connected to camera, but cannot read the video frames.")
            break
            
        cv2.imshow("Hardware Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()