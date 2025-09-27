from databaseconfigs.database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    useremail = Column(String, nullable=False)
    password = Column(String, nullable=False)

class Menu(Base):
    __tablename__ = "menu"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String ,nullable=False)
    desc = Column(String, nullable=False)
    price = Column(String, nullable=False)
    image = Column(String ,nullable=False)
    rating = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    name = Column(String , nullable=False)
    description = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    useremail = Column(String, nullable=False)
    orderid = Column(String, nullable=False)

class OrderFood(Base):
    __tablename__ = "order_food"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    table_no = Column(String, nullable=False)
    useremail = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    item_description = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    orderid = Column(String, nullable=False)
    total = Column(Float, nullable=False)
    location_name = Column(String, nullable=False)
    status = Column(String, default="Pending")  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class KitchenOrder(Base):
    __tablename__ = "kitchen"
    id = Column(Integer, primary_key=True)
    orderid = Column(String, nullable=False)
    useremail = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    item_description = Column(String, nullable=False)
    item_quantity = Column(Integer, nullable=False)

class OrderFood2(Base):
    __tablename__ = "order_food2"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    table_no = Column(String, nullable=False)
    useremail = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    item_description = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    orderid = Column(String, nullable=False)
    total = Column(Float, nullable=False)
    location_name = Column(String, nullable=False)
    status = Column(String, default="Pending")  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(Boolean, nullable=False, default=False)

class FeedBack(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)