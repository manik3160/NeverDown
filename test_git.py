import asyncio

async def test_git():
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        print(f"Return code: {proc.returncode}")
        print(f"Stdout: {stdout.decode().strip()}")
        print(f"Stderr: {stderr.decode().strip()}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_git())
