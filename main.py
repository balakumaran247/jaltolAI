from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.gpt import gpt_query

app = FastAPI(title="JaltolAI", version="0.0.1")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request":request})

@app.post("/query/")
async def query(request: Request):
    item_data = await request.json()
    return gpt_query(item_data['input'])