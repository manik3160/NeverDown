import asyncio
import os
import sys

sys.path.append(os.getcwd())

from database.connection import init_db, get_session
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository
from database.repositories.audit_repo import AuditRepository
from services.orchestrator import Orchestrator, OrchestrationContext
from models.incident import IncidentCreate, IncidentSeverity, IncidentSource, IncidentMetadata, RepositoryInfo

async def main():
    print("Starting pipeline trigger script...")
    
    await init_db()
    
    async with get_session() as session:
        incident_repo = IncidentRepository(session)
        patch_repo = PatchRepository(session)
        audit_repo = AuditRepository(session)
        
        repo_url = "https://github.com/mohitsaini958/CRUD-App"
        incident_data = IncidentCreate(
            title="Crash: ReferenceError: PORT is not defined",
            description="Application crashed on startup due to undefined PORT variable.",
            severity=IncidentSeverity.HIGH,
            source=IncidentSource.LOGS,
            logs="""
ReferenceError: PORT is not defined
    at Object.<anonymous> (backend/index.js:15:12)
    at Module._compile (node:internal/modules/cjs/loader:1376:14)
    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)
    at Module.load (node:internal/modules/cjs/loader:1207:32)
    at Module._load (node:internal/modules/cjs/loader:1023:12)
    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:135:12)
    at node:internal/main/run_main_module:28:49
            """,
            metadata=IncidentMetadata(
                repository=RepositoryInfo(
                    url=repo_url,
                    branch="main"
                )
            )
        )
        
        incident = await incident_repo.create(incident_data)
        print(f"Created Incident: {incident.id}")
        
        context = OrchestrationContext(
            incident_id=incident.id,
            repo_url=repo_url,
            logs=incident_data.logs,
            stack_trace=incident_data.logs
        )
        
        orchestrator = Orchestrator(
            incident_repo=incident_repo,
            patch_repo=patch_repo,
            audit_repo=audit_repo
        )
        
        print(f"Running pipeline for incident {incident.id}...")
        success = await orchestrator.process_incident(context)
        
        if success:
            print(f"Pipeline Succeeded! PR URL: {context.pull_request.pr_url}")
        else:
            print("Pipeline Failed.")
            if context.sanitization_report:
                print("Sanitization: OK")
            if context.detective_report:
                print("Detective: OK")
            if context.reasoner_output:
                print("Reasoner: OK")
            if context.verification_result:
                print(f"Verification: {context.verification_result.status}")
            if context.pull_request:
                print("Publisher: OK")

if __name__ == "__main__":
    asyncio.run(main())
