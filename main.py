from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.gpt import gpt_query
from src.utils import JaltolInput

app = FastAPI(title="JaltolAI", version="0.0.1")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request":request})

@app.post("/jaltol/")
async def jaltol(input: JaltolInput):
    input_dict = input.dict()
    return gpt_query(input_dict['user'])