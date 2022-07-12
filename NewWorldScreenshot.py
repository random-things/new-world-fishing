import imutils.object_detection
import logging
import numpy
import cv2
import re
import win32com.client
import win32con
import win32gui
import win32ui
import pytesseract
import PIL.Image

from typing import Any

SCREEN_WIDTH = 1920
DETECTION_DISTANCE = 200
TESSERACT_CONFIG = '--psm 7 -c page_separator=""'
TEMPLATES_TO_LOAD = ['bearing_15',
                     'bearing_30',
                     'bearing_60',
                     'bearing_75',
                     'bearing_105',
                     'bearing_120',
                     'bearing_150',
                     'bearing_165',
                     'bearing_195',
                     'bearing_210',
                     'bearing_240',
                     'bearing_255',
                     'bearing_285',
                     'bearing_300',
                     'bearing_330',
                     'bearing_345',
                     'button',
                     'compass',
                     'east',
                     'fish_hooked',
                     'fish_reeling',
                     'fish_unhooked',
                     'fishing_ready',
                     'interact',
                     'interactable',
                     'large_interactable',
                     'north',
                     'northeast',
                     'northwest',
                     'south',
                     'southeast',
                     'southwest',
                     'west']
TEMPLATES = {}

BOUNDS = {
    'default': {
        'lower': numpy.array([0, 0, 0], dtype="uint8"),
        'upper': numpy.array([240, 240, 240], dtype="uint8")
    },
    'button': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'compass': {
        'lower': numpy.array([10, 20, 10], dtype="uint8"),
        'upper': numpy.array([50, 80, 240], dtype="uint8")
    },
    'east': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'fish_hooked': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'fish_reeling': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'fish_unhooked': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'fishing_ready': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'interact': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 55, 255], dtype="uint8")
    },
    'interactable': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 50, 255], dtype="uint8")
    },
    'large_interactable': {
        'lower': numpy.array([0, 0, 50], dtype="uint8"),
        'upper': numpy.array([240, 50, 255], dtype="uint8")
    },
    'north': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'northeast': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'northwest': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'south': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'southeast': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'southwest': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
    'overlay': {
        'lower': numpy.array([20, 0, 0], dtype="uint8"),
        'upper': numpy.array([80, 240, 240], dtype="uint8")
    },
    'west': {
        'lower': numpy.array([10, 20, 100], dtype="uint8"),
        'upper': numpy.array([40, 150, 255], dtype="uint8")
    },
}

SIZES = {}

COORDINATES = {
    'FPS': (1768, 36, 1924, 53),
    'Position': (1563, 50, 1923, 65)
}


class NewWorldScreenshot:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

        self.image = None
        self.image_array = None
        self.prepared_images = {}

        self.load_templates(TEMPLATES_TO_LOAD)

    def crop_image(self, left: int, top: int, right: int, bottom: int):
        cropped = self.image.crop((left, top, right, bottom))
        return cropped

    def clean_ocr_number(self, ocr_text: str) -> float:
        ocr_text = ocr_text.replace(',', '.')

        try:
            ocr_value = float(ocr_text)
            return ocr_value
        except:
            return -1.0

    def clean_ocr_text(self, ocr_text: str) -> str:
        ocr_text = re.sub(r'[^A-Za-z ]', '', ocr_text).strip()
        return ocr_text

    def find_template(self, template: str, threshold: float = 0.7):
        image = self.prepare_for_ocr(template=template)

        res = cv2.matchTemplate(image, TEMPLATES[template], cv2.TM_CCOEFF_NORMED)
        loc = numpy.where(res >= threshold)
        template_width, template_height = TEMPLATES[template].shape[::-1]
        boxes = []
        for pt in zip(*loc[::-1]):
            if pt[0] < SCREEN_WIDTH * .85:
                boxes.append([pt[0], pt[1], pt[0] + template_width, pt[1] + template_height])
                cv2.rectangle(image, pt, (pt[0] + template_width, pt[1] + template_height), (255, 255, 255), 2)

        if template == '':
            cv2.imshow(template, image)
            cv2.waitKey()
        return boxes

    def find_template_in_prepared_image(self, image: Any, template: str, threshold: float = 0.7):
        res = cv2.matchTemplate(image, TEMPLATES[template], cv2.TM_CCOEFF_NORMED)
        loc = numpy.where(res >= threshold)
        template_width, template_height = TEMPLATES[template].shape[::-1]
        boxes = []
        for pt in zip(*loc[::-1]):
            if pt[0] < SCREEN_WIDTH * .85:
                boxes.append([pt[0], pt[1], pt[0] + template_width, pt[1] + template_height])
                cv2.rectangle(image, pt, (pt[0] + template_width, pt[1] + template_height), (50, 50, 50), 2)

        # cv2.imshow(template, image)
        # cv2.waitKey()
        return boxes

    def get_fps(self):
        fps_image = self.image.crop(COORDINATES['FPS'])
        cv_image = self.prepare_for_ocr(fps_image)
        # Example: 'FPS 30.0 - 33.3ms\n\x0c'
        fps_values = pytesseract.image_to_string(cv_image).split(' - ')
        fps = fps_values[0].split(' ')[1]
        render_time = fps_values[1].split('ms')[0]
        return fps, render_time

    def get_bearing(self, location: Any = ((SCREEN_WIDTH / 2) - (SCREEN_WIDTH / 5),
                                           50,
                                           (SCREEN_WIDTH / 2) + (SCREEN_WIDTH / 5),
                                           80)):
        bearings = {'north': 0,
                    'bearing_15': 15,
                    'bearing_30': 30,
                    'northeast': 45,
                    'bearing_60': 60,
                    'bearing_75': 75,
                    'east': 90,
                    'bearing_105': 105,
                    'bearing_120': 120,
                    'southeast': 135,
                    'bearing_150': 150,
                    'bearing_165': 165,
                    'south': 180,
                    'bearing_195': 195,
                    'bearing_210': 210,
                    'southwest': 225,
                    'bearing_240': 240,
                    'bearing_255': 255,
                    'west': 270,
                    'bearing_285': 285,
                    'bearing_300': 300,
                    'northwest': 315,
                    'bearing_330': 330,
                    'bearing_345': 345}

        heading_image = self.image.crop(location)
        pillow_array = numpy.array(heading_image)
        cv2.imwrite('debug/header.png', pillow_array)
        cv_image = self.prepare_for_ocr(pillow_array, 'compass')
        cv2.imwrite('debug/header-prepared.png', cv_image)
        # cv2.imshow('heading', cv_image)
        # cv2.waitKey()

        bearing = None
        compass_left = None
        leftmost = None
        nearest_left = None
        nearest_right = None
        template_left = None
        headings = []

        boxes = self.find_template_in_prepared_image(cv_image, 'compass', threshold=0.75)
        if not boxes:
            #logging.debug("Could not find the compass for this frame.")
            #cv2.imwrite('debug/header-failed.png', cv_image)
            #return None
            compass_left = round(SCREEN_WIDTH / 5)
            headings.append(('compass', compass_left))
        else:
            boxes = imutils.object_detection.non_max_suppression((numpy.array(boxes)))
            compass_left = round((boxes[0][0] + boxes[0][2]) / 2)
            headings.append(('compass', compass_left))

        for template in ('north', 'northeast', 'northwest', 'east', 'west', 'south',
                         'southeast', 'southwest', 'bearing_15', 'bearing_30', 'bearing_60', 'bearing_75',
                         'bearing_105', 'bearing_120', 'bearing_150', 'bearing_165', 'bearing_195', 'bearing_210',
                         'bearing_240', 'bearing_255', 'bearing_285', 'bearing_300', 'bearing_330', 'bearing_345'):
            boxes = self.find_template_in_prepared_image(cv_image, template, threshold=0.85)

            if boxes:
                boxes = imutils.object_detection.non_max_suppression((numpy.array(boxes)))

                template_left = round((boxes[0][0] + boxes[0][2]) / 2)
                headings.append((template, template_left))

        cv2.imwrite('debug/header-detected.png', cv_image)

        headings.sort(key=lambda x: x[1])

        for index, h in enumerate(headings):
            if h[0] == 'compass':
                if index >= 1:
                    nearest_left = headings[index - 1]
                if index < len(headings) - 1:
                    nearest_right = headings[index + 1]

        if nearest_left and nearest_right:
            degrees = abs(bearings[nearest_left[0]] - bearings[nearest_right[0]])
            # print(bearings[nearest_left[0]], bearings[nearest_right[0]])
            if degrees > 180:
                degrees = 360 - degrees

            compass_offset = compass_left - nearest_left[1]  # Pixel distance between compass and nearest left
            total_distance = nearest_right[1] - nearest_left[1]
            if total_distance == 0:
                return None
            degrees_past = round(compass_offset / total_distance * degrees)

            bearing = (bearings[nearest_left[0]] + degrees_past) % 360
            logging.debug(f"Detected bearing of {bearing} with nearest left {nearest_left} and nearest right {nearest_right}")
        elif nearest_left or nearest_right:
            fifteen_degrees = round(SCREEN_WIDTH / 27.5)
            if nearest_left:
                compass_offset = compass_left - nearest_left[1]
                degrees_past = round(compass_offset / fifteen_degrees)
                bearing = (bearings[nearest_left[0]] + degrees_past) % 360
            else:
                compass_offset = nearest_right[1] - compass_left
                degrees_past = round(compass_offset / fifteen_degrees)
                bearing = (bearings[nearest_right[0]] - degrees_past) % 360
            logging.debug(f"Single value approximation of bearing: {bearing}")
        else:
            logging.debug("Failed bearing detection")
            cv2.imwrite('debug/header-failed.png', cv_image)

        return bearing

    def get_interactable(self, location: Any) -> str:
        interactable_image = self.image.crop((location[0], location[1], location[0] + (SCREEN_WIDTH / 4), location[3]))
        cv_image = self.prepare_for_ocr(interactable_image, 'interactable')

        interactable = self.clean_ocr_text(pytesseract.image_to_string(cv_image, config=TESSERACT_CONFIG))
        return interactable

    def get_location(self):
        # This would be better replaced by referencing position on a map.
        location_image = self.image.crop(((SCREEN_WIDTH / 2) - (SCREEN_WIDTH / 6),
                                          83,
                                          (SCREEN_WIDTH / 2) + (SCREEN_WIDTH / 6),
                                          97))
        cv_image = self.prepare_for_ocr(location_image, 'interactable')

        location_name = self.clean_ocr_text(pytesseract.image_to_string(cv_image, config=TESSERACT_CONFIG))

        return location_name

    def get_position(self):
        logging.debug(f"get_position()")
        position_image = self.image.crop(COORDINATES['Position'])
        cv_image = self.prepare_for_ocr(position_image, 'overlay')
        # cv2.imshow('Position', cv_image)
        # cv2.waitKey()

        position_values = pytesseract.image_to_string(cv_image, config=TESSERACT_CONFIG).replace(',.', '.')

        position = re.search(r'(\d+?[,.]\d+?)[^\d]+?(\d+?[,.]\d+?)[^\d]+?(\d+?[,.]\d+)', position_values)
        if position is None:
            return None, None, None

        position_x = self.clean_ocr_number(position.group(1))
        position_y = self.clean_ocr_number(position.group(2))
        position_z = self.clean_ocr_number(position.group(3))

        logging.debug(f"/get_position()")

        return position_x, position_y, position_z

    def load_templates(self, template_list):
        global TEMPLATES

        for template in template_list:
            img = cv2.imread(f'templates/{template}_template.png')
            if template not in SIZES:
                SIZES[template] = {}
            SIZES[template]['height'], SIZES[template]['width'], _ = img.shape
            img = self.prepare_for_ocr(img, template)
            # cv2.imwrite(f"debug/template-{template}.png", img)
            self.prepared_images = {}

            TEMPLATES[template] = img

    @staticmethod
    def paint_hsv_to_opencv(hue, saturation, luminosity):
        return round(hue * 179 / 240), round(saturation * 255 / 240), round(luminosity * 255 / 240)

    def prepare_for_ocr(self, image_array: Any = None, template: str = ''):
        # logging.debug(f"prepare_for_ocr(image, {template})")
        if image_array is None:
            image_array = self.image_array
        cv_image = None
        if template:
            lower_bound = None
            upper_bound = None
            if template not in BOUNDS:
                lower_bound = BOUNDS['default']['lower']
                upper_bound = BOUNDS['default']['upper']
            else:
                lower_bound = BOUNDS[template]['lower']
                upper_bound = BOUNDS[template]['upper']
            hash_key = (tuple(lower_bound.flatten()), tuple(upper_bound.flatten()))
            if hash_key in self.prepared_images:
                return self.prepared_images[hash_key]

            original = image_array.copy()
            cv_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
            lower_range = NewWorldScreenshot.paint_hsv_to_opencv(*hash_key[0])
            upper_range = NewWorldScreenshot.paint_hsv_to_opencv(*hash_key[1])
            mask = cv2.inRange(cv_image, lower_range, upper_range)
            cv2.imwrite('debug/mask.png', mask)
            cv_image = cv2.bitwise_and(original, original, mask=mask)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            # cv_image = cv2.bitwise_not(cv_image)

            self.prepared_images[hash_key] = cv_image
        else:
            cv_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)

        # logging.debug(f"/prepare_for_ocr()")
        return cv_image

    def take(self, title: str = "New World", bring_to_front: bool = False) -> Any:
        logging.debug(f"screenshot_window({title}, {bring_to_front})")
        current_hwnd = win32gui.GetForegroundWindow()
        hwnd = win32gui.FindWindow(None, title)
        if not hwnd:
            raise ValueError

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        if bring_to_front and hwnd != current_hwnd:
            win32gui.SetForegroundWindow(hwnd)

        hdesktop = win32gui.GetDesktopWindow()
        window_device_context = win32gui.GetWindowDC(hdesktop)
        device_context = win32ui.CreateDCFromHandle(window_device_context)
        compatible_device_context = device_context.CreateCompatibleDC()
        data_bitmap = win32ui.CreateBitmap()
        data_bitmap.CreateCompatibleBitmap(device_context, width, height)
        compatible_device_context.SelectObject(data_bitmap)
        compatible_device_context.BitBlt((0, 0), (width, height), device_context, (left, top), win32con.SRCCOPY)
        data_bitmap.SaveBitmapFile(compatible_device_context, 'debug/screenshot.bmp')
        raw_image = numpy.fromstring(data_bitmap.GetBitmapBits(True), dtype=numpy.uint8)
        self.image = PIL.Image.frombuffer('RGB', (width, height), raw_image, 'raw', 'RGBX', 0, 1)
        self.image_array = numpy.array(self.image)
        self.prepared_images = {}
        device_context.DeleteDC()
        compatible_device_context.DeleteDC()
        win32gui.ReleaseDC(hdesktop, window_device_context)
        win32gui.DeleteObject(data_bitmap.GetHandle())

        if bring_to_front and hwnd != current_hwnd:
            # <Bizarre workaround for SetForegroundWindow failing>
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            # </Bizarre workaround for SetForegroundWindow failing>
            win32gui.SetForegroundWindow(current_hwnd)

        logging.debug(f"/screenshot_window")

        return self.image
