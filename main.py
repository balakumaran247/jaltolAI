from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from src.gpt import gpt_query
from src.utils import JaltolInput, JaltolOutput
from dotenv import load_dotenv, find_dotenv
import os

__version__ = "0.0.2"

_ = load_dotenv(find_dotenv())
app = FastAPI(title="JaltolAI", version=__version__)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_KEY"), max_age=7200)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/jaltol/", response_model=JaltolOutput)
async def jaltol(input: JaltolInput):
    input_dict = input.dict()
    return {"text": gpt_query(input_dict["user"])}
