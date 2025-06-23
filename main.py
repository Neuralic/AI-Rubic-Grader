# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Assignment Reviewer")

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Assignment Reviewer up and running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)