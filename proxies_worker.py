import os
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()

async def my_script():
    os.system("save_proxies.py")

@app.on_event("startup")
async def schedule_script():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(my_script, "interval", hours=24)
    scheduler.start()

