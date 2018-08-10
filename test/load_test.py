# https://aiohttp.readthedocs.io/en/stable/
# https://www.artificialworlds.net/blog/2017/06/12/making-100-million-requests-with-python-aiohttp/
# https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
import aiohttp
import asyncio
import async_timeout
from datetime import datetime
import dateutil
import time
from aiohttp import ClientSession

loop = asyncio.get_event_loop()

tasks = []
url = 'https://d8dsx2bkn9.execute-api.eu-west-1.amazonaws.com/api/sigfox?time={}&id={}&data=02180AE4&test=test'

async def fetch_url(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            response = await response.read()
            print("fetched url" + url)

for i in range(10000):
    # task = asyncio.ensure_future(fetch_url(url.format(i)))
    task = asyncio.ensure_future(fetch_url(url.format(str(int(round(time.time()))), "LoadTest" + str(i))))
    tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))

