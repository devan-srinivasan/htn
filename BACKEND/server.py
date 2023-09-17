from flask import Flask
import waitress
from flask import request
from flask import session
import numpy as np
import cv2
import pyautogui
from PIL import Image
from pytesseract import pytesseract
from utils import createGoogleDoc
from utils import extractText, generateNotes
import time
import math

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
#Create a dictionary for all details regarding notes - in particular, document ID and current slide number
NOTE_DETAILS = {"DOCUMENT_ID" : None, "CURRENT_SLIDE_NUMBER" : 1}

#Routes
@NOTE_SERVER.route("/")
def response():
    return "Root dir accessed"

#Get response
@NOTE_SERVER.route("/save-note", methods=["POST", "GET"])
def save_note():
    if request.method == "GET": data = request.get_json
    
    #Get screenshot of current text
    time.sleep(5)
    img = pyautogui.screenshot()
    #Convert to numpy array and then to a PIL image that can be written to disk
    saved_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    complete_screenshot_filename = "COMPLETE_SCREENSHOT_" + str(len(COMPLETE_NOTE_SCREENSHOT_NAMES)) + ".png"
    cv2.imwrite(complete_screenshot_filename, saved_img)
    #Get complete text from image
    complete_text = extractText(image_file_path = complete_screenshot_filename)
    #Append name to screenshot list
    COMPLETE_NOTE_SCREENSHOT_NAMES.append(complete_screenshot_filename)

    #Get gaze direction from AdHawk dataset and crop the image accordingly
    #9-quadrant-based system
    #horizontal_direction, vertical_direction = getScreenGazeDirection()
    vertical_direction = "up"
    horizontal_direction = "right"
    #Get center of region the user is looking at
    center_point = DIRECTION_MATRIX[vertical_directions.index(vertical_direction)][horizontal_directions.index(horizontal_direction)]
    #Crop the screen shot to ~60% of the screen size around the center point
    #Crop percentage for vertical and horizontal directions
    vertical_crop_percent = 0.5
    horizontal_crop_percent = 0.3
    #convert saved_img to PIL image
    PIL_Image = Image.fromarray(saved_img)
    #Left, top, right, bottom
    left_crop = max(center_point[1] - (vertical_crop_percent * screen_size[0]), 0)
    top_crop = max(center_point[0] - (horizontal_crop_percent * screen_size[1]), 0)
    right_crop = min(center_point[1] + (vertical_crop_percent * screen_size[0]), screen_size[0])
    down_crop = min(center_point[0] + (horizontal_crop_percent * screen_size[1]), screen_size[1])
    cropped_img = PIL_Image.crop((left_crop, top_crop,
                                  right_crop, down_crop))
    #Save to disk
    img_name = "PARTIAL_NOTE_" + str(len(PARTIAL_NOTE_SCREENSHOT_NAMES)) + ".png"
    cropped_img.save(img_name)
    #Get cropped region text
    cropped_region_text = extractText(img_name)
    #Log
    print("CROPPED REGION TEXT:", cropped_region_text)
    #Get LLM-augmented notes - do this based on the text retreived from the complete image and the cropped iamge
    augmented_complete_notes_text = generateNotes(note_text = complete_text)
    augmented_cropped_notes_text = generateNotes(note_text = cropped_region_text)
    print("AUGMENTED COMPLETED NOTES:", augmented_complete_notes_text)
    print("AUGMENTED CROPPED NOTES:",  augmented_cropped_notes_text)
    #Prepare augmented notes to be written on Google Docs
    augmented_notes = f"Our notes for this slide:\n\n{augmented_complete_notes_text}\n\nWhat we think you were most intrigued by (with some more thorough explanation):\n\n{augmented_cropped_notes_text}"
    #Save image and text to Google Docs - provide all augmented notes, filepath of image to be saved, and note details (document ID and slide number)
    createGoogleDoc(extracted_text = augmented_notes, image_filepath = img_name, note_details = NOTE_DETAILS)
    message = "We've successfully enhanced and saved your notes to Google Docs."
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