import easyocr
import numpy as np
import copy
import cv2
from PIL import Image
from plateformatter import format_number_plate


# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=False)

import os, shutil
folder = './cropped'
def clear_output():
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def crop_image_using_box(img: np.ndarray, x1, y1, x2, y2, id):
    x1 = int(x1)
    y1 = int(y1)
    x2 = int(x2)
    y2 = int(y2)
    cropped_array = img[y1:y2, x1:x2]

    license_plate_crop_gray = cv2.cvtColor(cropped_array, cv2.COLOR_BGR2GRAY)
    # _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_OTSU)
    # cv2.imshow("Cropped", license_plate_crop_gray)
    # if cv2.waitKey(1) == ord('q'):
    #     cv2.destroyAllWindows()
    cropped_image = Image.fromarray(license_plate_crop_gray)
    cropped_image.save(f"./cropped/{id}.jpg")


def crop_image(img: np.ndarray, x, y, width, height, img_height, img_width):
    x = int(x)
    y = int(y)
    height = int(height)
    width = int(width)
    img_height = int(img_height)
    img_width = int(img_width)

    # print(f"x:{x} y:{y} height:{height} width:{width} img_height:{img_height} img_width:{img_width}")
    # print(x,y,height,width,img_height,img_width)

    start_x = x - width // 2
    start_y = y - height // 2
    end_x = x + width // 2
    end_y = y + height // 2

    # Ensure the coordinates do not go out of image bounds
    start_x = max(start_x, 0)
    start_y = max(start_y, 0)
    end_x = min(end_x, img_width)
    end_y = min(end_y, img_height)

    # print(f"start_x:{start_x}, end_x:{end_x} start_y:{start_y}, end_y:{end_y}, height:{height} width:{width} img_height:{img_height} img_width:{img_width}")

    # Crop the image using NumPy slicing
    cropped_array = img[start_y:end_y, start_x:end_x]


    # Convert the cropped array back to an image to save or display
    license_plate_crop_gray = cv2.cvtColor(cropped_array, cv2.COLOR_BGR2GRAY)
    # _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_OTSU)
    # cv2.imshow("Cropped", license_plate_crop_gray)
    # if cv2.waitKey(1) == ord('q'):
    #     cv2.destroyAllWindows()
    cropped_image = Image.fromarray(license_plate_crop_gray)
    cropped_image.save("./cropped/cropped.jpg")

    return (start_x, start_y, end_x, end_y)

def read_license_plate(license_plate_crop):
    """
    Read the license plate text from the given cropped image.

    Args:
        license_plate_crop (PIL.Image.Image): Cropped image containing the license plate.

    Returns:
        tuple: Tuple containing the formatted license plate text and its confidence score.
    """

    detections = reader.readtext(license_plate_crop)

    for detection in detections:
        bbox, text, score = detection

        text = text.upper().replace(' ', '')
        print(text)
        return text, score

    return None, None

async def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    texts_list = []

    for text in texts:
        texts_list.append(text.description)
        # print(f'\n"{text.description}"')

        # vertices = [
        #     f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        # ]

        # print("bounds: {}".format(",".join(vertices)))
    print(texts_list)
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    return format_number_plate(texts_list)[0]

def upscale_result(result: dict, scale):
    upscaled_result = copy.deepcopy(result)

    upscaled_result["image"]["height"] = round(upscaled_result["image"]["height"] * scale)
    upscaled_result["image"]["width"] = round(upscaled_result["image"]["width"] * scale)

    for prediction in upscaled_result["predictions"]:
        prediction["x"] = round(prediction["x"] * scale)
        prediction["y"] = round(prediction["y"] * scale)
        prediction["width"] = round(prediction["width"] * scale)
        prediction["height"] = round(prediction["height"] * scale)
    # print(result, upscaled_result)
    return upscaled_result