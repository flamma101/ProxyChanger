from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)  # Enable CORS

# Health‑check target
TARGET_URL = 'https://httpbin.org/ip'

@app.route('/api/check', methods=['POST'])
def check_proxies():
    data = request.get_json()
    proxies = data.get('proxies', ['208.86.33.26:3128'])
    timeout = data.get('timeout', 2)  # seconds

    results = []
    for proxy in proxies:
        proxy_url = f"http://{proxy}"
        proxy_dict = {
            "http": proxy_url,
            "https": proxy_url
        }
        start = time.time()
        try:
            # Issue request through the proxy
            resp = requests.get(TARGET_URL, proxies=proxy_dict, timeout=timeout)
            elapsed = int((time.time() - start) * 1000)  # ms
            results.append({
                "proxy": proxy,
                "working": True,
                "responseTime": elapsed
            })
        except requests.exceptions.Timeout:
            results.append({
                "proxy": proxy,
                "working": False,
                "reason": "Timeout"
            })
        except Exception as e:
            results.append({
                "proxy": proxy,
                "working": False,
                "reason": str(e)
            })

    return jsonify(results=results)

if __name__ == '__main__':
    app.run(port=5000, debug=False)
