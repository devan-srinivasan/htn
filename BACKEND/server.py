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

#Init server
NOTE_SERVER = Flask(__name__)
#Note screenshot names
NOTE_SCREENSHOT_NAMES = []

#Routes
@NOTE_SERVER.route("/")
def response():
    return "Root dir accessed"

#Get response
@NOTE_SERVER.route("/save-note")
def save_note():
    #Get screenshot of current text
    img = pyautogui.screenshot()
    #Convert to PIL image that can be written to disk
    saved_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    #Save to disk
    img_name = "NOTE_" + str(len(NOTE_SCREENSHOT_NAMES)) + ".png"
    cv2.imwrite(img_name, saved_img)
    #Extract text from screenshot
    print("TEXT LOADING PROGRESS")
    pytesseract.tesseract_cmd='C:\Program Files\Tesseract-OCR\\tesseract.exe'
    img_text = pytesseract.image_to_string(Image.open(img_name))
    #Filter image text - replace all newlines and special characters
    img_text = img_text.replace("\n", "")
    img_text = img_text.replace("@", "")
    img_text = img_text.replace("©", "")
    #Print text
    print("IMAGE TEXT:", img_text)
    #Save image and text to Google Docs
    createGoogleDoc(extracted_text = img_text, image_filepath = img_name)
    #Get text from AdHawk dataset
    # getADText()
    message = "We've successfully saved this note to Google Docs."
    return {"success_message": message}

# @NOTE_SERVER.route("/auth")
# def auth() -> Union[Tuple[str, int], werkzeug.Response]:
#     # Check these two values
#     print(flask.request.args.get('state'), flask.session.get('_google_authlib_state_'))

#     token = oauth.google.authorize_access_token()
#     user = oauth.google.parse_id_token(token)
#     flask.session["user"] = user
#     return flask.redirect("/")

#Serve
if __name__ == "__main__":
        #Port number
    port_number = 3001
    from waitress import serve
    serve(NOTE_SERVER, host = "localhost", port = port_number)
    #Print
    print("NOTE SERVER RUNNING ON PORT {}.".format(port_number))
    #Run server
    # waitress.serve(LLM_SERVER, port = port_number)
    # NOTE_SERVER.run(port = port_number, debug = True)