import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from fasthtml.common import *
from ollama import chat
from ollama import ChatResponse
import pymupdf
from starlette.responses import StreamingResponse

load_dotenv()

app, rt = fast_app(
    static_path="public",
    hdrs=(
        MarkdownJS(),
        Link(rel="stylesheet", href="/index.css")
    )
)


def get_bills():
    head = "https://api.congress.gov/"
    endpoint = "v3/bill"
    apikey = os.getenv("CONGRESSAPIKEY")

    params = {
        "format": "json",
        "api_key": apikey
    }
    # Perform the GET request to the general bill endpoint
    response = requests.get(head + endpoint, params=params)
    bills = response.json()['bills']
    return bills

def get_pdf(bill_congress,bill_type,bill_number):
    head = "https://api.congress.gov/"
    apikey = os.getenv("CONGRESSAPIKEY")
    params = {
        "format": "json",
        "api_key": apikey
    }
    bill_congress = int(bill_congress)
    textpoint = f"v3/bill/{bill_congress}/{bill_type}/{bill_number}/text"
    reponse = requests.get(head + textpoint, params=params)
    print(reponse.json())
    while len(reponse.json()['textVersions']) == 0:
        bill_congress -= 1
        textpoint = f"v3/bill/{bill_congress}/{bill_type}/{bill_number}/text"
        reponse = requests.get(head + textpoint, params=params)
    pdf = reponse.json()['textVersions'][0]['formats'][1]['url']
    return pdf

def get_response_stream(url, input):
    r = requests.get(url)
    doc = pymupdf.Document(stream=r.content)

    print("Extracting PDF")

    content = ""
    for page in doc:
        text = page.get_textpage().extractTEXT()
        content += text + "\n\n"

    print(content)

    print("Asking model")

    response = chat(
        model="gemma3:270m",
        messages=[
            {
                "role": "user",
                "content": "Why is the sky blue?"
                # "content" : f"""
                # You are a AI model that helps make understanding Congressional bills easier for the average person.
                # The next message is the document that the user needs help understand.
                # Respond to the next message with your explanation of the bill and its main summarized points without having too little information.
                # TELL ME ABOUT THE GODDAMN BILL DIRTY CLANKER
                # """
            }
            # {
            #     "role": "user",
            #     "content": content
            # }
        ],
        stream=True
    )

    for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
        yield chunk["message"]["content"]

    
@app.get("/")
def read_root():
    bills = get_bills()
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

    return (
        Title("But not you"),
        Main(
            Div(
                H1("But not you"),
                P("Learn more about bills"),
                Hr(),
                *bill_elements
            ),
            cls="container"
        )
    )

@app.get("/public/{fname}.{ext}")
async def public_get(fname: str, ext: str):
    return FileResponse(f"public/{fname}.{ext}")

# Type annotations are a must
@app.get("/bill/{congress}/{number}/{_type}")
def bill_handler(congress: int, number: int, _type: str):
    b1lls = get_bills()
    bill = None
    for b in b1lls:
        if b["congress"] == congress and b["number"] == str(number) and b["type"] == _type:
            bill = b
            break

    if bill == None:
        return H1("You do one we donthave/ dont exist")
    
    print(bill)
    our_pdf = get_pdf(congress, _type.lower(), number)
    # our_response = get_response(our_pdf, "explain it")


    return (
        Title(bill["title"]),
        Main(
            Div(
                H1(bill["title"]),
                Div(
                    Iframe(src=f"/bill/pdf/{congress}/{number}/{_type}", width="100%"),
                    Div(
                        P("Loading model analysis"),
                        hx_get=f"/model/bill/{congress}/{number}/{_type}",
                        hx_trigger="load"
                    ),
                    id="content-container",
                    cls="grid"
                )
            ),
            cls="container"
        )
    )

@app.get("/model/bill/{congress}/{number}/{_type}")
def model_bill_handler(congress: int, number: int, _type: str):
    b1lls = get_bills()
    bill = None
    for b in b1lls:
        if b["congress"] == congress and b["number"] == str(number) and b["type"] == _type:
            bill = b
            break

    if bill == None:
        return H1("You do one we donthave/ dont exist")
    
    our_pdf = get_pdf(congress, _type.lower(), number)

    return StreamingResponse(get_response_stream(our_pdf, "explain it"), media_type="text")



@app.get("/bill/pdf/{congress}/{number}/{_type}")
async def bill_handler_pdf(congress: int, number: int, _type: str):
    b1lls = get_bills()
    bill = None
    for b in b1lls:
        if b["congress"] == congress and b["number"] == str(number) and b["type"] == _type:
            bill = b
            break

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
