import asyncio
import random
import time
import random

async def async_random_sleep(min, max):
    sleep_time = random.uniform(min, max)  # Random sleep between 0.5 and max seconds
    await asyncio.sleep(sleep_time)

async def async_sleep(sleep_time):
    await asyncio.sleep(sleep_time)

def random_sleep(min, max):
    time.sleep(random.randint(min, max))

def sleep(sleep_time):
    time.sleep(sleep_time)