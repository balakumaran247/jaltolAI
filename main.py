import logging
import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

__version__ = "0.0.2"

_ = load_dotenv(find_dotenv())

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaltolAI", version=__version__)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_KEY"), max_age=7200)

credential_dir_path = os.path.join(os.path.expanduser("~"), ".config", "earthengine")
credential_file_path = os.path.join(credential_dir_path, "credentials")
if os.path.isfile(credential_file_path):
    logger.info("EE credential file is available!")
else:
    logger.info("EE credential file not found!")
    ee_token = os.getenv("EE_TOKEN")
    credential = '{"refresh_token":"%s"}' % ee_token
    os.makedirs(credential_dir_path, exist_ok=True)
    with open(credential_file_path, "w") as file:
        file.write(credential)
    logger.info("EE credential file created.")

from src.gpt import AgentHandler
from src.utils import JaltolInput, JaltolOutput


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
