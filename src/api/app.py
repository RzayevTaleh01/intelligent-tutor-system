from fastapi import FastAPI
from src.api.v1_main import app as v1_app
from src.api.v2_main import app as v2_app

app = FastAPI(title="EduVision API Gateway")

app.mount("/v1", v1_app)
app.mount("/v2", v2_app)

@app.get("/")
async def root():
    return {"message": "EduVision API Gateway. Use /v1 for dev or /v2 for prod."}
