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
from langchain.prompts import MessagesPlaceholder
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.agents import initialize_agent, AgentExecutor
from langchain.agents import AgentType
from src.prompt import sys_msg
import logging
import pickle
from src.exception import log_e
import src.components.precipitation as precipitaion
import src.components.evapotranspiration as evapotranspiration

topics_list = [
    precipitaion.topic,
    evapotranspiration.topic,
]

tools_list = [
    precipitaion.PrecipitationSingleHydrologicalYearSingleVillage(),
    evapotranspiration.EvapotranspirationSingleHydrologicalYearSingleVillage(),
]

logger = logging.getLogger(__name__)


class ConversationHandler:
    def __init__(self, history) -> None:
        self.llm = self.create_llm()
        self.chat_history = MessagesPlaceholder(variable_name="chat_history")
        self.memory = self.read_memory(history) if history else self.create_memory()
        self.tools = tools_list
        self.sys_msg = sys_msg.format("\n".join(topics_list))
        self.agent = self.create_agent()
        if not history:
            self.create_prompt()

    def create_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            openai_api_key=os.getenv("GPT_TOKEN"),
            temperature=0,
            model_name=os.getenv("LLM_MODEL"),
        )

    def create_memory(self) -> ConversationSummaryBufferMemory:
        return ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=300,
            memory_key="chat_history",
            return_messages=True,
        )

    def create_agent(self) -> AgentExecutor:
        return initialize_agent(
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            tools=self.tools,
            llm=self.llm,
            verbose=False,
            max_iterations=3,
            early_stopping_method="force",  # 'generate',
            handle_parsing_errors=True,
            memory=self.memory,
            agent_kwargs={
                "memory_prompts": [self.chat_history],
                "input_variables": ["input", "agent_scratchpad", "chat_history"],
            },
        )

    def create_prompt(self) -> None:
        try:
            prompt = self.agent.agent.create_prompt(
                tools=self.tools, prefix=self.sys_msg
            )
            self.agent.agent.llm_chain.prompt = prompt
        except Exception as e:
            logger.exception(log_e(e))

    def read_memory(self, serialized_memory):
        encoded = serialized_memory.encode('utf-8').replace(b'\xc2',b'')
        buffer = pickle.loads(encoded)
        memory = self.create_memory()
        memory.chat_memory.messages = buffer
        return memory

    @property
    def serialized_memory(self):
        pkld = pickle.dumps(self.memory.chat_memory.messages)
        return pkld.decode('unicode_escape')

    def query(self, input: str) -> str:
        response = self.agent.run(input)
        logger.debug(f"response from agent: {response}")
        return response
