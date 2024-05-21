import asyncio
from threading import Lock
import requests

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r

async def api_loop(lock: Lock, queue, area_id: int, entry: bool, base_url: str, token: str):
    while True:
        await asyncio.sleep(1)
        lock.acquire()
        if not queue:
            # print("Queue is empty")
            lock.release()
            continue
        result = queue.pop(0)
        lock.release()
        print(f"Proccessing {result}")
        api_result = post_anpr_result(result, area_id, entry, base_url, token)
        print(f"Proccessed {result}. Result: {api_result}")


def post_anpr_result(plate: str, area_id: int, entry: bool, base_url: str, token: str):
    # return "Testing"
    result = requests.post(
        url=f"{base_url}/Area/details/anplr/{area_id}",
        json={
            "plateNumber": plate,
            "entry": entry
        },
        auth=BearerAuth(token=token),
        verify="/Users/mohamadshahin/Downloads/Certificate.pem",
        cert="/Users/mohamadshahin/Downloads/Certificate.pem",
    )

    return result.content

def register_camera_url(area_id: int, entry: bool, base_url: str, token: str):
    result = requests.post(
        url=f"{base_url}/Area/details/anplr/stream/{area_id}?url={base_url}&entry={entry}",
        auth=BearerAuth(token=token),
        verify="/Users/mohamadshahin/Downloads/Certificate.pem",
        cert="/Users/mohamadshahin/Downloads/Certificate.pem",
    )

    return result.content



async def start_api(lock: Lock, queue, area_id: int, entry: bool, base_url: str, token: str):
    await api_loop(lock, queue, area_id, entry, base_url, token)