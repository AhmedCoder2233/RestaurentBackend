from pydantic import BaseModel
import random
from uuid import uuid4

class UserSchema(BaseModel):
    username:str
    useremail:str
    password:str

class UserLoginSchema(BaseModel):
    useremail:str
    password:str

class MenuSchema(BaseModel):
    title:str
    desc:str
    price:str
    image:str
    rating:int
    
class OrderedItemSchema(BaseModel):
    name:str
    description:str
    price:str
    quantity:int
    useremail:str
    orderid:str = uuid4()

class OrderSchema(BaseModel):
    name:str
    table_no:str
    useremail:str
    item_name:str
    item_description:str
    price:str
    quantity:int
    orderid:str
    total:float
    location_name:str
    status:str
    
    
class OrderSchema2(BaseModel):
    name:str
    table_no:str
    useremail:str
    item_name:str
    item_description:str
    price:str
    quantity:int
    orderid:str
    total:float
    location_name:str
    status:str
    
class KitchenSchema(BaseModel):
    orderid: str
    useremail:str
    item_name:str
    item_description:str
    item_quantity:int

class StaffSchema(BaseModel):
    name:str
    status:bool = False