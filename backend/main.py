from fastapi import FastAPI

app = FastAPI(title="Technical Support Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}
