import asyncio
from pprint import pprint

from app.osint.workers.github import github_worker

async def main():
    result = await github_worker("Guillermo Rauch")
    pprint(result)

asyncio.run(main())
