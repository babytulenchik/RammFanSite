from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from database import init_db
from shop.routes import router as shop_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Application shutting down")

app = FastAPI(title="Rammstein Fan Site", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(shop_router)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/bandmates", response_class=HTMLResponse)
async def bandmates_page(request: Request):
    return templates.TemplateResponse("bandmates.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/merchandise")
async def merchandise_redirect():
    return RedirectResponse(url="/shop/merchandise")

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request})

@app.get("/cart")
async def cart_redirect():
    return RedirectResponse(url="/shop/cart")

@app.get("/checkout")
async def checkout_redirect():
    return RedirectResponse(url="/shop/checkout")

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request})

@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)