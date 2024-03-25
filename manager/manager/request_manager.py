import os
import httpx

class RequestManager:
    @staticmethod
    async def post(url, json_data):
        async with httpx.AsyncClient() as client:
          response = await client.post(url, json=json_data, timeout=float(os.getenv("MAX_TIMEOUT")))
          return {
              'status_code': response.status_code,
              'data': response.json()
          }