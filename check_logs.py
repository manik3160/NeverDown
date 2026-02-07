import asyncio
import uuid
from database.connection import get_session
from database.models import IncidentORM, AuditLogORM
from sqlalchemy import select

async def check_incident_logs(incident_id_str: str):
    async with get_session() as db:
        incident_id = uuid.UUID(incident_id_str)
        query = select(AuditLogORM).filter(AuditLogORM.incident_id == incident_id).order_by(AuditLogORM.timestamp)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        with open("logs_report.txt", "w") as f:
            f.write(f"Audit logs for incident {incident_id}:\n")
            for log in logs:
                f.write(f"[{log.timestamp}] {log.event_type}: {log.event_data}\n")
        print("Logs written to logs_report.txt")

if __name__ == "__main__":
    incident_id = "44da5b46-af03-444c-bd30-4480a9207829"
    asyncio.run(check_incident_logs(incident_id))
