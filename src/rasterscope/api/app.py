from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rasterscope.api.routes import router
from rasterscope.settings import get_config


def create_app(serve_frontend: bool = True) -> FastAPI:
    config = get_config()
    application = FastAPI(
        title="RasterScope API",
        summary="Local satellite land-cover segmentation and change analysis",
        version="0.1.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    application.include_router(router)
    application.mount(
        "/scenarios",
        StaticFiles(directory=config.paths.scenario_dir),
        name="scenarios",
    )
    if serve_frontend and config.paths.frontend_dist.exists():
        application.frontend("/", directory=config.paths.frontend_dist)
    return application


app = create_app()
