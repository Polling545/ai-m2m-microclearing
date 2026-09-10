import hmac
import hashlib
import requests
import time

GATEWAY_URL = "http://127.0.0.1:8000/v1/settlement/sync"
SETTLEMENT_SECRET_KEY = b"nexus_m2m_secret_2026"

agent_id = "agent-alpha-007"
payload_amount = 0.05
nonce = int(time.time() * 1000)
timestamp = int(time.time())

# 计算签名
message = f"{agent_id}:{payload_amount}".encode()
payment_token = hmac.new(
    SETTLEMENT_SECRET_KEY,
    message,
    hashlib.sha256
).hexdigest()

headers = {
    "x-agent-id": agent_id,
    "x-payment-token": payment_token,
    "x-payload-amount": str(payload_amount),
    "x-nonce": str(nonce),
    "x-timestamp": str(timestamp)
}

print(f"正在向网关发起 M2M 微支付结算请求，Agent ID: {agent_id}...")
response = requests.post(GATEWAY_URL, headers=headers)

print(f"响应状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
