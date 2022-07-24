from datetime import timedelta

from debug_toolbar.middleware import DebugToolbarMiddleware

from fastapi import FastAPI, status, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from auth.authentication import authenticate_user, get_current_active_user
from auth.token import create_access_token
from sql_app.crud import *
from sql_app.database import engine, SessionLocal
from sql_app import schemas
from sqlalchemy.orm import Session
from sql_app.schemas import Token, User


models.Base.metadata.create_all(engine)

app = FastAPI(debug=True)

app.add_middleware(
    DebugToolbarMiddleware,
    panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


# Dependency
def get_db(request: Request):
    return request.state.db




@app.post("/create-user/", status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    created_user = create_new_user(db, user)
    return created_user


@app.get("/get-users/", status_code=status.HTTP_200_OK, response_model=List[schemas.User])
def get_all_users(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return get_users(db)


@app.get("/get-user/{id}", status_code=status.HTTP_200_OK, response_model=schemas.User)
def get_user(id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return get_user_by_id(id, db)


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm=Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"data": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user), token: str = Depends(oauth2_scheme)):
    return current_user


@app.post("/user/{user_id}/create-item/", response_model=schemas.Item)
def create_item_for_user(user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db),
                         token: str = Depends(oauth2_scheme)):
    created_item = create_user_task(db=db, item=item, user_id=user_id)
    return created_item


@app.put("/item/{id}")
def update_task(id: int, title: str, description: str,
                token: str = Depends(oauth2_scheme),
                current_user: User = Depends(get_current_active_user),
                db: Session = Depends(get_db)):
    my_item = update_my_item_by_id(db=db, id=id, title=title, description=description, user_id=current_user.id)
    return my_item


@app.delete("/item/{item_id}")
def delete_task(item_id: int, current_user: User = Depends(get_current_active_user),
                token: str = Depends(oauth2_scheme),
                db: Session = Depends(get_db)):
    item = delete_my_item(db=db, item_id=item_id, user_id=current_user.id)
    return item
