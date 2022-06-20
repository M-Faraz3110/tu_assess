from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import sqlalchemy
import databases
import motor.motor_asyncio
from pymongo import MongoClient
from models import User, UserInDB, Token, TokenData
from dependencies import authenticate_user, create_access_token, get_current_active_user


MONGO_DETAILS = "mongodb://localhost:27017"
client = MongoClient(MONGO_DETAILS)
database = client.mydb


SECRET_KEY = "61b3ccc171463868608752edcf25ed364b5cbc1ebd5b52474009f3c70751fd48"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()  # GO TO 127.0.0.1/docs FOR UI


@app.post("/register")  # REGISTER USER
async def register(username: str = Form(), password: str = Form(), type: str = Form()):
    if type == "admin":
        database.admins.insert_one({
            "id": database.admins.count_documents({}) + 1,
            "username": username,
            "password": password,
            "type": type
        })
    elif type == "doctor":
        database.doctors.insert_one({
            "id": database.doctors.count_documents({}) + 1,
            "username": username,
            "password": password,
            "type": type,
            "time_left": 8
        })
    else:
        database.patients.insert_one({
            "id": database.patients.count_documents({}) + 1,
            "username": username,
            "password": password,
            "type": type
        })


@app.post("/login", response_model=Token)  # LOGIN, GET JWT TOKEN
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/doctors")  # ALL DOCTORS
async def getdocs():
    doctors = database.doctors

    cursor = doctors.find()
    res = {}

    for doc in cursor:
        res.update({
            doc["id"]: {
                "Name": doc["username"],
                "time left": doc["time_left"]}
        })
    return res


@app.get("/doctors/{docid}")  # SEARCH DOC BY ID
async def getdoc(docid: int):
    doctors = database.doctors

    cursor = doctors.find({"id": docid})
    res = {}

    for doc in cursor:
        if doc["id"] == docid:
            res.update({
                "Name": doc["username"],
                "time left": doc["time_left"]
            })
    if len(res) != 0:
        return res
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@ app.get("/doctors/{docid}/slots")  # DOCS AND SLOTS
async def getslots(docid: int, current_user: User = Depends(get_current_active_user)):
    pats = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}}
    apps = database.apps
    doctors = database.doctors
    if doctors.count_documents({"id": docid}) == 1:
        cursor = apps.find({"doc_id": docid})
    else:
        raise HTTPException(status_code=404, detail="Doctor Not Found")
    count = 1
    if current_user.type == "patient":
        for app in cursor:
            pats[count] = app["length"]
            count += 1

    else:
        for app in cursor:
            print(app)
            pats[count] = {
                "doctor ID": app["doc_id"],
                "patient ID": app["pat_id"],
                "length": app["length"]
            }
            count += 1

    return pats


@ app.post("/book")
async def book(docid: int, duration: int, current_user: User = Depends(get_current_active_user)):
    doctors = database.doctors
    apps = database.apps
    if current_user.type == "patient":
        doc = doctors.find_one({"id": docid})
        if doc["time_left"] > duration/60 and apps.count_documents({"doc_id": docid}) < 12:
            apps.insert_one({
                "app_id": apps.count_documents({}) + 1,
                "doc_id": docid,
                "pat_id": current_user.id,
                "length": duration
            })
            doctors.update_one(
                {"id": docid}, {"$inc": {"time_left": -duration/60}})
        else:
            return "Doctor is fully booked."

    else:
        raise HTTPException(status_code=403, detail="Not Permitted")


@ app.delete("/cancel/{app_id}")
async def cancel(app_id: int, current_user: User = Depends(get_current_active_user)):
    if current_user.type == "doctor" or current_user.type == "admin":
        apps = database.apps
        doctors = database.doctors
        if apps.count_documents({"app_id": app_id}) == 0:
            raise HTTPException(
                status_code=404, detail="Appointment Not Found")
        else:
            app = apps.find_one({"app_id": app_id})
        length = app["length"]
        docid = app["doc_id"]
        doctors.update_one(
            {"id": docid}, {"$inc": {"time_left": length/60}})
        apps.delete_one({"app_id": app_id})

    else:
        raise HTTPException(status_code=403, detail="Not Permitted")


@ app.get("/available")
async def avail(current_user: User = Depends(get_current_active_user)):
    avail = {}
    doctors = database.doctors
    apps = doctors.apps
    if current_user.type == "patient":
        for doc in doctors.find():
            if apps.count_documents({"doc_id": doc["id"]}) < 12 and doc["time_left"] != 0:
                avail.update({
                    len(avail) + 1: {
                        "Doctor": doc["username"],
                        "Time Left": doc["time_left"]
                    }
                })
        return avail
    elif current_user.type == "admin":
        for doc in doctors.find():
            avail.update({
                len(avail) + 1: {
                    "Doctor": doc["username"],
                    "Time Left": doc["time_left"]
                }
            })
        return avail


@ app.get("/history")
async def history(patient_id: Union[int, None] = None, current_user: User = Depends(get_current_active_user)):
    if current_user.type == "patient":
        if patient_id != current_user.id:
            return "Not Permitted"
        else:
            res = {}
            apps = database.apps
            apps = apps.find({"pat_id": current_user.id})
            for app in apps:
                res.update(
                    {len(res) + 1: {"Doctor": app["doc_id"],
                                    "Patient": app["pat_id"],
                                    "Length": app["length"]}
                     })
            return res

    elif current_user.type == "doctor" or current_user.type == "admin":
        res = {}
        apps = database.apps
        apps = apps.find({"pat_id": patient_id})
        for app in apps:
            res.update({len(res) + 1: {"Doctor": app["doc_id"],
                                       "Patient": app["pat_id"],
                                       "Length": app["length"]}

                        })
        return res


@ app.get("/appointments")
async def get_app(app_id: int, current_user: User = Depends(get_current_active_user)):
    apps = database.apps
    app = apps.find_one({"app_id": app_id})

    if app["pat_id"] == current_user.id or app["doc_id"] == current_user.id:
        return {
            "Doctor": app["doc_id"],
            "Patient": app["pat_id"],
            "Length": app["length"]
        }

    else:
        return "invalid ID"


@ app.get("/mostapps")
async def get_mostapps(current_user: User = Depends(get_current_active_user)):
    if current_user.type == "admin":
        doctors = database.doctors
        docs = {}
        apps = database.apps
        for app in apps.find():
            docid = app["doc_id"]
            doctor = doctors.find_one({"id": docid})
            if doctor["username"] in docs.keys():
                docs[doctor["username"]] += 1
            else:
                docs[doctor["username"]] = 1
        sorted_dict = dict(sorted(docs.items(),
                                  key=lambda item: item[1],
                                  reverse=True))
        print(sorted_dict)
        return sorted_dict
    else:
        raise HTTPException(status_code=403, detail="Not Permitted")


@app.get("/6+hours")
async def get_sixplushours(current_user: User = Depends(get_current_active_user)):
    if current_user.type == "admin":
        doctors = database.doctors
        res = {}
        for doc in doctors.find():
            if doc["time_left"] <= 2:
                res.update({len(res) + 1: {"Doctor": doc["username"],
                                           "Total appointment hours": 8 - doc["time_left"]}

                            })
        return res
    else:
        raise HTTPException(status_code=403, detail="Not Permitted")
