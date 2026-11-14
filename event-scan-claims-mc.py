#!/usr/bin/env python3
"""
poidh #1550: full claims census via Multicall3 batching (43 eth_calls).
claims(id) for ids 1..4283 (id 0 is empty; 4284+ reverts).
Read-only. Writes event-scan-claims-full.jsonl (one JSON per claim).
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

from eth_abi import decode as abi_decode, encode as abi_encode
from web3 import Web3

POIDH = "0x5555Fa783936C260f77385b4E153B9725feF1719"
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
OUT = Path(__file__).parent / "event-scan-claims-full.jsonl"
BATCH = 100

RPCS = ["https://base.publicnode.com", "https://mainnet.base.org"]
CLAIMS_SEL = Web3.keccak(text="claims(uint256)")[:4]
AGG_SEL = Web3.keccak(text="aggregate((address,bytes)[])")[:4]
CLAIM_TYPES = ["uint256", "address", "uint256", "address", "string", "string", "uint256", "bool"]

def month(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")

def main():
    w3 = None
    for rpc in RPCS:
        try:
            t = Web3(Web3.HTTPProvider(rpc, request_kwargs={
                "timeout": 60,
                "headers": {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                            "Content-Type": "application/json"}}))
            if t.is_connected():
                w3 = t
                print("RPC:", rpc, flush=True)
                break
        except Exception as e:
            print("RPC fail", rpc, e, flush=True)
    assert w3 is not None

    # sanity: does Multicall3 have code?
    code = w3.eth.get_code(Web3.to_checksum_address(MULTICALL3))
    print("multicall code bytes:", len(code), flush=True)
    assert len(code) > 0

    total = 4283  # ids 1..4283
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    print(f"claims already have: {len(done)}", flush=True)

    def aggregate(ids):
        calls = [(Web3.to_checksum_address(POIDH), CLAIMS_SEL + abi_encode(["uint256"], [i])) for i in ids]
        data = AGG_SEL + abi_encode(
            ["(address,bytes)[]"],
            [[(Web3.to_checksum_address(t), d) for t, d in calls]])
        for attempt in range(6):
            try:
                raw = w3.eth.call({"to": Web3.to_checksum_address(MULTICALL3), "data": data})
                _, rets = abi_decode(["uint256", "bytes[]"], raw)
                return rets
            except Exception as e:
                wait = min(60, 3 * (2 ** attempt))
                print(f"  aggregate fail attempt {attempt+1} ({str(e)[:120]}), wait {wait}s", flush=True)
                time.sleep(wait)
        raise RuntimeError("aggregate failed")

    n_written = 0
    with OUT.open("a") as f:
        for start in range(1, total + 1, BATCH):
            ids = [i for i in range(start, min(start + BATCH, total + 1)) if i not in done]
            if not ids:
                continue
            rets = aggregate(ids)
            for cid, ret in zip(ids, rets):
                (c_id, issuer, bounty_id, bounty_issuer, title, desc, created_at, accepted) = \
                    abi_decode(CLAIM_TYPES, ret)
                assert c_id == cid, f"id mismatch {c_id} != {cid}"
                f.write(json.dumps({
                    "id": c_id, "issuer": issuer, "bountyId": bounty_id,
                    "title": title, "description": desc,
                    "createdAt": created_at, "month": month(created_at),
                    "accepted": accepted,
                }) + "\n")
                n_written += 1
            f.flush()
            print(f"  claims {start}..{min(start+BATCH-1, total)} ({n_written} written)", flush=True)
            time.sleep(1.0)
    print(f"DONE: {n_written} claims written this run", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
