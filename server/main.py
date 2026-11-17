
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

from ocr import ocr, OCRError

from schemas import ReceiptResponse, ReceiptCreate, UserCreate, UserResponse, ReceiptItemCreate

from typing import Annotated

from text_utils import clean_description, clean_title

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
    try:
        r = ocr(receipt_image )
    except OCRError as e:
        raise HTTPException(status_code=422, detail=str(e))
    new = {
    "retailer": r.get("merchant_name"),
    "purchase_date": r.get("date"),
    "currency": r.get("currency"),
    "total": r.get("total"),
    }

    new["items"] = [{"description": i.get("description"), "amount": i.get("amount")} for i in r.get("items", [])]

    # json.dump(new, open("pantree_receipt.json", "w", encoding="utf-8"), indent=4)

    data = ReceiptCreate( 
        retailer=clean_title(r.get("merchant_name")),
        raw_retailer=r.get("merchant_name"),
        currency=r.get("currency"), total=r.get("total"),
        purchase_date=r.get("date"),
        items=[ReceiptItemCreate(description=clean_description(i["description"]),
        raw_description=i["description"],
        amount=i["amount"]) 
        for i in r.get("items",[])])
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
        title = receipt.retailer[:50]
        return templates.TemplateResponse(request, "receipt.html", {"receipt": receipt, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

# TODO: Needs to be finished right now doesnt return anything

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
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
    return new_user

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

@app.post("/api/receipts", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED,)
def create_receipt(data: ReceiptCreate, db: Annotated[Session, Depends(get_db)]) -> models.Receipt:

    receipt = models.Receipt(**data.model_dump(exclude=["items"]))

    receipt.items = [models.ReceiptItem(**item.model_dump()) for item in data.items]
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


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
def validation_exception_handler(request: Request, exception: RequestValidationError):
    print(exception.errors())
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


