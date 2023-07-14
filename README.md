# jaltolAI

jaltolAI is a prototype project on GPT implementation of
[Jaltol](https://welllabs.org/jaltol/), open source water security tool,
by [WELL Labs](https://welllabs.org/) providing a REST API.

# Features

-   Precipitation for single location in a year
-   Evapotranspiration for single location in a year

# Installation

1. create a virtual environment for python 3.9
2. activate the virtual environment
3. `pip install -r requirements.txt`
4. create .env file based on .env.example

# Usage

To start the application run the command

```
uvicorn main:app
```

navigate to `127.0.0.1:8000` for Chat UI or `127.0.0.1:8000/docs` for Swagger UI.

# Packages

-   FastAPI
-   Google Earth Engine
-   OpenAI
-   LangChain
-   geopy
