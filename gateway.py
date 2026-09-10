import time
import hmac
import hashlib
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from distributed_sync import DistributedNonceEngine

app = FastAPI(title="AI Agent Sovereign Gateway", version="2.0.0")

nonce_engine = DistributedNonceEngine(node_id="node-us-east-01", secret_seed=b"secure_cluster_secret_seed")
SETTLEMENT_SECRET_KEY = b"nexus_m2m_secret_2026"

class NodeStateSyncPayload(BaseModel):
    node_id: str
    client_id: str
    last_nonce: int
    timestamp: int
    hmac_signature: str

@app.post("/v1/settlement/sync")
async def process_settlement_sync(request: Request):
    agent_id = request.headers.get("x-agent-id")
    payment_token = request.headers.get("x-payment-token")
    payload_amount = float(request.headers.get("x-payload-amount", "0.0"))
    nonce = int(request.headers.get("x-nonce", "0"))
    timestamp = int(request.headers.get("x-timestamp", "0"))

    if not agent_id or not payment_token:
        raise HTTPException(status_code=402, detail="Payment Required: Missing autonomous agent credentials or payment token.")

    expected_token = hmac.new(
        SETTLEMENT_SECRET_KEY,
        f"{agent_id}:{payload_amount}".encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_token, payment_token):
        raise HTTPException(status_code=403, detail="Settlement Failed: Invalid M2M cryptographic payment signature.")

    if not nonce_engine.verify_and_update_nonce(agent_id, nonce, timestamp):
        raise HTTPException(status_code=400, detail="Invalid nonce or potential replay attack detected.")

    sync_payload = nonce_engine.create_edge_sync_payload(agent_id, payload_amount, nonce)

    return {
        "status": "success",
        "node_id": nonce_engine.node_id,
        "client_id": agent_id,
        "net_amount": payload_amount,
        "sync_payload": sync_payload
    }

@app.post("/v1/cluster/sync-state")
async def receive_cluster_sync(payload: NodeStateSyncPayload):
    if payload.node_id == nonce_engine.node_id:
        return {"status": "skipped", "detail": "cannot sync state from self"}
    
    accepted = nonce_engine.sync_replicated_state(
        client_id=payload.client_id,
        nonce=payload.last_nonce,
        timestamp=payload.timestamp,
        hmac_signature=payload.hmac_signature
    )
    
    if not accepted:
        raise HTTPException(status_code=400, detail="Cluster state synchronization rejected due to invalid signature or stale nonce.")
        
    return {
        "status": "synchronized",
        "target_node": nonce_engine.node_id,
        "synced_client": payload.client_id
    }
