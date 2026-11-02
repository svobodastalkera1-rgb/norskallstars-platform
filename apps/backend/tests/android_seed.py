"""Reuse the approved synthetic client scenario; never touch ordinary runtime DBs."""

import asyncio

from browser_seed import main

if __name__ == "__main__":
    asyncio.run(main("android"))
