#For Google Docs / Google Drive Integration
import os
#For image processing and text generation
from PIL import Image
from pytesseract import pytesseract

#ALL MACHINE LEARNING LIBRARIES

#API key
import Keys
import openai
#For Langchain context
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory
#For embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
#For model
from langchain.llms import OpenAI
#For vectorstore
from langchain.vectorstores import Chroma
#For dataloading
from langchain.document_loaders import DirectoryLoader, TextLoader
#Prompt Templates
from langchain.prompts import PromptTemplate
#Parsers
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List

#For the current date (supplying the notes header)
from datetime import datetime
current_date = datetime.today().strftime("%B %d, %Y")

#Define all types of prompt templates

#TEMPLATE ONE - Generate Summarized / Refined version of notes based on all text.
class DeNoiseSummary(BaseModel):
    #Just one summary
    summary : str = Field(description = "Go through the user's notes and generate what the notes were trying to say. Filter all symbols.")
#TEMPLATE TWO - Generate specialized answers based on pupil dilation / alterness / number of blinks

#Validators
denoiser_validator = PydanticOutputParser(pydantic_object = DeNoiseSummary)

#Prompt formats
denoiser_prompt = PromptTemplate(
    template = "You are an assisstant fixing student notes. Fix the following and return a summary.\n'''{format_instructions}'''. The notes are as follows. '''{query}'''",
    input_variables = ["query"],
    partial_variables = {"format_instructions" : denoiser_validator.get_format_instructions()}
)

#Set API key as environment veriable
os.environ["OPENAI_API_KEY"] = Keys.OPENAI_SECRET_KEY
#Set default parameters for PyTesseract
pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\\tesseract.exe'

#Create google doc with notes
def createGoogleDoc(extracted_text : str, image_filepath : str, note_details : dict, google_docs_client):
    #If the Document ID is None, create a new document and add text to that
    #Otherwise, leverage the pre-existing Document ID
    if note_details["DOCUMENT_ID"] == None:
        print(f"CURRENT STATUS OF DOCUMENT ID: {note_details['DOCUMENT_ID']} - CREATING NEW DOCUMENT.")
        new_document = google_docs_client.documents().create().execute()
        note_details["DOCUMENT_ID"] = new_document["documentId"]
    print("\n\nDOCUMENT ID:", note_details["DOCUMENT_ID"])
    #Add the slide number at the beginning of each statement
    #Introduce two newline characters if the slide number is above 1; otherwise introduce page header with current date
    if note_details["CURRENT_SLIDE_NUMBER"] == 1: sentence_start = f"NOTES - {current_date}:\n\n".upper()
    else: sentence_start = "\n\n"
    slide_formatted_text = sentence_start + f"SLIDE {note_details['CURRENT_SLIDE_NUMBER']} NOTES:\n\n" + extracted_text
    #Get current text of the document from the id - if this is a new document, this result will be blank
    existing_document_object = google_docs_client.documents().get(documentId = note_details["DOCUMENT_ID"]).execute()
    #Get text and index (length of the retrieved body)
    existing_document_text = existing_document_object.get("body").get("content")
    index_to_add = 1
    #Create object for new notes
    new_notes = {
        "paragraph" : {
            "elements" : [
                {
                    "textRun" : {
                        "content" : slide_formatted_text,
                    }
                }
            ]
        }
    }
    #Insert the new phrase at the slide_number - 1 position
    # existing_document_text.insert(index_to_add, new_notes)
    #Modify the end document
    #Format request
    request = [
        {
            "insertText" : {
                # "location" : {
                #     "index" : index_to_add,
                # },
                "text" : slide_formatted_text,
                "endOfSegmentLocation" : {}
            },
        },
    ]
    #Send and complete request
    google_docs_client.documents().batchUpdate(documentId = note_details["DOCUMENT_ID"], body = {"requests" : request}).execute()
    #Increment slide number
    note_details["CURRENT_SLIDE_NUMBER"] += 1

#Extract text from image
def extractText(image_file_path : str):
    from sys import platform
    if platform == "darwin":
        pytesseract.tesseract_cmd = '/opt/homebrew/Cellar/tesseract/5.3.2_1/bin/tesseract'
    elif platform == "win32":
        pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\\tesseract.exe'
    
    img_text = pytesseract.image_to_string(Image.open(image_file_path))
    #Filter image text - replace all newlink/;pes and special characters
    img_text = img_text.replace("\n", "")
    img_text = img_text.replace("@", "")
    img_text = img_text.replace("©", "")
    #Return text
    return img_text

#Generate notes based on imperfect input text (artificially augmented notes)
def generateNotes(note_text : str):
    #AI should exhibit zero creativity
    model = OpenAI(temperature = 0)
    #Configure input to model
    instructed_model_input = denoiser_prompt.format_prompt(query = note_text)
    #Get output
    # model_output = model("Chemistry is the subject of AUFIOSJFLSJOFIS atoms and their properties - namely, how they interact with one another in a controlled fashion known as reactions.")
    model_output = model(instructed_model_input.to_string())
    #Parse
    parsed_model_output = dict(denoiser_validator.parse(model_output))["summary"]
    print("PARSED MODEL OUTPUT:", parsed_model_output)
    print("TYPE:", type(parsed_model_output))
    #Return
    return parsed_model_output