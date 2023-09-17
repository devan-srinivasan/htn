#For Google Docs / Google Drive Integration
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
#For initial authentication
from google_auth_oauthlib.flow import InstalledAppFlow
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
#Get scopes for the API
PROJECT_SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
#Path to credentials
credentials_filepath = "client_secrets.json"
#Authentication flow
authentication_flow = InstalledAppFlow.from_client_secrets_file(credentials_filepath, scopes = PROJECT_SCOPES)
#Begin flow for token transfer + authorization
CREDENTIALS = authentication_flow.run_local_server()

#SET UP CLIENTS FOR GOOGLE DOCS AND DRIVE
google_drive_client = build("drive", "v3", credentials = CREDENTIALS)
google_docs_client = build("docs", "v1", credentials = CREDENTIALS)

#Create google doc with notes
def createGoogleDoc(extracted_text : str, image_filepath : str):
    #Create new Google doc
    new_document = google_docs_client.documents().create().execute()
    new_document_id = new_document["documentId"]
    #Format request
    request = [
        {
            "insertText" : {
                "location" : {
                    "index" : 1,
                },
                "text" : extracted_text,
            },
        },
    ]
    #Send and complete request
    google_docs_client.documents().batchUpdate(documentId = new_document_id, body = {"requests" : request}).execute()

#Extract text from image
def extractText(image_file_path : str):
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