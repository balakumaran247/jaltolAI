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
from langchain.agents import AgentType
from src.utils import tools_list
from src.prompt import sys_msg, text_msg, data_msg, map_msg, chart_msg
from typing import List, Any, Dict
import logging
from src.exception import log_e

logger = logging.getLogger(__name__)

class ConversationHandler:
    def __init__(self, history) -> None:
        self.llm = self.create_llm()
        self.history = history if history else self.create_memory()
        self.tools = tools_list
        self.sys_msg = sys_msg
        self.agent = self.create_agent()
        self.output_parser = self.create_output_parser()
        if not history:
            self.create_prompt()

    def create_llm(self) -> ChatOpenAI:
        try:
            return ChatOpenAI(
                openai_api_key=os.getenv("GPT_TOKEN"),
                temperature=0,
                model_name="gpt-3.5-turbo",
            )
        except Exception as e:
            logger.exception(log_e(e))

    def create_memory(self) -> ConversationSummaryBufferMemory:
        try:
            return ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=300,
                memory_key='chat_history',
                input_key='input',
                human_prefix='Human',
                ai_prefix='AI',
                return_messages=True)
        except Exception as e:
            logger.exception(log_e(e))

    def create_agent(self) -> AgentExecutor:
        try:
            return initialize_agent(
                    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                    tools=self.tools,
                    llm=self.llm,
                    verbose=False,
                    max_iterations=3,
                    early_stopping_method="force",  # 'generate',
                    handle_parsing_errors=True,
                    memory=self.history,
                )
        except Exception as e:
            logger.exception(log_e(e))

    @classmethod
    def create_output_parser(cls) -> StructuredOutputParser:
        try:
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
        except Exception as e:
            logger.exception(log_e(e))
    
    def create_prompt(self) -> None:
        try:
            format_instructions = self.output_parser.get_format_instructions()
            logger.debug(f'parser_format_instructions: {format_instructions}')
            prompt = self.agent.agent.create_prompt(system_message = sys_msg, tools = self.tools)
            logger.debug(f'system_prompt: {prompt}')
            # messages = prompt.format_prompt(output_format = format_instructions, chat_history=[])
            messages = prompt
            logger.debug(f'agent_prompt: {messages}')
            self.agent.agent.llm_chain.prompt = messages
        except Exception as e:
            logger.exception(log_e(e))

    def query(self, input: str) -> Dict[str, str]:
        try:
            response = self.agent.run(input)
            logger.debug(f'response from agent: {response}')
            # return self.output_parser.parse(response)#.content)
            return response
        except Exception as e:
            logger.exception(log_e(e))
