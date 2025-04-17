from backend.settings import settings

import uvicorn


def main():
    uvicorn.run(
        "backend.web.application:get_app",
        workers=settings.workers_count,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.value.lower(),
        reload_dirs=["backend"],
        factory=True,
    )


if __name__ == "__main__":
    main()
