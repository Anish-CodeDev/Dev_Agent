import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
import asyncio
import json
class RedisUtils:
    def __init__(self):
        self.retry = Retry(ExponentialBackoff(), retries=1)
        self.r = redis.Redis(decode_responses=True,retry=self.retry)

    async def emit(self,sid,role,content):
        try:
            working = await self.r.ping()
        except:
            working = False
            await self.r.aclose()
            print("Error occurred")
        if(working):
            key = f"session:{sid}:events"
            await self.r.xadd(key,{"role":role,"content":content},maxlen=2000,approximate=True)
            await self.r.expire(key,18000)
            await self.r.aclose()

    async def stream(self,sid,last):
        last = 0
        try:
            working =  await self.r.ping()

        except:
            working= False
            await self.r.aclose()
            print("An error occurred")
            yield None

        if(working):
            print("Went inside")
            while True:
                res = await self.r.xread({f"session:{sid}:events":last},block=15000)
                print(res)
                
                if not res:
                    yield ":keepalive\n\n"
                    continue

                for _, entries in res:
                    for eid,fields in entries:
                        last = eid
                        yield f"id: {eid}\ndata: {json.dumps(fields)}\n\n"