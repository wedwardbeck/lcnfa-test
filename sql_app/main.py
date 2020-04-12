# from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

from . import crud, deps, models, schemas, security
from .api import items, users
from .database import SessionLocal, engine
from .settings import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(users.router, tags=["users"])
app.include_router(items.router, tags=["items"])


app.mount("/static", StaticFiles(directory="static"), name="static")


# Dependency
# def get_db():
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)


# @app.get("/users/", response_model=List[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users
#
#
# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# #
# # @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# # def create_item_for_user(
# #     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# # ):
# #     return crud.create_user_item(db=db, item=item, user_id=user_id)
#
#
# @app.get("/items/", response_model=List[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    user = crud.get_user_by_email(db, settings.super_user_email)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.super_user_email, password=settings.super_user_password
        )
        crud.create_user(db, user_in)
    db.close()


@app.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return {
        "access_token": security.create_access_token(subject=user.id),
        "token_type": "bearer",
    }
