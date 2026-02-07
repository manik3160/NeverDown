import asyncio
import json
from database.connection import get_session
from database.models import IncidentORM
from models.incident import IncidentStatus
from sqlalchemy import select

async def check_failed_incidents():
    async with get_session() as db:
        query = select(IncidentORM).filter(IncidentORM.status == IncidentStatus.FAILED)
        result = await db.execute(query)
        failed_incidents = result.scalars().all()
        
        with open("failed_report.txt", "w") as f:
            f.write(f"Found {len(failed_incidents)} failed incidents.\n\n")
            for i in failed_incidents:
                f.write(f"ID: {i.id}\n")
                f.write(f"Title: {i.title}\n")
                repo_info = i.incident_metadata.get('repository', {})
                f.write(f"Repo: {repo_info.get('url')}\n")
                f.write(f"Branch: {repo_info.get('branch')}\n")
                f.write(f"Error Message: {i.error_message}\n")
                f.write(f"Current State: {i.current_state}\n")
                f.write("-" * 40 + "\n")
        print("Report generated in failed_report.txt")

if __name__ == "__main__":
    asyncio.run(check_failed_incidents())
