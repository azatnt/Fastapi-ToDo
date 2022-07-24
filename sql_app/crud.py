from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from sql_app import models
from sql_app.schemas import UserCreate, ItemCreate
from passlib.context import CryptContext


SECRET_KEY = "fast-api"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password):
    return pwd_context.hash(password)


def update_my_item_by_id(db: Session, id: int, title: str, description: str, user_id: int):
    item = db.query(models.Item).get(id)
    if item and item.user_id == user_id:
        item.title = title
        item.description = description
        db.commit()
    db.close()
    if not item:
        return {"detail": f"item with id {id} not found"}
    return item


def delete_my_item(db: Session, item_id: int, user_id: int):
    item = db.query(models.Item).get(item_id)
    if item and item.user_id == user_id:
        db.delete(item)
        db.commit()
    db.close()
    if not item:
        return {"detail": f"item with id {item_id} not found"}
    return {"detail": "item successfully deleted"}


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(user_id: int, db: Session):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(username: str, db: Session):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session):
    # return db.query(models.User).join(models.Item, models.User.id == models.Item.user_id, isouter=True).all()
    return db.query(models.User).all()


def create_new_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(id: int, db: Session):
    user = db.query(models.User).get(id)
    if not user:
        return {"detail": f"user with id {id} not found"}
    return user


def create_user_task(db: Session, item: ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), user_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
