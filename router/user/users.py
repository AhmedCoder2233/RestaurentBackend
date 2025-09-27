from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from databaseconfigs.database import LocalSession
from databaseconfigs.schema import UserSchema, UserLoginSchema, MenuSchema, OrderedItemSchema, OrderSchema, KitchenSchema, OrderSchema2, StaffSchema
from databaseconfigs.model import User, Menu, Order, OrderFood, KitchenOrder, OrderFood2, Staff, FeedBack
from sqlalchemy.orm import Session
from ..auth.authentication import create_token, hash_password, verify_password, verify_token
from email.message import EmailMessage
from dotenv import load_dotenv
from fastapi.background import BackgroundTasks
import smtplib
import os

load_dotenv()

router = APIRouter(
    prefix="/users",      
    tags=["Users"],    
)

security = HTTPBearer()

def getdb():
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()


def sendEmail(to:str, subject:str, body:str):
    message = EmailMessage()
    message["to"] = to
    message["from"] = "ahmedpubgking3388@gmail.com"
    message["subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("ahmedpubgking3388@gmail.com", os.getenv("APP_PASS"))
        server.send_message(message)

# ----------------- SIGNUP -----------------
@router.post("/signup")
def SignUP(data: UserSchema, db: Session = Depends(getdb)):
    checkemail = db.query(User).filter(User.useremail == data.useremail).first()
    if checkemail:
        raise HTTPException(status_code=409, detail="User Already Exists")

    hashedPassword = hash_password(password=data.password)

    new_user = User(
        username=data.username,
        useremail=data.useremail,
        password=hashedPassword
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "detail": "User Signup Successfully",
        "username": new_user.username,
        "useremail": new_user.useremail
    }


# ----------------- SIGNIN -----------------
@router.post("/signin")
def SignIN(data: UserLoginSchema, db: Session = Depends(getdb)):
    checkemail = db.query(User).filter(User.useremail == data.useremail).first()
    if not checkemail or not verify_password(data.password, checkemail.password):
        raise HTTPException(detail="User Not Exist", status_code=404)
    token = create_token(checkemail.useremail)
    return {"token": token, "username": checkemail.username, "useremail": checkemail.useremail}


# ----------------- MENU -----------------
@router.get("/getmenu")
def getMenu(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    return db.query(Menu).all()

@router.get("/getmenu/foragent")
def getMenu(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    data = db.query(Menu).all()
    menu_data = [
        {
            "title": item.title,
            "desc": item.desc,
            "price": item.price
        }
        for item in data
    ]

    return {"menu": menu_data, "email": user.get("email")}

@router.get("/getorderbyemail/{email}")
def getOrderByEmail(email:str,credentials: HTTPAuthorizationCredentials = Depends(security), db:Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    data = db.query(OrderFood).filter(OrderFood.useremail == email).all()
    if data:
        return data
    return "No Order Found!"

# ----------------- PLACE ORDER -----------------
@router.post("/orderitem")
def OrderItem(order: OrderedItemSchema, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    data = Order(**order.model_dump())
    db.add(data)
    db.commit()
    return


# ----------------- GET USER ORDERS -----------------
@router.get("/getorders")
def getOrders(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")

    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=403, detail="Invalid token data")

    data = db.query(Order).filter(Order.useremail == user_email).all()
    if not data:
        raise HTTPException(status_code=404, detail="Order not found!")

    return data


# ----------------- DELETE SINGLE ORDER -----------------
@router.delete("/deleteorder/{order_id}")
def delete_order(order_id: str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    order = db.query(Order).filter(Order.orderid == order_id, Order.useremail == user["email"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return {"detail": f"Order {order_id} deleted successfully"}


# ----------------- SUBMIT ORDER -----------------
from datetime import datetime, timezone

@router.post("/submit")
def postOrder(order: OrderSchema, background_tasks: BackgroundTasks, db: Session = Depends(getdb), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    data = OrderFood(**order.model_dump())
    background_tasks.add_task(sendEmail, order.useremail, "Your Order Has Been Placed", "Your Order Is Placed and will be in your Table very Soon!")
    background_tasks.add_task(sendEmail, "ahmedmemon3344@gmail.com", "Order Arrived", f"Order placed from email: {data.useremail}, and the order is: {data.item_name} x {data.quantity}")
    db.add(data)
    db.commit()
    return "Order Booked Please Wait for Owner Approval"


@router.post("/submit2")
def postOrder(order: OrderSchema2, db: Session = Depends(getdb), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")

    data = OrderFood2(**order.model_dump())
    db.add(data)
    db.commit()
    return "Order Booked Please Wait for Owner Approval"

# ----------------- DELETE ALL USER ORDERS -----------------
@router.delete("/deleteallorders/{useremail}")
def delete_orders(useremail: str, db: Session = Depends(getdb), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    orders = db.query(Order).filter(Order.useremail == useremail).all()
    for order in orders:
        db.delete(order)
    db.commit()
    
    return {"detail": f"All orders for {useremail} deleted successfully."}


# ----------------- ADMIN ORDERS -----------------
@router.get("/adminorders")
def AdminOrder(db: Session = Depends(getdb)):
    return db.query(OrderFood).all()


# ----------------- ADMIN APPROVE ORDER -----------------
@router.put("/admin/order/{orderid}/accept")
def accept_order(orderid: str, db: Session = Depends(getdb)):
    order = db.query(OrderFood).filter(OrderFood.orderid == orderid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Approved & Now Processing"
    db.commit()
    return {"detail": "Order approved", "orderid": order.orderid, "status": order.status}


# ----------------- ADMIN REJECT ORDER -----------------
@router.put("/admin/order/{orderid}/reject")
def reject_order(orderid: str, db: Session = Depends(getdb)):
    order = db.query(OrderFood).filter(OrderFood.orderid == orderid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Rejected (This Item is not Avaliable)"
    db.commit()
    return {"detail": "Order rejected", "orderid": order.orderid, "status": order.status}

@router.get("/getstatus")
def getOrders(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")

    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=403, detail="Invalid token data")

    data = db.query(OrderFood).filter(OrderFood.useremail == user_email).all()
    if not data:
        raise HTTPException(status_code=404, detail="Order not found!")

    return data

@router.post("/kitchenorder")
def KitchenOrderFood(data:KitchenSchema ,db:Session = Depends(getdb)):
    savetodb = KitchenOrder(**data.model_dump())
    db.add(savetodb)
    db.commit()
    return

@router.get("/kitchenorder")
def getKitchenOrders(db:Session = Depends(getdb)):
    return db.query(KitchenOrder).all()

@router.put("/kitchen/order/{orderid}/done")
def accept_order(orderid: str, db: Session = Depends(getdb)):
    order = db.query(OrderFood).filter(OrderFood.orderid == orderid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Order Done"
    db.commit()
    return {"detail": "Order Done", "orderid": order.orderid, "status": order.status}

@router.delete("/delete/kitchen/order/{orderid}")
def deleteKitchenOrder(orderid:str, db:Session = Depends(getdb)):
    data = db.query(KitchenOrder).filter(KitchenOrder.orderid == orderid).first()
    db.delete(data)
    db.commit()
    return

@router.delete("/deleteownerorder/{orderid}")
def deleteOwnerOrder(orderid:str ,db:Session = Depends(getdb)):
    data = db.query(OrderFood2).filter(OrderFood2.orderid == orderid).first()
    db.delete(data)
    db.commit()
    return

@router.get("/ownerorders")
def getOwnerOrders(db:Session = Depends(getdb)):
    return db.query(OrderFood2).all()

@router.post("/addmenu")
def AddMenu(data:MenuSchema, db:Session = Depends(getdb)):
    saveToDB = Menu(**data.model_dump())
    db.add(saveToDB)
    db.commit()
    return

@router.delete("/deletemenu/{name}")
def DeleteMenu(name:str, db:Session = Depends(getdb)):
    data = db.query(Menu).filter(Menu.title == name).first()
    db.delete(data)
    db.commit()
    return

@router.get("/menu")
def getMenuForAdminPanel(db:Session = Depends(getdb)):
    return db.query(Menu).all()

@router.get("/staff")
def getStaff(db:Session = Depends(getdb)):
    return db.query(Staff).all()

@router.post("/staff")
def postStaff(data:StaffSchema, db:Session = Depends(getdb)):
    savetoDB = Staff(**data.model_dump())
    db.add(savetoDB)
    db.commit()
    return

@router.put("/staffstatusonline/{name}")
def changeStaffStatus(name:str, db:Session = Depends(getdb)):
    data = db.query(Staff).filter(Staff.name == name).first()
    data.status = True
    db.commit()
    return

@router.put("/staffstatusoffline/{name}")
def changeStaffStatus(name:str, db:Session = Depends(getdb)):
    data = db.query(Staff).filter(Staff.name == name).first()
    data.status = False
    db.commit()
    return

@router.get("/allcustomers")
def getAllCustomers(db:Session = Depends(getdb)):
    return db.query(OrderFood).all()

@router.post("/feedback/{message}")
def PostFeedBack(message:str,credentials: HTTPAuthorizationCredentials = Depends(security), db:Session = Depends(getdb)):
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    data = FeedBack(message=message)
    db.add(data)
    db.commit()
    return

@router.get("/feedback")
def getFeedBack(db:Session = Depends(getdb)):
    return db.query(FeedBack).all()