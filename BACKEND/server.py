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
from utils import extractText, generateNotes, setupLLM, generateLLMRecommendations
import time
import math

#Init server
NOTE_SERVER = Flask(__name__)
#Create Dictionary to hold Conversation Data
CONVERSATION_USER_INSTANCE = {}
#Create a dictionary for all details regarding notes - in particular, document ID and current slide number
NOTE_DETAILS = {"DOCUMENT_ID" : None, "CURRENT_SLIDE_NUMBER" : 1}
#Note screenshot names - complete and partial
COMPLETE_NOTE_SCREENSHOT_NAMES = []
PARTIAL_NOTE_SCREENSHOT_NAMES = []
#Directory of storage for augmented notes - both complete and fragmented
DIRECTORY_OF_NOTES = "./DIRECTORY_OF_NOTES/"
#Keep a history of all augmented notes - both complete and cropped
#This will serve as context for the model
AUGMENTED_NOTE_HISTORY = {"COMPLETE" : [], "INCOMPLETE" : []}
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
    #Save both completed notes and cropped notes to the directory
    with open(DIRECTORY_OF_NOTES + "_SLIDE_" + str(NOTE_DETAILS["CURRENT_SLIDE_NUMBER"]) + ".txt", "w") as save_notes_file:
        #Introduce headers between both strings and save
        FINAL_NOTE = f"COMPLETE NOTES:\n\n{augmented_complete_notes_text}\n\nNOTES THAT USERS PAID HIGH ATTENTION TO:\n\n{augmented_cropped_notes_text}"
        #Save to file
        save_notes_file.write(FINAL_NOTE)
    #Append both augmented text strings to arrays
    AUGMENTED_NOTE_HISTORY["COMPLETE"].append(augmented_complete_notes_text)
    AUGMENTED_NOTE_HISTORY["INCOMPLETE"].append(augmented_cropped_notes_text)
    #Log to terminal
    print("AUGMENTED COMPLETED NOTES:", augmented_complete_notes_text)
    print("AUGMENTED CROPPED NOTES:",  augmented_cropped_notes_text)
    #Prepare augmented notes to be written on Google Docs
    augmented_notes = f"Our notes for this slide:\n\n{augmented_complete_notes_text}\n\nWhat we think you were most intrigued by (with more thorough explanation):\n\n{augmented_cropped_notes_text}"
    #Save image and text to Google Docs - provide all augmented notes, filepath of image to be saved, and note details (document ID and slide number)
    createGoogleDoc(extracted_text = augmented_notes, image_filepath = img_name, note_details = NOTE_DETAILS)
    message = "We've successfully enhanced and saved your notes to Google Docs."
    return {"success_message": message}

#Receive eye pupil measurements and fuel that into the LLM
@NOTE_SERVER.route("/pupil-data", methods = ["POST"])
def get_pupil_data():
    #Receive both outliers and non-outliers
    outliers = request.json["outliers"]
    nonoutliers = request.json["nonoutliers"]
    #Compare ratio of outliers to non-outliers - rate of change in pupil dilation
    #If this ratio is high (perhaps above 0.75), epinephrine levels are relatively high, while below indicates decreased activation.
    #Pinpoint this exactly
    activation_threshold = 0.75
    #This indicates level of excitement / arousal -> less change = more excitement
    ratio_o_n = len(nonoutliers)/len(outliers)
    #Get the average of all outliers - do they tend to be above or below the nonoutliers?
    #In other words, is pupil dilation greater or less than the average?
    #This indicates valence - positive or negative emotion
    average_outliers = sum(outliers)/len(outliers)
    #Check for signs and magntitude - if ratio is above 0.75, epinephrine levels are relatively high and vice versa
    #If the average outliers are positive or negative, this implies impacts on serotonin levels
    #Translate ratio_o_n down by the activation threshold for translation into vector space and subsequent embedding
    ratio_o_n -= activation_threshold
    #If less than zero, snap to zero -> cannot be negative
    if ratio_o_n < 0: ratio_o_n = 0
    #Final (x, y) coordinates
    RUSSEL_VECTOR_SPACE_COORDINATES = (average_outliers, ratio_o_n)
    #If this is the first time an LLM response is being generated, setup LLM
    #Determine this via the slide number
    if (NOTE_DETAILS["CURRENT_SLIDE_NUMBER"] == 1): setupLLM(instance = CONVERSATION_USER_INSTANCE, notes_dir = DIRECTORY_OF_NOTES)
    #Query the model for suggestions, providing the most recent general and specific attented text as well as critical brain state information
    model_response = generateLLMRecommendations(instance = CONVERSATION_USER_INSTANCE, general_answer = AUGMENTED_NOTE_HISTORY["COMPLETE"][-1],
                                                specific_answer = AUGMENTED_NOTE_HISTORY["INCOMPLETE"][-1], brain_state_coords = RUSSEL_VECTOR_SPACE_COORDINATES, notes_dir = DIRECTORY_OF_NOTES)
    #Return the model's response
    return {"model_response" : model_response}

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