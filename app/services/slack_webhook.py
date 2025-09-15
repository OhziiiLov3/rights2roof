# slack/fastpi lives 
# starter code to test locally

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Rights2Roof API"}