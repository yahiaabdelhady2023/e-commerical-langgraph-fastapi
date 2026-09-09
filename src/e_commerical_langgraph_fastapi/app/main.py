from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"welcome_message":"hello carrot"}


@app.get("/test")
def read_root():
    return {"welcome_message":"test"}