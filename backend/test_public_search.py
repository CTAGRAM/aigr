import asyncio
from app.osint.public_search import public_search

async def main():
    result = await public_search("Who is Guillermo Rauch?")
    print(result)

asyncio.run(main())
