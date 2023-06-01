from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.gpt import gpt_query
from src.utils import JaltolInput

__version__ = "0.0.1"

app = FastAPI(title="JaltolAI", version=__version__)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/jaltol/")
async def jaltol(input: JaltolInput):
    input_dict = input.dict()
    return gpt_query(input_dict["user"])
