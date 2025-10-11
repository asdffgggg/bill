import asyncio
import requests
import json
# from openai import OpenAI
import os
from dotenv import load_dotenv
from fasthtml.common import *
from fasthtml.components import Zero_md
from ollama import chat
from ollama import ChatResponse
from ollama import AsyncClient
import pymupdf
from requests_cache import CachedSession
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
import uuid
import time
from dataclasses import dataclass












load_dotenv()

app, rt = fast_app(
    static_path="public",
    hdrs=(
        Script(type="module", src="https://cdn.jsdelivr.net/npm/zero-md@3?register"),
        Script(src="https://cdn.jsdelivr.net/npm/htmx-ext-ws@2.0.2"),
        Link(rel="stylesheet", href="/index.css")
    )
)
SESSION = CachedSession("requests_cache", expire_after=300) # 5 minute expiration cache

# Connection information is stored in the following format:
# The key is a UUID
# The value is a dictionary: {
#   "last_time": UNIX_TIMESTAMP,
#   "messages": []
# }
CONNECTIONS = {
    
}

def get_bills(laws: Optional[int] = None):
    head = "https://api.congress.gov/"
    endpoint = "v3/bill" if not laws else f"v3/law/{laws}"
    apikey = os.getenv("CONGRESSAPIKEY")

    params = {
        "format": "json",
        "api_key": apikey
    }
    # Perform the GET request to the general bill endpoint
    response = SESSION.get(head + endpoint, params=params)
    bills = response.json()['bills']
    return bills

def get_congressional_bills(congress, _type):
    head = "https://api.congress.gov/"
    endpoint = f"v3/bill/{congress}/{_type}"
    apikey = os.getenv("CONGRESSAPIKEY")

    params = {
        "format": "json",
        "api_key": apikey
    }
    # Perform the GET request to the general bill endpoint
    return SESSION.get(head + endpoint, params=params).json()["bills"]

def find_bill(congress, number, _type):
    head = "https://api.congress.gov/"
    endpoint = f"v3/bill/{congress}/{_type}/{number}"
    apikey = os.getenv("CONGRESSAPIKEY")

    params = {
        "format": "json",
        "api_key": apikey
    }
    # Perform the GET request to the general bill endpoint
    return SESSION.get(head + endpoint, params=params).json()["bill"]

def get_pdf(bill_congress,bill_type,bill_number):
    head = "https://api.congress.gov/"
    apikey = os.getenv("CONGRESSAPIKEY")
    params = {
        "format": "json",
        "api_key": apikey
    }
    bill_congress = int(bill_congress)
    textpoint = f"v3/bill/{bill_congress}/{bill_type}/{bill_number}/text"
    reponse = SESSION.get(head + textpoint, params=params)
    print(reponse.json())
    while len(reponse.json()['textVersions']) == 0:
        bill_congress -= 1
        textpoint = f"v3/bill/{bill_congress}/{bill_type}/{bill_number}/text"
        reponse = SESSION.get(head + textpoint, params=params)
    try:
        pdf = reponse.json()['textVersions'][0]['formats'][1]['url']
        return pdf
    except:
        return ""
async def get_response_stream(url, input, id, send):
    r = SESSION.get(url)
    doc = pymupdf.Document(stream=r.content)

    print("Extracting PDF")

    content = ""
    for page in doc:
        text = page.get_textpage().extractTEXT()
        content += text + "\n\n"

    print("Asking model")

    messages = [
        {
            "role": "user",
            "content" : f"""
            You are a AI model that helps make understanding Congressional bills easier for the average person.
            The next message is the document that the user needs help understand.
            All messages after the next message are from the user.
            """
        }
    ]

    if input != "":
        additional_context = ""
        prior_messages = CONNECTIONS[id]['messages']

        for message in prior_messages:
            additional_context += f"""

            Question: {message[0]}
            Answer: {message[1]}
            
            """

        messages.append({
            "role": "user",
            "content": f"""
            You, the model, have already said the following:
            {additional_context}

            ---
            Now respond to this question:

            {input}
            """
        })
    else:
        messages.append({
            "role": "user",
            "content": f"""
            Summarize this bill:
            
            {content}
            """
        })

    response_index = len(CONNECTIONS[id]['messages'])
    CONNECTIONS[id]["messages"].append([input, ""])
    
    client = AsyncClient()
    response = await client.chat(
        model="gemma3:270m",
        messages=messages,
        stream=True
    )
#    response = openai.chat.completions.create(
#        model="gpt-3.5-turbo",  # Or your desired model, e.g., "gpt-4"
#        messages=[
#            {"role": "system", "content": "You are a helpful assistant."},
#            {"role": "user", "content": "What is the capital of France?"},
#        ]
#    )

#    # Access the response content
#    print(response.choices[0].message.content)




    async for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
        CONNECTIONS[id]["messages"][response_index][1] += chunk["message"]["content"]
        await send(Script(
            chunk["message"]["content"],
            id="response",
            type="text/markdown",
            hx_swap_oob="beforeend"))








def main_list(laws:Optional[int], custom_bills:Optional[Any]=None):

    bills: list[Any] = custom_bills or get_bills(laws)
    print(bills)

    bill_elements = []
    for bill in bills:
        title = bill["title"]
        origin_chamber = bill["originChamber"]
        date = bill["updateDateIncludingText"]
        congress = bill["congress"]
        number = bill["number"]
        _type = bill["type"]

        bill_elements.append(Div(
            Hgroup( 
                B(A(title, href=f"/bill/{congress}/{number}/{_type}")),
                P(date),
            ),
            P(f"Chamber of Origin: {origin_chamber}")
        ))

    law_select = None
    if laws:
        law_select = Form(
            Input( type = "number", name="congress", value=str(laws)),
            method="get",
            action = "/laws"
        ),

        

    return (
        Title("BillAI"),
        Main(
            Div(
                H1("BillAI"),
                P("Learn more about bills"),
                
                Form(
                    Div(
                        Select(
                            Option("House of Representatives", value = "HR"),
                            Option("Senate", value = "SRES"),
                            name = "chamber",
                            cls ="searchinput"
                        ),
                        Input(type= "number", name='congress', id='congress', placeholder = "congress",required = True,cls ="searchinput"),
                        Input(type= "number", name='number', id='number', placeholder = "number",cls ="searchinput"),
                        Input(type='submit', value='search',cls ="searchinput"),
                        cls  = "horizontal"
                    ),
                    method="post",
                    action="/search",
                    
                ),
                Hr(),
                Div(
                    A("Bills",href ="/"), 
                    A("Laws",href ="/laws"),
                    law_select,
                    cls = "horizontal" 
                ),
                Br(),
                *bill_elements
            ),
            cls="container"
        )
    )

@app.get("/")
def read_root():
    return main_list(laws=None)
@app.get("/laws/")
def read_laws(congress:str = ""):
    print(f"laws: ({congress})")
    try:
        laws = int(congress)
    except:
        laws = 119
    return main_list(laws=laws)
@dataclass
class SearchQ:
    chamber: str
    congress: int
    number: Optional[int]


@app.post("/search")
async def searchfor_bill(data: SearchQ):
    print(f"data:{data}")
    if data.number:
        return bill_handler(data.congress,data.number,data.chamber)
    else:
        return main_list(laws=None, custom_bills=get_congressional_bills(data.congress,data.chamber) )
@app.get("/public/{fname}.{ext}")
async def public_get(fname: str, ext: str):
    return FileResponse(f"public/{fname}.{ext}")

# Type annotations are a must
@app.get("/bill/{congress}/{number}/{_type}")
def bill_handler(congress: int, number: int, _type: str):
    bill = find_bill(congress,number,_type)

    if bill == None:
        return H1("You do one we donthave/ dont exist")
    
    print(bill)
    our_pdf = get_pdf(congress, _type.lower(), number)
    # our_response = get_response(our_pdf, "explain it")

    id = uuid.uuid4()

    return (
        Title(bill["title"]),
        Main(
            Div(
                H1(bill["title"]),
                Div(
                    Iframe(src=f"/bill/pdf/{congress}/{number}/{_type}", width="100%", height = '100%'),
                    Div(
                        Zero_md(
                            Template(),
                            Script(type="text/markdown", id="response")
                        ),
                        # Textarea(id="response"),
                        Script("""
                            function remove_model_analysis() {
                               
                               let el = document.getElementById("model_analysis_btn");
                               el.outerHTML = "";
                            }
                        """),
                        Form(
                            Input(
                                id="msg",
                                hidden=True,
                                value=json.dumps({
                                    "phase": 0,
                                    "congress": congress,
                                    "number": number,
                                    "type": _type,
                                    "uuid": str(id)
                                }),
                                hx_trigger="load"
                            ),
                            Input(type="submit", value="Get analysis"),\
                            onsubmit="setTimeout(remove_model_analysis, 1000)",
                            id="model_analysis_btn",
                            ws_send=True
                        ),
                        Form(
                            Script("""
                            function prepare_ask_model() {
                                let el = document.querySelector("#ask_model_form > #msg");
                                let payload_el = document.querySelector("#ask_model_in");
                                let data = JSON.parse(el.value);
                                data.payload = payload_el.value;
                                el.value = JSON.stringify(data);
                            }
                            """),
                            Input(id="ask_model_in", placeholder="Ask the model something..."),
                            Input(
                                id="msg",
                                hidden=True,
                                value=json.dumps({
                                    "phase": 1,
                                    "congress": congress,
                                    "number": number,
                                    "type": _type,
                                    "payload": "",
                                    "uuid": str(id)
                                }),
                            ),
                            Input(type="submit", value="Ask"),
                            onsubmit="prepare_ask_model()",
                            id="ask_model_form",
                            ws_send=True
                        )
                    ),
                    style="min-height: 83vh",
                    id="content-container",
                    cls="grid",
                    hx_ext="ws",
                    ws_connect=f"/model/bill"
                )
            ),
            cls="container"
        )
    )

@app.ws("/model/bill")
async def model_bill_handler(msg: str, send):
    data = json.loads(msg)
    print(data)
    phase = data["phase"]
    congress = data["congress"]
    number = data["number"]
    _type = data["type"]
    id = data["uuid"]
    
    if CONNECTIONS.get(id, None) is None:
        # CONNECTIONS["key"] = value
        CONNECTIONS[id] = {
            "last_time": time.time(),
            "messages" : []
        }

    if phase == 0:
        bill = find_bill(congress, number, _type)

        if bill == None:
            return H1("You do one we donthave/ dont exist")
        
        our_pdf = get_pdf(congress, _type.lower(), number)

        asyncio.create_task(get_response_stream(our_pdf, "", id, send))
        response = Script(type="text/markdown", id="response")
    else:
        payload = data["payload"]
        
        bill = find_bill(congress, number, _type)

        if bill == None:
            return H1("You do one we donthave/ dont exist")
        
        our_pdf = get_pdf(congress, _type.lower(), number)

        asyncio.create_task(get_response_stream(our_pdf, payload, id, send))

        response = Script(
            "\n\n---\n\n",
            id="response",
            type = "text/markdown",
            hx_swap_oob="beforeend"
        )

    await send(response)



@app.get("/bill/pdf/{congress}/{number}/{_type}")
async def bill_handler_pdf(congress: int, number: int, _type: str):
    bill = find_bill(congress, number, _type)

    if bill == None:
        return H1("You do one we donthave/ dont exist")
    
    our_pdf = get_pdf(congress, _type.lower(), number)
    pdf = requests.get(our_pdf, stream=True)

    async def pdf_response(pdf):
        for chunk in pdf.iter_content(chunk_size=2048):
            yield chunk

    return StreamingResponse(pdf_response(pdf), media_type="application/pdf")


serve()

# @app.get("/bills")
#
# @app.get("/pdf")
#
# @app.get("/response")
#
#
# # print(len(bills))
# # numbrdex = int(input("What bill would you like? "))
# # while numbrdex > 20 or numbrdex < 0:
# #   numbrdex = int(input("What bill would you like? "))
#
# # bill = bills[numbrdex - 1]
# # bill_number = bill['number']def get_response(url
# # bill_type = bill["type"].lower()
# # bill_congress = bill['congress']
# # billsthatwork = []
#
# # Perform the GET request to the specfic bill to get its text
#
