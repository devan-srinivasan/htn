from flask import Flask, make_response
from flask_cors import CORS
import waitress
from flask import request
from flask import session
import secrets
import uuid
import json
#Import Query Processing Fuctionality
from utils import setupServer, setupConversation, queryModel, extractDrugName
#For OpenAI API
import Keys
import os

#Declare application
LLM_SERVER = Flask(__name__)
LLM_SERVER.secret_key = secrets.token_hex(32)
#Allow frontend origin requests
CORS(LLM_SERVER)

#Session lifetime
LLM_SERVER.config["PERMANENT_SESSION_LIFETIME"] = 1800
#Dictionary to hold all session instances for users
ALL_USER_INSTANCES = {}
#Set API key as environment veriable
os.environ["OPENAI_API_KEY"] = Keys.OPENAI_SECRET_KEY
#Setup server - extract monograph text and create chunked summaries
monograph_dir = "PDF_MONOGRAPHS"
txt_save_dir = "TXT_MONOGRAPHS"
summaries_save_dir = "SUMMARIZED_MONOGRAPHS"
#Initialize vectorstore
VECTORSTORE = {"vectorstore" : None}
setupServer(data_dir = monograph_dir, txt_save_dir = txt_save_dir, summary_save_dir = summaries_save_dir)
#Define supported monographs and links
SUPPORTED_MONOGRAPHS = {
    "OZEMPIC" : "https://www.novonordisk.ca/content/dam/Canada/AFFILIATE/www-novonordisk-ca/OurProducts/PDF/ozempic-product-monograph.pdf"
}

#Set app routes

#Default route
@LLM_SERVER.route("/")
def response():
    return "Server Root Directory Accessed."

#For setting up the model and pre-loading all monographs, triggered when the application is initially rendered
@LLM_SERVER.route("/setup-model", methods = ["POST"])
def setup():
    #Get user ID
    user_id = request.json["userID"]
    #Begin new user session
    ALL_USER_INSTANCES[user_id] = {}
    #Setup conversation
    setupConversation(user_instance = ALL_USER_INSTANCES[user_id], vectorstore = VECTORSTORE, summaries_dir = summaries_save_dir)
    #Set flag confirming first response to true
    ALL_USER_INSTANCES[user_id]["first_response"] = True
    return {}, 200

#Generate Response for Query
@LLM_SERVER.route("/generate-LLM-response", methods = ["POST"])
def generate_ngram_dictionary():
    #Get user ID
    user_id = request.json["userID"]
    #Get input query
    user_query = request.json["query"]
    #Valid prompt flag - this should be true unless the given drug brand name is invalid
    #Lowercase for javascript frontend support
    valid_prompt = "true"
    #If the user ID is not currently registered in the session, do so and re-setup the conversation
    try: ALL_USER_INSTANCES[user_id]
    except KeyError: 
        ALL_USER_INSTANCES[user_id] = {}
        setupConversation(user_instance = ALL_USER_INSTANCES[user_id], vectorstore = VECTORSTORE, summaries_dir = summaries_save_dir)
        #Set first response flag to true (this will now be the user's first query after redeclaration)
        ALL_USER_INSTANCES[user_id]["first_response"] = True
    #Get current drug name if any (try except)
    try: 
        #Get Names
        general_name, brand_name = extractDrugName(query = user_query)
        print(f"GENERAL NAME: {general_name} BRAND NAME: {brand_name}")
        #Check if a drug name has already been saved within the conversation.
        # If yes, compare to names currently present in the conversation - if the names are different, state that the user must first clear the converstion before orienting to a different drug.
        # If not, create a new one and check that the drug is valid.
        try: 
            ALL_USER_INSTANCES[user_id]["brand_name"]
            print("SUCCEEDED.")
            #Compare to those currently present in the conversation - if the names are different, state that the user must first clear the converstion before orienting to a different drug.
            if brand_name != ALL_USER_INSTANCES[user_id]["brand_name"]:
                #Set response
                model_response = f'''It looks like you're trying to ask a question about a different drug than {ALL_USER_INSTANCES[user_id]["brand_name"]}. No problem! I'll be happy to help. Just restart the conversation.'''
                #Set valid prompt to false
                valid_prompt = "False"
                #Set citations to none
                model_citations = []
                #Return and send this response
                return {"model_response" : model_response, "model_citations" : model_citations, "monograph_link" : ALL_USER_INSTANCES[user_id]["monograph_link"],
                        "valid_prompt" : valid_prompt, "drug_general_name" : ALL_USER_INSTANCES[user_id]["general_name"], "drug_brand_name" : ALL_USER_INSTANCES[user_id]["brand_name"]}
        except KeyError:
            #Check if the current names are valid
            if brand_name.upper() in SUPPORTED_MONOGRAPHS.keys():
                #Save names
                ALL_USER_INSTANCES[user_id]["general_name"], ALL_USER_INSTANCES[user_id]["brand_name"] = general_name, brand_name
                #Get monograph link
                ALL_USER_INSTANCES[user_id]["monograph_link"] = SUPPORTED_MONOGRAPHS[ALL_USER_INSTANCES[user_id]["brand_name"].upper()]
            #Otherwise, send a response requesting questions regarding supported drug types.
            else:
                #Set model response with drug name and all currently supported drugs
                model_response = f'''Unfortunately, I don't know much about {brand_name}. Try searching your question online instead, or check out TheRounds platform. 
                                     As of now, I only have experience with the following drugs: {", ".join(list(SUPPORTED_MONOGRAPHS.keys()))}'''
                #Add period
                model_response = model_response + "."
                #Set valid prompt to false and citations to none
                valid_prompt = "false"
                model_citations = []
                #Send response
                return {"model_response" : model_response, "model_citations" : model_citations, "monograph_link" : "",
                        "valid_prompt" : valid_prompt, "drug_general_name" : "", "drug_brand_name" : ""}
    #If a Key or Index error has been raised, the query does not consist of a valid drug name.
    #If this is the first response, the model must re-prompt the user.
    except (KeyError, IndexError) as e:
        #Verify first response
        if ALL_USER_INSTANCES[user_id]["first_response"]:
            #Set model message asking for a re-prompt
            model_response = f'''Hey there! Unfortunately, it seems that your question isn't about a specific drug, so I'm not sure if I can be of help. Try asking a drug-specific question! Thanks.'''
            #Add period
            model_response = model_response + "."
            #Set valid prompt to false and citations to none
            valid_prompt = "false"
            model_citations = []
            #Send response
            return {"model_response" : model_response, "model_citations" : model_citations, "monograph_link" : "",
                    "valid_prompt" : valid_prompt, "drug_general_name" : "", "drug_brand_name" : ""}
    #Get model response
    #Understand why model provided 
    model_response, model_citations = queryModel(chain = ALL_USER_INSTANCES[user_id]["chain"], user_query = user_query)
    #Convert model citations to a list of individual page citations
    model_citations = [page_citation.strip() for page_citation in model_citations.split(",")]
    #Remove all elements with no page number
    filtered_citations = []
    for page_citation in model_citations: 
        #Flag to check if a number has been found
        string_has_number = False
        #Iterate over all string characters and search for a number
        for char in page_citation:
            #Set flag to true if found
            if char.isdigit(): string_has_number = True
        #If a number has been found, append.
        if string_has_number: filtered_citations.append(page_citation)
    #Set first response to False if True
    if ALL_USER_INSTANCES[user_id]["first_response"]: ALL_USER_INSTANCES[user_id]["first_response"] = False
    #Print currently stored names
    print("NAMES:", ALL_USER_INSTANCES[user_id]["general_name"], ALL_USER_INSTANCES[user_id]["brand_name"])

    #Return output
    return {"model_response" : model_response, "model_citations" : filtered_citations, "monograph_link" : ALL_USER_INSTANCES[user_id]["monograph_link"],
            "valid_prompt" : valid_prompt, "drug_general_name" : ALL_USER_INSTANCES[user_id]["general_name"], "drug_brand_name" : ALL_USER_INSTANCES[user_id]["brand_name"]}

#For resetting a user's conversation history once the application has been refreshed or closed
@LLM_SERVER.route("/reset-conversation", methods = ["POST"])
def reset_conversation():
    #Get userID
    userID = request.json["userID"]
    #Check to see if the vectorstore exists and has more than one ID
    if VECTORSTORE["vectorstore"] != None:
        #Iterate over all IDs and delete
        for id in VECTORSTORE["vectorstore"].get()["ids"]:
            VECTORSTORE["vectorstore"].delete(id)
    #Delete all corresponding information to the userID if it exists
    try: 
        ALL_USER_INSTANCES[userID]
        ALL_USER_INSTANCES.pop(userID)
    except KeyError: pass
    #Return
    return {}, 200

#Allow cross-origin requests
@LLM_SERVER.after_request
def set_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

#Run server on port 3001
if __name__ == "__main__":
    #Port number
    port_number = 3001
    #Print
    print("LLM Server Backend running on port {}.".format(port_number))
    #Run server
    # waitress.serve(LLM_SERVER, port = port_number)
    LLM_SERVER.run(port = port_number, debug = True)
     