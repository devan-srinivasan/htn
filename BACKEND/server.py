from flask import Flask
import waitress
from flask import request
from flask import session
import numpy as np
import cv2
import pyautogui
from PIL import Image
from pytesseract import pytesseract
# from utils import createGoogleDoc
from utils import extractText, generateNotes
import time

#Init server
NOTE_SERVER = Flask(__name__)
#Note screenshot names - complete and partial
COMPLETE_NOTE_SCREENSHOT_NAMES = []
PARTIAL_NOTE_SCREENSHOT_NAMES = []
#List all possible directions
vertical_directions = ["up", "center", "down"]
horizontal_directions = ["left", "center", "right"]
#Get screen size
screen_size = pyautogui.size()
#Divide by three vertically and horizontally
vertical_interval = screen_size[1] // 3
horizontal_interval = screen_size[0] // 3
#Calculate exact pixel position of each combination of directions - place in 3x3 matrix
DIRECTION_MATRIX = [[1, 1, 1], [1, 1, 1,], [1, 1, 1]]
#Iterate and populate direction matrix
for i, vertical_direction in enumerate(vertical_directions):
    for j, horizontal_direction in enumerate(horizontal_directions):
        #To get the correct center value for each quadrant, multiply i + 1 by the vertical interval and j + 1 by the horizontal interval
        DIRECTION_MATRIX[i][j] = ((i + 1) * vertical_interval, (j + 1) * horizontal_interval)

#Routes
@NOTE_SERVER.route("/")
def response():
    return "Root dir accessed"

#Get response
@NOTE_SERVER.route("/save-note")
def save_note():
    #Get screenshot of current text
    time.sleep(5)
    img = pyautogui.screenshot()
    #Convert to numpy array and then to a PIL image that can be written to disk
    saved_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    #Write complete screenshot to disk
    PIL_saved_img = Image.fromarray(saved_img.astype("uint8"), "RGB")
    complete_screenshot_filename = "COMPLETE_SCREENSHOT_" + str(len(COMPLETE_NOTE_SCREENSHOT_NAMES)) + ".png"
    PIL_saved_img.save("COMPLETE_SCREENSHOT_" + str(len(COMPLETE_NOTE_SCREENSHOT_NAMES)) + ".png")
    #Append name to screenshot
    COMPLETE_NOTE_SCREENSHOT_NAMES.append(complete_screenshot_filename)
    #Extract text
    complete_text = extractText(image_file_path = complete_screenshot_filename)
    print("COMPLETED TEXT:", complete_text)
    #Get gaze direction from AdHawk dataset and crop the image accordingly
    #9-quadrant-based system9
    #horizontal_direction, vertical_direction = getScreenGazeDirection()
    vertical_direction = "down"
    horizontal_direction = "right"
    #Get center of region the user is looking at
    center_point = DIRECTION_MATRIX[vertical_directions.index(vertical_direction)][horizontal_directions.index(horizontal_direction)]
    #Crop the screen shot to ~60% of the screen size around the center point
    #Crop percentage for vertical and horizontal directions
    vertical_crop_percent = 0.6
    horizontal_crop_percent = 0.25
    #Left, top, right, bottom
    cropped_img = PIL_saved_img.crop((center_point[1] - (vertical_crop_percent * screen_size[1]), center_point[0] - (horizontal_crop_percent * screen_size[0]),
                                      center_point[1] + (vertical_crop_percent * screen_size[1]), center_point[0] + (horizontal_crop_percent * screen_size[0])))
    #Save to disk
    img_name = "PARTIAL_NOTE_" + str(len(PARTIAL_NOTE_SCREENSHOT_NAMES)) + ".png"
    cropped_img.save(img_name)
    #Get cropped region text
    cropped_region_text = extractText(img_name)
    #Get LLM-augmented notes - do this based on the full generation
    augmented_notes_text = generateNotes(note_text = complete_text)
    print("AUGMENTED NOTES TEXT:", augmented_notes_text)
    #Save image and text to Google Docs
    # createGoogleDoc(extracted_text = augmented_notes_text, image_filepath = img_name)
    message = "We've successfully saved this note to Google Docs."
    return {"success_message": message}

#Serve
if __name__ == "__main__":
    #Port number
    port_number = 3001
    from waitress import serve
    #Print
    print("NOTE SERVER RUNNING ON PORT {}.".format(port_number))
    #Run server
    serve(NOTE_SERVER, host = "localhost", port = port_number)
    # NOTE_SERVER.run(port = port_number, debug = True)