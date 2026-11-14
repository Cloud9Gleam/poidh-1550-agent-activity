#!/usr/bin/env python3
"""
poidh #1550: full on-chain enumeration via current-state eth_calls.
No eth_getLogs (archive-blocked / rate-limited). Reads:
  - bounties(id) for ids 0..565 (title, description, issuer, amount, createdAt, claimer)
  - getClaimsByBountyId(id, offset) paginated (claim title/description/issuer/createdAt/accepted)
Resumable via JSONL checkpoints. Rotates RPC on 429/403.
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

from web3 import Web3

CONTRACT = "0x5555Fa783936C260f77385b4E153B9725feF1719"
D = Path(__file__).parent
B_OUT = D / "event-scan-bounties-full.jsonl"
C_OUT = D / "event-scan-claims-full.jsonl"

RPCS = ["https://base.publicnode.com", "https://mainnet.base.org",
        "https://base.drpc.org"]

BOUNTY_FN = {
    "inputs": [{"name": "", "type": "uint256"}], "name": "bounties",
    "outputs": [
        {"name": "id", "type": "uint256"}, {"name": "issuer", "type": "address"},
        {"name": "name", "type": "string"}, {"name": "description", "type": "string"},
        {"name": "amount", "type": "uint256"}, {"name": "claimer", "type": "address"},
        {"name": "createdAt", "type": "uint256"}, {"name": "claimId", "type": "uint256"},
    ], "stateMutability": "view", "type": "function",
}
CLAIM_TUPLE = [
    {"name": "id", "type": "uint256"}, {"name": "issuer", "type": "address"},
    {"name": "bountyId", "type": "uint256"}, {"name": "bountyIssuer", "type": "address"},
    {"name": "name", "type": "string"}, {"name": "description", "type": "string"},
    {"name": "createdAt", "type": "uint256"}, {"name": "accepted", "type": "bool"},
]
GET_CLAIMS = {
    "inputs": [{"name": "bountyId", "type": "uint256"}, {"name": "offset", "type": "uint256"}],
    "name": "getClaimsByBountyId",
    "outputs": [{"components": CLAIM_TUPLE, "name": "", "type": "tuple[]"}],
    "stateMutability": "view", "type": "function",
}
COUNTER = lambda n: {"inputs": [], "name": n, "outputs": [{"type": "uint256"}],
                     "stateMutability": "view", "type": "function"}

def month(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")

class Rotator:
    def __init__(self):
        self.i = 0
        self.w3 = None
        self.contract = None
        self._connect()
    def _connect(self):
        rpc = RPCS[self.i % len(RPCS)]
        self.w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={
            "timeout": 30,
            "headers": {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                        "Content-Type": "application/json"}}))
        if not self.w3.is_connected():
            raise RuntimeError(f"cannot connect {rpc}")
        print("RPC:", rpc, flush=True)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT),
            abi=[BOUNTY_FN, GET_CLAIMS, COUNTER("bountyCounter"), COUNTER("claimCounter")])
    def rotate(self):
        self.i += 1
        print("rotating RPC...", flush=True)
        time.sleep(5)
        self._connect()
    def call(self, fn, *args):
        for attempt in range(8):
            try:
                return fn(*args).call()
            except Exception as e:
                msg = str(e)[:160]
                print(f"  call fail attempt {attempt+1}: {msg}", flush=True)
                if "429" in msg or "403" in msg or "limit" in msg.lower():
                    self.rotate()
                time.sleep(min(60, 2 * (2 ** attempt)))
        raise RuntimeError(f"call failed after retries: {fn}")

def load_done(path, key):
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                done.add(json.loads(line)[key])
            except Exception:
                pass
    return done

def main():
    r = Rotator()
    n_b = r.call(r.contract.functions.bountyCounter)
    n_c = r.call(r.contract.functions.claimCounter)
    print(f"counters: bounties={n_b} claims={n_c}", flush=True)

    done_b = load_done(B_OUT, "id")
    print(f"bounties already have: {len(done_b)}", flush=True)
    with B_OUT.open("a") as f:
        for bid in range(n_b):
            if bid in done_b:
                continue
            b = r.call(r.contract.functions.bounties, bid)
            f.write(json.dumps({
                "id": b[0], "issuer": b[1], "title": b[2], "description": b[3],
                "amount_eth": float(r.w3.from_wei(b[4], "ether")), "claimer": b[5],
                "createdAt": b[6], "month": month(b[6]), "claimId": b[7],
            }) + "\n")
            f.flush()
            if bid % 50 == 0:
                print(f"  bounty {bid}/{n_b}", flush=True)
            time.sleep(0.45)

    done_c = load_done(C_OUT, "id")
    print(f"claims already have: {len(done_c)}", flush=True)
    with C_OUT.open("a") as f:
        for bid in range(n_b):
            offset = 0
            while True:
                batch = r.call(r.contract.functions.getClaimsByBountyId, bid, offset)
                if not batch:
                    break
                for cl in batch:
                    if cl[0] in done_c:
                        continue
                    f.write(json.dumps({
                        "id": cl[0], "issuer": cl[1], "bountyId": cl[2],
                        "title": cl[4], "description": cl[5],
                        "createdAt": cl[6], "month": month(cl[6]),
                        "accepted": cl[7],
                    }) + "\n")
                    done_c.add(cl[0])
                f.flush()
                offset += len(batch)
                if len(batch) < 10:
                    break
                if offset > 200:
                    print(f"  SAFETY STOP claims bounty {bid} offset {offset}", flush=True)
                    break
                time.sleep(0.2)
            if bid % 100 == 0:
                print(f"  claims bounty {bid}/{n_b} (total claims so far {len(done_c)})", flush=True)
            time.sleep(0.3)
    print(f"DONE: {len(load_done(B_OUT,'id'))} bounties, {len(load_done(C_OUT,'id'))} claims", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
