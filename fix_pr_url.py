import asyncio
from uuid import UUID
from database.connection import get_session
from database.repositories.incident_repo import IncidentRepository

async def fix():
    async with get_session() as session:
        repo = IncidentRepository(session)
        incident_id = UUID("AEE9DB50-53B9-4EB2-8A2C-D5BBCB88BC47")
        incident = await repo.get(incident_id)
        if incident:
            await repo.set_pr_url(incident_id, "https://github.com/manik3160/Stack-Overflow/pull/5")
            print("Fixed incident locally")
        else:
            print("Incident not found locally")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(fix())
