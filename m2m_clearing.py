import hmac
import hashlib
import time
from decimal import Decimal, ROUND_DOWN
from fastapi import HTTPException, Request

class ProductionM2MMicroClearingEngine:
    def __init__(self, settlement_secret: str = "nexus_m2m_secret_2026", max_time_drift: int = 30):
        self.secret_key = settlement_secret.encode()
        self.max_time_drift = max_time_drift  # 允许的最大时间戳漂移（秒），防重放

    async def settle_agent_transaction(self, request: Request):
        agent_id = request.headers.get("x-agent-id")
        payment_token = request.headers.get("x-payment-token")
        raw_amount = request.headers.get("x-payload-amount", "0.0")
        timestamp_str = request.headers.get("x-timestamp")
        nonce = request.headers.get("x-nonce")

        # 1. 基础凭证与防重放参数校验
        if not agent_id or not payment_token or not timestamp_str or not nonce:
            raise HTTPException(status_code=402, detail="Payment Required: Missing credentials, timestamp, or nonce.")

        # 2. 校验时间戳防重放攻击
        try:
            req_time = int(timestamp_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format.")
        
        current_time = int(time.time())
        if abs(current_time - req_time) > self.max_time_drift:
            raise HTTPException(status_code=403, detail="Settlement Failed: Request expired or time drift too large.")

        # 3. 使用 Decimal 转换金额，杜绝浮点数精度误差
        try:
            payload_amount = Decimal(raw_amount).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payload amount format.")

        # 4. 构建严密的 HMAC 签名字段 (加入 nonce 与时间戳)
        message = f"{agent_id}:{payload_amount}:{timestamp_str}:{nonce}".encode()
        expected_token = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

        # 5. 时序安全比对
        if not hmac.compare_digest(expected_token, payment_token):
            raise HTTPException(status_code=403, detail="Settlement Failed: Invalid M2M cryptographic payment signature.")

        print(f"[Production M2M] 智能体清算成功 | 代理ID: {agent_id} | 金额: ${payload_amount} | 时间戳: {req_time}")
        return True

prod_m2m_engine = ProductionM2MMicroClearingEngine()
