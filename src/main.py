from fastapi import FastAPI, Request
import time
import logging
from pythonjsonlogger import jsonlogger
from src.core.config import config
from src.core.database import init_db
from src.routers import auth, chat, upload, conversations

# Initialize DB
init_db()

# Configure Logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI(title="AI Chat Bot")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
        }
    )
    return response

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(conversations.router)

@app.get("/")
async def root():
    return {"message": "AI Chat Bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT)
