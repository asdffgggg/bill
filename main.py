import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from fasthtml.common import *
from ollama import chat
from ollama import ChatResponse

load_dotenv()

app, rt = fast_app()


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

def get_response(url, input):
    response = chat(
        model="gemma3:270m",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_url": url,
                    },
                    {
                        "type": "input_text",
                        "text": input,
                    },
                ],
            },
        ]
    )

    print(response.message.content)

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
            Form(
                Input(name="key"),
                method="POST",
                action="/key"
            ),
            Div(
                H1("But not you"),
                P("Learn more about bills"),
                Hr(),
                *bill_elements
            ),
            cls="container"
        )
    )

@app.post("/key")
def key(key: str):
    print(key)
    return "ok"

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
    our_response = get_response(our_pdf, "explain it")


    return (
        Title(bill["title"]),
        Main(
            Div(
                H1(bill["title"]),
                P(our_response)
            ),
            cls="container"
        )
    )

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
# # bill_number = bill['number']
# # bill_type = bill["type"].lower()
# # bill_congress = bill['congress']
# # billsthatwork = []
#
# # Perform the GET request to the specfic bill to get its text
#
