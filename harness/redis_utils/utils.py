import json
import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry


class RedisUtils:
    def __init__(self):
        self.retry = Retry(ExponentialBackoff(), retries=1)
        self.r = redis.Redis(host='redis-service',port=6379,decode_responses=True, retry=self.retry)

    async def emit(self, sid, role, content):
        try:
            working = await self.r.ping()
        except:
            working = False
            await self.r.aclose()
            print("Error occurred")

        if working:

            fields = {"role": role, "content": content}
            key = f"session:{sid}:events"
            await self.r.xadd(key, fields)
            await self.r.expire(key,18000)
            await self.r.aclose()

    async def stream(self, sid, last="0-0"):
        try:
            working = await self.r.ping()
        except:
            working = False
            await self.r.aclose()
            print("Error occurred")
        if working:

            key = f"session:{sid}:events"
            while True:
                streams = await self.r.xread({key: last}, block=15000, count=100)
                if not streams:
                    yield ":keepalive\n\n"
                    continue

                for _, entries in streams:
                    for event_id, fields in entries:
                        last = event_id
                        yield f"id: {event_id}\ndata: {json.dumps(fields)}\n\n"