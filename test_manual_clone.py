import asyncio
import os
import shutil
from pathlib import Path

async def test_clone():
    repo_url = "https://github.com/mohitsaini958/CRUD-App"
    incident_id = "test-manual"
    clone_path = Path("./clones-test") / f"repo-{incident_id}"
    
    if clone_path.exists():
        shutil.rmtree(clone_path)
    clone_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = ["git", "clone", "--depth", "1", repo_url, str(clone_path)]
    print(f"Running: {' '.join(cmd)}")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        print(f"Return code: {proc.returncode}")
        print(f"Stdout: {stdout.decode().strip()[:100]}")
        print(f"Stderr: {stderr.decode().strip()[:100]}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_clone())
