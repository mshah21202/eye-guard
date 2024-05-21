import cv2
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def main():
    # RTSP URL of the stream
    rtsp_url = "rtsp://localhost:8554/test"
    logging.debug(f"Connecting to RTSP stream at {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        logging.error("Failed to open RTSP stream")
        return

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            logging.error("Failed to retrieve frame or received None frame")
            break

        # Display the frame
        cv2.imshow('RTSP Stream', frame)

        # Press 'q' to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    logging.debug("Released all resources")

if __name__ == "__main__":
    main()