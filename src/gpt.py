import openai
import os

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key  = os.getenv('GPT_TOKEN')

def get_completion(prompt, model="gpt-3.5-turbo", temperature=0):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message["content"]

def gpt_query(input: str):
    prompt = f"""
    Identify the following details from the input text delimited by \
    triple backticks and return the extracted details in JSON format as below:
    location: <the name of the location, including village, District, State>
    year: <year as integer>
    
    input text: ```{input}```
    """
    import json
    input_json = json.loads(get_completion(prompt))
    from src.utils import LocationDetails
    from src.components.precipitation import Precipitation
    ll = LocationDetails(input_json['location'])
    ee_location = ll.ee_obj()
    rain = Precipitation(ee_location, input_json['year'])
    return f"The Precipitation over {input_json['location']} for the hydrological \
year {input_json['year']} is {rain.handler()} mm."