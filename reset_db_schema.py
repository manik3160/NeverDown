import asyncio
from database.connection import drop_db, init_db

async def reset():
    print("Dropping database tables...")
    await drop_db()
    print("Recreating database tables with updated enums...")
    await init_db()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(reset())
