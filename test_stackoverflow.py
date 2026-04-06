import asyncio
import os
import sys

sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from database.connection import init_db, get_session
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository
from database.repositories.audit_repo import AuditRepository
from services.orchestrator import Orchestrator, OrchestrationContext
from models.incident import IncidentCreate, IncidentSeverity, IncidentSource, IncidentMetadata, RepositoryInfo

async def main():
    print("Starting StackOverflow pipeline test script...")
    
    await init_db()
    
    async with get_session() as session:
        incident_repo = IncidentRepository(session)
        patch_repo = PatchRepository(session)
        audit_repo = AuditRepository(session)
        
        repo_url = "https://github.com/manik3160/Stack-Overflow"
        incident_data = IncidentCreate(
            title="Next.js Build Failure: module not defined, module not found",
            description="The CI build failed with multiple webpack errors, including missing packages (canvas-confetti), unresolvable aliases (@/utils/cn), and an ES module scope error in postcss.config.mjs",
            severity=IncidentSeverity.HIGH,
            source=IncidentSource.LOGS,
            logs="""
  ▲ Next.js 14.2.4

   Creating an optimized production build ...
Failed to compile.

src/app/layout.tsx
An error occurred in `next/font`.

ReferenceError: module is not defined in ES module scope
    at file:///Users/manik/NeverDown/Stack-Overflow/postcss.config.mjs:2:1

./src/components/magicui/border-beam.tsx
Module not found: Can't resolve '@/utils/cn'

./src/components/magicui/confetti.tsx
Module not found: Can't resolve 'canvas-confetti'

./src/components/magicui/magic-card.tsx
Module not found: Can't resolve '@/utils/cn'

./src/components/magicui/number-ticker.tsx
Module not found: Can't resolve '@/utils/cn'

src/middleware.ts:14:24
Type error: Property 'nextError' does not exist on type 'typeof NextResponse'.

  12 |     getOrCreateStorage()
  13 |   ])
> 14 |   return NextResponse.nextError() // Intentional CI error here
     |                        ^
  15 | }

> Build failed because of webpack errors
Exit code: 1""",
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
            print(f"Pipeline Succeeded! PR URL: {context.pull_request.pr_url if context.pull_request else 'None'}")
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
