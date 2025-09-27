from fastapi import FastAPI
from router.user import users
from AgentWork import agentno1
from fastapi.middleware.cors import CORSMiddleware
from databaseconfigs.database import engine
from databaseconfigs.model import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,  
        allow_methods=["*"],    
        allow_headers=["*"],     
    )

app.include_router(users.router)
app.include_router(agentno1.router, prefix="/agent", tags=["Agent"])

