import openai
import os
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai.api_key = os.getenv("GPT_TOKEN")


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

    ll = LocationDetails(input_json["location"])
    ee_location = ll.ee_obj()
    rain = Precipitation(ee_location, input_json["year"])
    return f"The Precipitation over {input_json['location']} for the hydrological \
year {input_json['year']} is {rain.handler()} mm."


from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.agents import initialize_agent, AgentExecutor
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from src.utils import tools_list
from src.prompt import sys_msg, text_msg, data_msg, map_msg, chart_msg
from typing import List, Any


class ConversationHandler:
    def __init__(self, history) -> None:
        self.llm = self.create_llm()
        self.history = history or self.create_memory()
        self.tools = tools_list
        self.sys_msg = sys_msg
        self.agent = self.create_agent()
        self.output_parser = self.create_output_parser()
        if not self.history:
            self.create_prompt()

    def create_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            openai_api_key=os.getenv("GPT_TOKEN"),
            temperature=0,
            model_name="gpt-3.5-turbo",
        )

    def create_memory(self) -> ConversationSummaryBufferMemory:
        return ConversationSummaryBufferMemory(llm=self.llm, max_token_limit=300)

    def create_agent(self) -> AgentExecutor:
        return initialize_agent(
            agent="chat-conversational-react-description",
            tools=self.tools,
            llm=self.llm,
            verbose=False,
            max_iterations=3,
            early_stopping_method="force",  # 'generate',
            handle_parsing_errors=True,
            memory=self.history,
        )

    @classmethod
    def create_output_parser(cls) -> StructuredOutputParser:
        text_schema = ResponseSchema(
            name="text",
            description=text_msg)
        data_schema = ResponseSchema(
            name="data",
            description=data_msg)
        map_schema = ResponseSchema(
            name="map",
            description=map_msg)
        chart_schema = ResponseSchema(
            name="chart",
            description=chart_msg)

        response_schemas = [text_schema, 
                            data_schema,
                            map_schema,
                            chart_schema]
        
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def create_prompt(self) -> None:
        format_instructions = self.output_parser.get_format_instructions()
        prompt = self.agent.agent.create_prompt(system_message = sys_msg, tools = self.tools)
        messages = prompt.format_prompt(output_format = format_instructions)
        self.agent.agent.llm_chain.prompt = messages

    def query(self, input: str):
        response = self.agent(input)
        return self.output_parser.parse(response)#.content)
