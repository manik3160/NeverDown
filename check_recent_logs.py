import asyncio
from database.connection import get_session
from database.models import AuditLogORM
from sqlalchemy import select

async def check_recent_logs():
    async with get_session() as db:
        query = select(AuditLogORM).order_by(AuditLogORM.timestamp.desc()).limit(10)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        for log in logs:
            print(f"[{log.timestamp}] {log.event_type}: {log.event_data}")

if __name__ == "__main__":
    asyncio.run(check_recent_logs())
