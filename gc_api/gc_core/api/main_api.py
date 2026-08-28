"""Main API program"""

### external imports
import datetime
import logging
from fastapi import (
    Body,
    Cookie,
    FastAPI,
    UploadFile,
    File,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
    BackgroundTasks,
)


from fastapi.middleware.cors import CORSMiddleware
from random import randint
import sys
from typing import Any, List

### internal imports
from gc_core.shared.stream import AnalysisResponse, StreamManager
from gc_core.shared import dbase, config
from gc_core.api.web_socket import SocketMessage, WebSocketManager, Duration

### limit error output
sys.tracebacklimit = 0

### config logger
logging.basicConfig(level=logging.DEBUG)
log_format = logging.Formatter("%(levelname)s - %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_format)
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(log_format)

lg = logging.getLogger("app_logger")
lg.addHandler(file_handler)
lg.addHandler(stream_handler)
lg.propagate = False
logging.getLogger("python_multipart.multipart").disabled = True

### fastapi setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

### init db, analyser
db = dbase.DBase("database")
analyser = StreamManager()

### websocket manager
websocket_manager = WebSocketManager()


### Routes
@app.get("/")
async def root():
    return {"message": "Hello World"}


### home page routes
@app.post("/generate-api-key")
async def generate_api_key(response: Response):
    new_api_key = dbase.get_key(30)
    db.add_api_key(new_api_key)
    response.set_cookie(
        key="api_key",
        value=new_api_key,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=604800,
    )
    return {"api_key": new_api_key}


@app.get("/verify-saved-api-key")
async def verify_saved_api_key(api_key: str | None = Cookie(None)) -> dict[str, str]:
    if api_key is None:
        return {"status": "invalid", "api_key": ""}

    if db.get_uid(api_key):
        return {"status": "valid", "api_key": api_key}
    return {"status": "invalid", "api_key": ""}


@app.post("/verify-new-api-key")
async def verify_new_api_key(data: dbase.Key, response: Response):
    if db.get_uid(data.key):
        response.set_cookie(
            key="api_key",
            value=data.key,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=604800,
        )
        return {"message": "valid", "api_key": data.key}
    else:
        return {"message": "invalid", "api_key": ""}


### files routes
@app.get("/files", response_model=List[dbase.FileItem] | None)
async def get_files(api_key: str | None = Cookie(None)):
    if api_key is None:
        return
        # return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.get_file_items(api_key)


@app.delete("/files/{file_id}")
async def delete_item(file_id: str, api_key: str | None = Cookie(None)):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if file_id == "all":
        db.delete_all_files(api_key)
        return Response(status_code=status.HTTP_202_ACCEPTED)

    # convert id to int
    try:
        file_id_i = int(file_id)
    except Exception:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    db.delete_file(api_key, file_id_i)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@app.post("/upload")
async def upload(
    api_key: str | None = Cookie(None),
    files: List[UploadFile] = File(...),
):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    db.add_files(api_key, files)
    await websocket_manager.send_message(
        api_key,
        SocketMessage(
            title="File Upload Successful",
            info=f"Uploaded {len(files)} file(s)",
            time=f"{datetime.datetime.now().strftime('%H:%M:%S')}",
            id=randint(0, 10000000),
            duration=Duration.SHORT,
        ),
    )
    return Response(status_code=status.HTTP_202_ACCEPTED)


### config routes
@app.post("/set-config")
async def set_config(
    config: dict[Any, Any] = Body(...), api_key: str | None = Cookie(None)
):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    db.set_config(api_key, config)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/get-config")
async def get_config(api_key: str | None = Cookie(None)):
    if api_key is None:
        return None

    config_values = db.get_config(api_key)

    if config_values is None:
        return None
    return config.get_frontend_config(config_values).model_dump()


### results
@app.get("/analysis-status", response_model=None)
async def analysis_status(
    api_key: str | None = Cookie(None),
) -> AnalysisResponse | Response | None:
    if api_key is None:
        return None

    c_status = db.get_analysis_status(api_key)
    c_progress = analyser.get_progress(api_key)

    if c_status is None:
        return AnalysisResponse(status=dbase.AnalysisStatus.NONE, progress=0)

    return AnalysisResponse(status=dbase.AnalysisStatus(c_status), progress=c_progress)


@app.get("/result-selector")
async def result_selector(api_key: str | None = Cookie(None)):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    selector = db.get_selectors(api_key)

    return {
        "dates": selector.dates,
        "identifiers": selector.identifiers,
        "models": selector.models,
    }


@app.post("/result-data")
async def result_data(select: dbase.ResultSelect, api_key: str | None = Cookie(None)):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    data = db.get_result(api_key, select)

    if data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=data, media_type="application/json")


@app.post("/run-analysis")
async def run_analysis(
    background_tasks: BackgroundTasks, api_key: str | None = Cookie(None)
):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    background_tasks.add_task(analyser.start_analysis, api_key, db, websocket_manager)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@app.post("/get-horizon")
async def get_horizons(select: dbase.ResultSelect, api_key: str | None = Cookie(None)):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    data = db.get_horizon(api_key, select)
    if data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=data, media_type="application/json")


@app.post("/model-scores-hz")
async def get_model_scores_hz(
    select: dbase.ResultSelect, api_key: str | None = Cookie(None)
):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    data = db.get_model_scores_select(api_key, select)
    if data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=data, media_type="application/json")


@app.post("/model-scores")
async def get_model_scores(api_key: str | None = Cookie(None)):
    if api_key is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    data = db.get_model_scores(api_key)
    if data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=data, media_type="application/json")


### websocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, api_key: str | None = Cookie(None)):
    if api_key is None:
        lg.debug("Failed to create websocket: no api key")
        return

    if not db.get_uid(api_key):
        lg.debug("Failed to create websocket: invalid api key")
        return

    # create unique socket key
    socket_key = str(randint(0, 1000000))
    lg.info(f"Websocket connection {api_key}, {socket_key}")

    await websocket.accept()
    websocket_manager.add_websocket(api_key, socket_key, websocket)

    try:
        while True:
            # keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.remove_websocket(api_key, socket_key)
        lg.info(f"Web socket closed: {api_key}, ({socket_key})")
