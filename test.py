import asyncio
import json
import threading
import time
import supervision as sv
from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import display_image, multi_sink
from utils import clear_output, crop_image_using_box, detect_text

tracker = sv.ByteTrack(track_activation_threshold=0.3)
box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()

detected_detections = {}

clear_output()

# This function runs the event loop
def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Prepare the event loop
loop = asyncio.new_event_loop()
t = threading.Thread(target=start_loop, args=(loop,))
t.start()

# Dictionary to keep track of the last execution times for tasks
last_executed_times = {}

# Set to keep track of currently running tasks
running_plate_reading = set()

# tracked vehicles
tracked_vehicles = set()

def enqueue_task(id):
    """Enqueue a task if it's not currently in the queue or on cooldown."""
    if id not in running_plate_reading and (id not in last_executed_times or 
                                    time.time() - last_executed_times[id] > 1):
        asyncio.run_coroutine_threadsafe(read_plate(id), loop)

async def read_plate(id):
    cooldown = 1
    current_time = time.time()
    last_executed = last_executed_times.get(id, 0)
    
    if current_time - last_executed < cooldown:
        print(f"Cooldown active for task {id}. Skipping.")
        return
    if (id not in tracked_vehicles):
        print(tracked_vehicles)
        print(f"Vehicle no longer tracked: {id}. Skipping.")
        return

    print(f"Running OCR on {id}. Running Tasks: {running_plate_reading}")
    running_plate_reading.add(id)
    result = await detect_text(f'./cropped/{id}.jpg')
    if (result == ""):
        result = detected_detections[id]
    detected_detections[id] = result
    running_plate_reading.remove(id)
    last_executed_times[id] = time.time()
    print(f"Finished OCR on {id}. Result: {result}.  Running Tasks: {running_plate_reading}")

    # print(f"Id: {id}, Result: {result}, Detections: {detected_detections}, Task: {running_plate_reading}")

def track_and_annotate(predictions, video_frame):
    detections = sv.Detections.from_inference(predictions)
    detections = tracker.update_with_detections(detections)
    tracked_vehicles.clear()
    tracked_vehicles.update(detections.tracker_id.copy().tolist())
    labels = [
        f"#{tracker_id} Plate: {detected_detections.get(tracker_id, '-')}{'*' if tracker_id in running_plate_reading else ''}"
        for tracker_id
        in detections.tracker_id
    ]
    for i in range(abs(len(labels) - len(detections))):
        labels.append(f"${i+1}")

    for xyxy, id in zip(detections.xyxy, detections.tracker_id):
        crop_image_using_box(video_frame.image, xyxy[0], xyxy[1], xyxy[2], xyxy[3], id)
        if (id not in running_plate_reading):
            enqueue_task(id)


    boxed_frame = box_annotator.annotate(video_frame.image.copy(), detections=detections)
    img = label_annotator.annotate(boxed_frame, detections=detections, labels=labels)
    display_image((video_frame.source_id, img))

api_key = "SVRg2aWesxdOAIjKzlT5"

# create an inference pipeline object
pipeline = InferencePipeline.init(
    model_id="license-plate-recognition-rxg4e/3", # set the model id to a yolov8x model with in put size 1280
    # video_reference="rtsp://raspberrypi.local:8554/cam1", # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    video_reference=1, # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    on_prediction=track_and_annotate, # tell the pipeline object what to do with each set of inference by passing a function
    api_key=api_key, # provide your roboflow api key for loading models from the roboflow api
    confidence=0.4
)


# start the pipeline
pipeline.start()
# wait for the pipeline to finish
pipeline.join()

