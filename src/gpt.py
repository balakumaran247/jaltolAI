import logging
import os
import pickle
from typing import Optional

from dotenv import find_dotenv, load_dotenv
from langchain.agents import AgentExecutor, AgentType, initialize_agent
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import messages_from_dict, messages_to_dict

import src.components.evapotranspiration as evapotranspiration
import src.components.precipitation as precipitaion
from src.exception import log_e
from src.prompt import sys_msg

_ = load_dotenv(find_dotenv())

topics_list = [
    precipitaion.topic,
    evapotranspiration.topic,
]

tools_list = [
    precipitaion.PrecipitationSingleHydrologicalYearSingleVillage(),
    evapotranspiration.EvapotranspirationSingleHydrologicalYearSingleVillage(),
]

logger = logging.getLogger(__name__)


class AgentHandler:
    def __init__(self, history: Optional[str]) -> None:
        """
        Initializes an AgentHandler object.

        Args:
            history (Optional[str]): Serialized memory containing chat history.

        """
        self.llm = self.create_llm()
        self.chat_history = MessagesPlaceholder(variable_name="chat_history")
        self.memory = self.read_memory(history) if history else self.create_memory()
        self.tools = tools_list
        self.sys_msg = sys_msg.format("\n".join(topics_list))
        self.agent = self.create_agent()
        if not history:
            self.create_prompt()

    def create_llm(self) -> ChatOpenAI:
        """
        Creates and returns a ChatOpenAI instance for language modeling.

        Returns:
            ChatOpenAI: The ChatOpenAI instance.

        """
        return ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
            model_name=os.getenv("LLM_MODEL"),
        )

    def create_memory(self) -> ConversationSummaryBufferMemory:
        """
        Creates and returns a ConversationSummaryBufferMemory instance.

        Returns:
            ConversationSummaryBufferMemory: The ConversationSummaryBufferMemory instance.

        """
        return ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=300,
            memory_key="chat_history",
            return_messages=True,
        )

    def create_agent(self) -> AgentExecutor:
        """
        Creates and returns an AgentExecutor instance.

        Returns:
            AgentExecutor: The AgentExecutor instance.

        """
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
        """
        Creates a prompt for the agent and sets it in the agent's llm_chain.

        """
        try:
            prompt = self.agent.agent.create_prompt(
                tools=self.tools, prefix=self.sys_msg
            )
            self.agent.agent.llm_chain.prompt = prompt
        except Exception:
            logger.exception(log_e())

    def read_memory(self, serialized_memory: str) -> ConversationSummaryBufferMemory:
        """
        Deserializes the memory and creates a ConversationSummaryBufferMemory instance.

        Args:
            serialized_memory (str): Serialized memory containing chat history.

        Returns:
            ConversationSummaryBufferMemory: The ConversationSummaryBufferMemory instance.

        """
        try:
            messages = pickle.loads(serialized_memory.encode("latin-1"))
            retrieved_messages = messages_from_dict(messages)
            retrieved_chat_history = ChatMessageHistory(messages=retrieved_messages)
            return ConversationSummaryBufferMemory(
                chat_memory=retrieved_chat_history,
                llm=self.llm,
                max_token_limit=300,
                memory_key="chat_history",
                return_messages=True,
            )
        except Exception:
            logger.exception(log_e())
            return ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=300,
                memory_key="chat_history",
                return_messages=True,
            )

    @property
    def serialized_memory(self) -> Optional[str]:
        """
        Serializes the memory.

        Returns:
            str: Serialized memory.

        """
        try:
            return pickle.dumps(
                messages_to_dict(self.memory.chat_memory.messages)
            ).decode("latin-1")
        except Exception:
            logger.exception(log_e())
            return None

    def query(self, input: str) -> str:
        """
        Executes a query using the agent.

        Args:
            input (str): The user's input/query.

        Returns:
            str: The agent's response.

        """
        try:
            return self.agent.run(input)
        except Exception:
            logger.exception(log_e())
            return "Something went wrong, contact JaltolAI team."
