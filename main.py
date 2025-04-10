from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from chainlit.utils import mount_chainlit

app = FastAPI()


@app.get("/docs")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

mount_chainlit(app=app, target="./src/app/chainlitUI.py", path="/chainlit")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)