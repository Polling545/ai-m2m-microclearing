import hmac
import hashlib
from fastapi import HTTPException, Request

class M2MMicroClearingEngine:
    def __init__(self, settlement_secret: str = "nexus_m2m_secret_2026"):
        self.secret_key = settlement_secret.encode()

    async def settle_agent_transaction(self, request: Request):
        agent_id = request.headers.get("x-agent-id")
        payment_token = request.headers.get("x-payment-token")
        payload_amount = float(request.headers.get("x-payload-amount", "0.0"))

        if not agent_id or not payment_token:
            raise HTTPException(status_code=402, detail="Payment Required: Missing autonomous agent credentials or payment token.")

        expected_token = hmac.new(
            self.secret_key,
            f"{agent_id}:{payload_amount}".encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_token, payment_token):
            raise HTTPException(status_code=403, detail="Settlement Failed: Invalid M2M cryptographic payment signature.")

        print(f"[M2M Clearing] 智能体自主清算成功 | 代理ID: {agent_id} | 划拨金额: ${payload_amount:.6f}")
        return True

m2m_engine = M2MMicroClearingEngine()
