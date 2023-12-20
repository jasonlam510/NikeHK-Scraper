import asyncio
import random

async def random_sleep(min, max):
    sleep_time = random.uniform(min, max)  # Random sleep between 0.5 and max seconds
    await asyncio.sleep(sleep_time)

async def sleep(sleep_time):
    await asyncio.sleep(sleep_time)