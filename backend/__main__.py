from backend.settings import settings

from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


def main():
    uvicorn.run(
        "backend.__main__:app",
        workers=settings.workers_count,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.value.lower(),
        # factory=True,
    )


if __name__ == "__main__":
    main()
