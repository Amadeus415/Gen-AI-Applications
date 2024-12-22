import cv2

def take_photo():
    # Initialize the camera (0 is usually the built-in webcam)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise IOError("Cannot access webcam")
    
    print("Camera opened. Press SPACE to take a photo or ESC to quit.")
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if ret:
            # Display the frame
            cv2.imshow('Take Photo', frame)
            
            # Wait for key press
            key = cv2.waitKey(1)
            
            # If space bar is pressed, save the image
            if key == 32: # Space key
                cv2.imwrite("../images/webcam_photo.jpg", frame)
                print("Photo saved as 'webcam_photo.jpg'")
                break
            # If ESC is pressed, exit
            elif key == 27: # ESC key
                print("Photo capture cancelled")
                break
    
    # Release the camera and destroy windows
    cap.release()
    cv2.destroyAllWindows()
    
    return "../images/webcam_photo.jpg"