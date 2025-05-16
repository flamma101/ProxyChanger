from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
# Allow requests from any origin (or lock down to your GH pages domain)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Test URLs
HTTPS_TEST = 'https://httpbin.org/ip'
HTTP_TEST  = 'http://httpbin.org/ip'

def test_proxy(proxy: str, timeout: float):
    """
    Returns (working: bool, info: int|str)
    info is responseTime in ms if working, or exception message if not.
    """
    proxy_url = f"http://{proxy}"
    proxies = {"http": proxy_url, "https": proxy_url}

    # 1) Try HTTPS (CONNECT)
    start = time.time()
    try:
        resp = requests.get(HTTPS_TEST, proxies=proxies, timeout=timeout)
        elapsed = int((time.time() - start) * 1000)
        return True, elapsed
    except Exception:
        pass

    # 2) Fallback to HTTP GET
    start = time.time()
    try:
        resp = requests.get(HTTP_TEST, proxies=proxies, timeout=timeout)
        elapsed = int((time.time() - start) * 1000)
        return True, elapsed
    except Exception as e:
        return False, str(e)

@app.route('/api/check', methods=['OPTIONS'])
def preflight():
    # CORS preflight handled by flask-cors, but this ensures a 204
    return make_response('', 204)

@app.route('/api/check', methods=['POST'])
def check_proxies():
    data = request.get_json(force=True)
    proxies = data.get('proxies', [])
    timeout = float(data.get('timeout', 5))

    results = []
    # Parallelize up to 20 threads
    with ThreadPoolExecutor(max_workers=20) as pool:
        future_map = { pool.submit(test_proxy, p, timeout): p for p in proxies }
        for fut in as_completed(future_map):
            p = future_map[fut]
            working, info = fut.result()
            entry = {"proxy": p, "working": working}
            if working:
                entry["responseTime"] = info
            else:
                entry["reason"] = info
            results.append(entry)

    return jsonify(results=results)

if __name__ == '__main__':
    # Local dev: flask run or python app.py
    app.run(host='0.0.0.0', port=5000, debug=True)
