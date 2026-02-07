import asyncio
import uuid
import os
# Disable sqlalchemy logging for clean output
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from database.connection import get_session
from database.models import IncidentORM
from sqlalchemy import select

async def check_incident_status(incident_id_str: str):
    async with get_session() as db:
        incident_id = uuid.UUID(incident_id_str)
        query = select(IncidentORM).filter(IncidentORM.id == incident_id)
        result = await db.execute(query)
        i = result.scalar_one_or_none()
        
        if i:
            print(f"ID: {i.id}")
            print(f"Status: {i.status}")
            print(f"State: {i.current_state}")
            print(f"Error: {i.error_message}")
        else:
            print("Not found")

if __name__ == "__main__":
    incident_id = "44da5b46-af03-444c-bd30-4480a9207829"
    asyncio.run(check_incident_status(incident_id))
