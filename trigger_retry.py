import httpx
import asyncio

async def retry_failed_incident():
    incident_id = "44da5b46-af03-444c-bd30-4480a9207829"
    async with httpx.AsyncClient() as client:
        response = await client.post(f"http://localhost:8000/api/v1/incidents/{incident_id}/retry")
        print(response.status_code)
        print(response.json())

if __name__ == "__main__":
    asyncio.run(retry_failed_incident())
