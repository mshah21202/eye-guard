import easyocr
import numpy as np
import copy
import cv2
import asyncio
from PIL import Image


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

def format_number_plate(plate_numbers: list[str]):
    '''
    Returns a formatted plate number

    Args:
        plate_number: List of strings containing a potential number plate

    Returns:
        plate_numbers: List of potential number plates
    '''
    # remove first element
    if len(plate_numbers) > 0:
        plate_numbers.pop(0)

    # supported countries
    supported_countries = {
        "JO": {
            "identifiers": ["JORDAN", "jordan", "الأردن", "الاردن"]
        },
        "SA": {
            "identifiers": ["KSA", "ksa", "السعودية"]
        },
        "KW": {
            "identifiers": ["KUWAIT", "Kuwait", "الكويت"]
        },
    }

    country_code = ""

    # Try to determine car nationality (Supports: Jordan, KSA, Kuwait)
    for text in plate_numbers:
        temp = text.lower()
        if temp in supported_countries["JO"]["identifiers"]:
            country_code = "JO"
        elif temp in supported_countries["SA"]["identifiers"]:
            country_code = "SA"
        elif temp in supported_countries["KW"]["identifiers"]:
            country_code = "KW"

    potential_plates = []
    # If determined car nationality then format
    if country_code == "JO":
        potential_plates = jordan_format(plate_numbers)
    elif country_code == "SA":
        potential_plates = sa_format(plate_numbers)
    elif country_code == "KW":
        potential_plates = jordan_format(plate_numbers)
    else:
        potential_plates = unknown_format(plate_numbers)
    
    return potential_plates


def jordan_format(strings: list[str]):
    '''
    Returns a list of potential jordan formatted plate numbers
    '''
    result = []

    strings = list(filter(lambda string: any(char.isdigit() for char in string) or '-' in string, strings))

    # if one string
    if len(strings) == 1:
        if ('-' in strings[0]):
            result.append(strings[0])
            return result
        
        if len(strings[0]) == 7:
            result.append(strings[0][:2] + '-' + strings[0][2:])
        else:
            result.append(strings[0][:2] + '-' + strings[0][2:])
            result.append(strings[0][:1] + '-' + strings[0][1:])
        
        return result
    
    
    # if two strings
    if len(strings[0] < strings[0]):
        result.append(strings[0] + '-' + strings[1])
        return result
    
    result.append(strings[1] + '-' + strings[0])
    return result

def sa_format(strings: list[str]):
    '''
    Returns a list of potential KSA formatted plate numbers
    '''
    identifiers = ["KSA", "ksa", "السعودية"]

    number_strings = list(filter(lambda string: any(char.isdigit() for char in string) and string.isascii(), strings))
    char_strings = list(filter(lambda string: any(not char.isdigit() and char != '+' for char in string) and string.isascii(), strings))

    numbers = ""
    chars = ""

    if len(number_strings) > 1:
        numbers = "".join(number_strings)
    else:
        numbers = number_strings[0]

    new_char_strings = []
    # Remove Identifiers
    for string in char_strings:
        if string in identifiers:
            continue
        
        new_char_strings.append(string)
    
    if len(new_char_strings) > 1:
        chars = "".join(new_char_strings)
    else:
        chars = new_char_strings[0]
    
    result_temp = chars + numbers

    return [result_temp]

    

def unknown_format(strings: list[str]):
    '''
    '''
    result = []

    strings = list(filter(lambda string: len(string) <= 5 and string.isascii(), strings))
    
    result.append("".join(strings))

    return result

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