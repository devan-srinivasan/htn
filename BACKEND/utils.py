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
class GenerateNeuralResponse(BaseModel):
    #One output - suggestions
    suggestions : str = Field(description = '''
                              You are a bot. You will have access to what I am paying attention to. You also will have information to what I
                              do or don't want to do and why, as well as brain state. This will help you understand what I know and what I'm struggling with.
                              Use these to make suggestions in the field I'm working in that 10x my task performance.

                              For example, if I was an author writing a book, you could provide ideas for new plot directions. You would be CREATIVE.
                              If I was a student solving a math problem, you could provide how to arrive at the solution to that given prolbem and what formulas to use. You would be LOGICAL.

                              Switch between these modes as I change and my problems change.''')
                              
                            # Everything should be related to the originals ubject - science aly pani, ali 

                            # #   You are a bot with access to what I'm looking at. I could be looking at text, images, or something else.
                            # #   Use the information you can see to make suggestions.

                            # #   You are a bot. You'll see what I'm actively looking at with my vision; generally and specifically (like a specific piece of text or problem)
                            # #   Based on this new information you have acquired, as well as information (RUSSELL VECTOR) about the brain state, generate closely relatedif I am motivated or not,
                            # #   brainstorm ideas, suggestions, mindsets, and more tailored advice to skyrocket SPECIFICALLY what I do. No random stuff.


                              
                            #   YOU ARE A BOT. YOU WILL ADOPT PERSONALITY CHARACTERISTICS BASED ON THE BELOW:

                            #   THIS IS WHAT YOU WILL BE GIVEN:
                            #   1. Particular words, concepts, and tasks I have paid extreme attention to - seemingly of HIGH IMPORTANCE to me.
                            #   2. General information about the topics I am interested in.
                            #   3. A vector depicting user brain state. The x-coordinate is optimism and satisfaction. The y-coordinate is attentiveness and drive.
                              
                            #   THIS IS YOUR OBJECTIVE:
                            #   Based on my specialized subject, field, and what my attitude seems to be based on provided pupil data, generate A RESPONSE THAT WILL HELP ME DO THEIR TASK 10X BETTER.
                            #   This can be - instructions, step-by-step walkthroughs of problems, ideas, things you might think are useful.
                              
                            #   CHANGE HOW YOU RESPOND based on emotional state. More attentive? Detailed, step-by step. Less attentive? Abstract, experimental.
                              
                            #   DO YOUR BEST.)

#Validators
denoiser_validator = PydanticOutputParser(pydantic_object = DeNoiseSummary)
generator_validator = PydanticOutputParser(pydantic_object = GenerateNeuralResponse)

#Prompt formats
denoiser_prompt = PromptTemplate(
    template = "\n'''{format_instructions}'''. The notes are as follows. '''{query}'''",
    input_variables = ["query"],
    partial_variables = {"format_instructions" : denoiser_validator.get_format_instructions()}
)
generator_prompt = PromptTemplate(
    template = "You are a dilligent bot that actively seeks ways to help me, based on my brain and emotional state. Adhere to the following and return your suggestions: '''{response_instructions}'''\n\n'''GENERAL USER ATTENTION: {general_user_attention}'''\n\n'''SPECIFIC USER ATTENTION: {specific_user_attention}'''\n\n'''EMOTIONAL VECTOR: {russell_vector}'''\n\n'''QUESTION:{question}\nSUMMARIES:{summaries}'''",
    input_variables = ["general_user_attention", "specific_user_attention", "russell_vector", "question", "summaries"],
    partial_variables = {"response_instructions" : generator_validator.get_format_instructions()}
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

#EYE PUPIL DIAMETER TRACKING - given an (x, y) scaled vector in the Russel's Circumplex Model of Effects and previous context, generate an LLM Response
#Setup function for the first conversation
def setupLLM(instance, notes_dir : str):
    print("NOTES DIRECTORY:", notes_dir)
    ALL_NOTES = DirectoryLoader(notes_dir, glob = "**/*.txt", loader_cls = TextLoader).load()
    #Generate embeddings
    vector_embeddings = OpenAIEmbeddings()
    #Set vectorstore
    instance["vectorstore"] = Chroma.from_documents(ALL_NOTES, vector_embeddings)
    #Set memory
    instance["memory"] = ConversationBufferMemory(memory_key = "chat_history", return_messages = True)
    #Set chain - inject initial prompt with general instructions
    instance["chain"] = RetrievalQAWithSourcesChain.from_chain_type(llm = OpenAI(temperature = 0), retriever = instance["vectorstore"].as_retriever(),
                                                                    chain_type = "stuff", chain_type_kwargs = {"prompt" : generator_prompt})
#Generate actual LLM recommendations and insights
def generateLLMRecommendations(instance : dict, general_answer : str, specific_answer : str, brain_state_coords : tuple):
    #Get response
    
    response = instance["chain"]({"general_user_attention" : general_answer, "specific_user_attention" : specific_answer, "russell_vector" : brain_state_coords, "question" : "GENERATE YOUR SUGGESTIONS AS PER THE INSTRUCTIONS AND PREVIOUS DATA."})
    #Print response
    print("RESPONSE", response)
    return response

