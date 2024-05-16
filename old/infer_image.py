# load config
import json
with open('roboflow_config.json') as f:
    config = json.load(f)

    ROBOFLOW_API_KEY = config["ROBOFLOW_API_KEY"]
    ROBOFLOW_MODEL = config["ROBOFLOW_MODEL"]
    ROBOFLOW_SIZE = config["ROBOFLOW_SIZE"]

    FRAMERATE = config["FRAMERATE"]
    BUFFER = config["BUFFER"]

import asyncio
import cv2
import base64
import httpx
import supervision as sv
import time
from utils import clear_output, crop_image_using_box, read_license_plate, crop_image, detect_text, upscale_result

# Construct the Roboflow Infer URL
# (if running locally replace https://detect.roboflow.com/ with eg http://127.0.0.1:9001/)
upload_url = "".join([
    "http://127.0.0.1:9001/",
    ROBOFLOW_MODEL,
    "?api_key=",
    ROBOFLOW_API_KEY,
    "&format=image", # Change to json if you want the prediction boxes, not the visualization
    "&stroke=0",
    "&confidence=55"
])

upload_url_json = "".join([
    "http://127.0.0.1:9001/",
    ROBOFLOW_MODEL,
    "?api_key=",
    ROBOFLOW_API_KEY,
    "&format=json", # Change to json if you want the prediction boxes, not the visualization
    "&stroke=0",
    "&confidence=55"
])

tracker = sv.ByteTrack(track_activation_threshold=0.55, lost_track_buffer=24, minimum_matching_threshold=0.9, frame_rate=24)
box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()

# Get webcam interface via opencv-python
video = cv2.VideoCapture("tcp://raspberrypi.local:5556")

json_sink = sv.JSONSink("./cropped/output.json")

detected_detections = set()

# Infer via the Roboflow Infer API and return the result
# Takes an httpx.AsyncClient as a parameter
async def infer(requests):
    # Get the current image from the webcam
    ret, img = video.read()

    # Resize (while maintaining the aspect ratio) to improve speed and save bandwidth
    height, width, channels = img.shape
    scale = ROBOFLOW_SIZE / max(height, width)
    scaled_img = cv2.resize(img, (round(scale * width), round(scale * height)))

    # Encode image to base64 string
    retval, buffer = cv2.imencode('.jpg', scaled_img)
    img_str = base64.b64encode(buffer)

    # Get prediction from Roboflow Infer API
    # resp = await requests.post(upload_url, data=img_str, headers={
    #     "Content-Type": "application/x-www-form-urlencoded"
    # })
    resp_json = await requests.post(upload_url_json, data=img_str, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })

    resp_json = json.loads((resp_json.content).decode('utf-8'))
    upscaled_result = upscale_result(resp_json, max(height, width) / ROBOFLOW_SIZE)
    detections = sv.Detections.from_inference(upscaled_result)
    detections = tracker.update_with_detections(detections)
    
    labels = [
        f"#{tracker_id}"
        for tracker_id
        in detections.tracker_id
    ]
    for i in range(abs(len(labels) - len(detections))):
        labels.append(f"${i+1}")

    # print(f"trackers: {len(detections.tracker_id)}, labels: {len(labels)}")

    predictions = resp_json["predictions"]
    # image_height = resp_json["image"]["height"]
    # image_width = resp_json["image"]["width"]

    # image = np.asarray(bytearray(resp.content), dtype="uint8")
    # image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    reverse_scale = max(height, width) / ROBOFLOW_SIZE

    for xyxy, id in zip(detections.xyxy, detections.tracker_id):
        if (id in detected_detections):
            continue
        # x_original = round(prediction["x"] * reverse_scale)
        # y_original = round(prediction["y"] * reverse_scale)
        # width_original = round(prediction["width"] * reverse_scale)
        # height_original = round(prediction["height"] * reverse_scale)
        # crop_image(img, x_original, y_original, width_original, height_original, height, width)
        crop_image_using_box(img, xyxy[0], xyxy[1], xyxy[2], xyxy[3], id)
        with json_sink as sink:
            sink.append(detections, {"plate-number": detect_text(f'./cropped/{id}.jpg')})
        detected_detections.add(id)

    boxed_frame = box_annotator.annotate(img.copy(), detections=detections)
    return label_annotator.annotate(boxed_frame, detections=detections, labels=labels)

# Main loop; infers at FRAMERATE frames per second until you press "q"
async def main():
    clear_output()

    # Initialize
    last_frame = time.time()

    # Initialize a buffer of images
    futures = []

    async with httpx.AsyncClient(timeout=None) as requests:
        while 1:
            # On "q" keypress, exit
            if(cv2.waitKey(1) == ord('q')):
                break

            # Throttle to FRAMERATE fps and print actual frames per second achieved
            elapsed = time.time() - last_frame
            # await asyncio.sleep(max(0, 1/FRAMERATE - elapsed))
            # await asyncio.sleep(1)
            print((1/(time.time()-last_frame)), " fps")
            last_frame = time.time()

            # Enqueue the inference request and safe it to our buffer
            task = asyncio.create_task(infer(requests))
            futures.append(task)

            # Wait until our buffer is big enough before we start displaying results
            if len(futures) < BUFFER * FRAMERATE:
                continue

            # Remove the first image from our buffer
            # wait for it to finish loading (if necessary)
            if len(futures) > 0:
                image = await futures.pop(0)
                # And display the inference results
                cv2.imshow('image', image)

# Run our main loop
asyncio.run(main())

# Release resources when finished
video.release()
cv2.destroyAllWindows()