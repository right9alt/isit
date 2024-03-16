import requests, os

class RequestManager:
  @staticmethod
  def post(url, json_data):
    response = requests.post(url, json=json_data, \
                             timeout=int(os.getenv("MAX_TIMEOUT")))
    result = {
      'status_code': response.status_code,
      'data': response.json()
    }
    return result