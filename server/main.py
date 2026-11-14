
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db

from schemas import ReceiptResponse, ReceiptCreate, UserCreate, UserResponse, ReceiptItemCreate

from typing import Annotated

import json
import requests

from image_utils import RECEIPT_PIC_DIR, process_receipt_image

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False)
@app.get("/receipts", include_in_schema=False)
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Receipt))
    receipts = result.scalars().all()
    return templates.TemplateResponse(request, "home.html", {"receipts": receipts, "title": "Home"})

@app.post("/upload")
def upload_receipt(request: Request, db:Annotated[Session, Depends(get_db)], receipt_image: UploadFile = File(...)):
    receiptOcrEndPoint = 'https://ocr.asprise.com/api/v1/receipt'
    content = receipt_image.file.read()
    filename = process_receipt_image(content)
    file_bytes = (RECEIPT_PIC_DIR / filename).read_bytes()
    r = requests.post(receiptOcrEndPoint, data={ \
        'api_key': 'TEST',
        'recognizer': 'auto',
        'ref_no': 'ocr_python_123',
        },
        files={
          "file": (filename, file_bytes, "image/jpeg")
        },
        )
    with open("receipt.json", "w", encoding="utf-8") as file:
        json.dump(r.json(), file, indent=4)

    raw = json.load(open("receipt.json", encoding="utf-8"))
    src = raw["receipts"][0]
    new = {
    "retailer": src.get("merchant_name"),
    "purchase_date": src.get("date"),
    "currency": src.get("currency"),
    "total": src.get("total"),
    }

    new["items"] = [{"description": i.get("description"), "amount": i.get("amount")} for i in src.get("items", [])]

    json.dump(new, open("pantree_receipt.json", "w", encoding="utf-8"), indent=4)

    src = r.json()["receipts"][0]

    data = ReceiptCreate(retailer=src.get("merchant_name"), currency=src.get("currency"), total=src.get("total"), purchase_data=src.get("date"), items=[ReceiptItemCreate(description=i["description"], amount=i["amount"]) for i in src.get("items", [])])
    receipt = save_receipt(db, data)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return RedirectResponse(url="/receipts", status_code=303)

def save_receipt(db: Annotated[Session, Depends(get_db)], data: ReceiptCreate):
    receipt = models.Receipt(**data.model_dump(exclude=["items"]))

    receipt.items = [models.ReceiptItem(**item.model_dump()) for item in data.items]

    return receipt


    

@app.get("/receipts/{receipt_id}", include_in_schema=False)
def receipt_page(request: Request ,receipt_id: int, db: Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Receipt).where(models.Receipt.id == receipt_id))
    receipt = results.scalars().first()
    if receipt:
        title = receipt.title[:50]
        return templates.TemplateResponse(request, "receipt.html", {"receipt": receipt, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")


@app.post("api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists", )

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists", )

    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.get("/api/receipts", response_model=list[ReceiptResponse])
def get_receipts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Receipt))
    receipts = result.scalars().all()
    return receipts

@app.post("api/receipts", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED,)
def create_receipt(data: ReceiptCreate, db: Annotated[Session, Depends(get_db)]) -> models.Receipt:

    receipt = models.Receipt(**data.model_dump(exclude=["items"]))

    receipt.items = [models.ReceiptItem(**item.model_dump()) for item in data.items]
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt

    # with open("receipt.json", "r", encoding="utf-8") as file:
    #     json.dump(r.json(), file, indent=4)
    # r = json.load(open("receipt.json", encoding="utf-8"))
    # result = db.execute(select(models.User).where(models.User.id == receipt.user_id))
    # user = result.scalars().first()
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # new_receipt = models.Receipt(title=r.title, description=receipt.description, user_id=receipt.user_id)


@app.get("/api/receipts/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(receipt_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Receipt).where(models.Receipt.id == receipt_id))
    receipt = result.scalars().first()
    if receipt:
        return receipt
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt no found")


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
async def show_422(request, exc):
    print(exc.errors())
    return JSONResponse({"detail": exc.errors()}, status_code=422)

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again."
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


