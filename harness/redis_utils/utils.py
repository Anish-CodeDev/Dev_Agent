import json
import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry


APPROVAL_TIMEOUT_SECONDS = 15 * 60


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

    async def create_approval(self, sid, approval_id):
        key = f"session:{sid}:approval:{approval_id}:state"
        
        try:
            created = await self.r.set(
                key,
                "pending",
                ex=APPROVAL_TIMEOUT_SECONDS,
                nx=True,
            )
        finally:
            await self.r.aclose()
        if not created:
            raise RuntimeError("Unable to register the code review request.")

    async def wait_for_approval(self, sid, approval_id):
        decision_key = f"session:{sid}:approval:{approval_id}:decision"
        
        try:
            response = await self.r.blpop(decision_key, timeout=APPROVAL_TIMEOUT_SECONDS)
        finally:
            await self.r.aclose()
        if response is None:
            raise TimeoutError("The code review request expired before a decision was received.")
        if response[1] not in ("true", "false"):
            raise RuntimeError("Received an invalid code review decision.")
        return response[1] == "true"

    async def clear_approval(self, sid, approval_id):
        keys = [
            f"session:{sid}:approval:{approval_id}:state",
            f"session:{sid}:approval:{approval_id}:decision",
        ]
        
        try:
            await self.r.delete(*keys)
        finally:
            await self.r.aclose()

    async def resolve_approval(self, sid, approval_id, approved):
        state_key = f"session:{sid}:approval:{approval_id}:state"
        decision_key = f"session:{sid}:approval:{approval_id}:decision"
        script = """
        local state = redis.call("GET", KEYS[1])
        if state == ARGV[3] then
            return 1
        end
        if state ~= "pending" then
            return 0
        end
        if redis.call("LLEN", KEYS[2]) > 0 then
            return 0
        end
        redis.call("RPUSH", KEYS[2], ARGV[1])
        redis.call("EXPIRE", KEYS[2], ARGV[2])
        redis.call("SET", KEYS[1], ARGV[3], "EX", ARGV[2])
        return 1
        """
        try:
            resolved = await self.r.eval(
                script,
                2,
                state_key,
                decision_key,
                "true" if approved else "false",
                APPROVAL_TIMEOUT_SECONDS,
                "approved" if approved else "rejected",
            )
        finally:
            await self.r.aclose()
        return resolved == 1