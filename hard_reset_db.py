import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from database.connection import init_db

load_dotenv()

async def reset_db():
    db_url = os.getenv("DATABASE_URL").replace("+asyncpg", "")
    print(f"Connecting to DB...")
    
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected. Dropping tables...")
        await conn.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS pull_requests CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS verifications CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS patches CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS analyses CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS incidents CASCADE;")
        
        print("Dropping enum types...")
        await conn.execute("DROP TYPE IF EXISTS incidentseverity CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS incidentsource CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS incidentstatus CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS prstatus CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS verificationstatus CASCADE;")
            
        await conn.close()
        
        print("Re-initializing tables...")
        await init_db()
        print("DB Reset Complete.")
    except Exception as e:
        print(f"Error during reset: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
