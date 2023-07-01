import logging
import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.gpt import AgentHandler
from src.utils import JaltolInput, JaltolOutput

__version__ = "0.0.2"

_ = load_dotenv(find_dotenv())

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaltolAI", version=__version__)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_KEY"), max_age=7200)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root route that serves the index.html template.

    Args:
        request (Request): The request object.

    Returns:
        HTMLResponse: The rendered index.html template.

    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/jaltol/", response_model=JaltolOutput)
async def jaltol(request: Request, input: JaltolInput):
    """
    Endpoint for handling JaltolAI requests.

    Args:
        request (Request): The request object.
        input (JaltolInput): The input data containing the user message.

    Returns:
        JaltolOutput: The output data containing the response text.

    """
    history = request.session.get("history", None)
    logger.debug(f"history={bool(history)}")
    input_dict = input.dict()
    input_text = input_dict["user"]
    logger.info(f"user input={input_text}")
    conversation = AgentHandler(history)
    response = conversation.query(input_text)
    logger.debug(f"response from agent={response}")
    request.session["history"] = conversation.serialized_memory
    return {"text": response}
