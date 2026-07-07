import asyncio

from app.osint.engine import lookup_person


async def main():

    result = await lookup_person(
        "Guillermo Rauch"
    )

    from pprint import pprint

    pprint(result)

asyncio.run(main())
