# jaltolAI

jaltolAI is a prototype project on GPT implementation of
[Jaltol](https://welllabs.org/jaltol/), open source water security tool,
by [WELL Labs](https://welllabs.org/) providing a REST API.

<img width="958" alt="JaltolAI" src="https://github.com/balakumaran247/jaltolAI/assets/77524312/d100e34c-38ce-4487-82e4-a1290fa4fb6e">


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

![Swagger UI](https://github.com/balakumaran247/jaltolAI/assets/77524312/327fbb16-10d1-4a3b-b800-6d2bcf5860fe)


# Packages

-   FastAPI
-   Google Earth Engine
-   OpenAI
-   LangChain
-   geopy
