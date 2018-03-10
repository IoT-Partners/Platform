# https://aiohttp.readthedocs.io/en/stable/
# https://www.artificialworlds.net/blog/2017/06/12/making-100-million-requests-with-python-aiohttp/
# https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
import aiohttp
import asyncio
import async_timeout
from aiohttp import ClientSession

loop = asyncio.get_event_loop()

tasks = []
# I'm using test server localhost, but you can use any url
# url = "http://localhost:8080/{}"
url = 'http://httpbin.org/get'

async def fetch_url(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            response = await response.read()
            print(response)

for i in range(5):
    # task = asyncio.ensure_future(fetch_url(url.format(i)))
    task = asyncio.ensure_future(fetch_url(url))
    tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))
