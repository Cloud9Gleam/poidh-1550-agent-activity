#!/usr/bin/env python3
"""poidh #1550: confound check — is the agent-signal spike topic-driven or authorship-driven?"""
import json, re
from collections import Counter, defaultdict

D = "/home/hatch/workspace/taskmarket/poidh-1550/"
bounties = {}
for line in open(D + "event-scan-bounties-full.jsonl"):
    r = json.loads(line)
    bounties[r["id"]] = r
claims = {}
for line in open(D + "event-scan-claims-full.jsonl"):
    r = json.loads(line)
    if r["id"] == 0:
        continue
    claims[r["id"]] = r

STRONG = ["ai agent", "autonomous agent", "i am an ai", "i'm an ai", "i am an agent",
          "i'm an agent", "built by an agent", "created by an agent", "agent-built",
          "agent built", "claude", "chatgpt", "gpt-4", "gpt-5", "gemini", "copilot",
          "cursor", "Muse", "openclaw", "autogpt", "babyagi", "multi-agent",
          "agent swarm", "as an ai agent", "this agent", "agentic", "ai-powered",
          "ai powered", "by an agent", "autonomous ai", "agent-to-agent"]
NARROW = ["i am an ai", "i'm an ai", "i am an agent", "i'm an agent",
          "built by an agent", "created by an agent", "by an agent", "agent built",
          "agent-built", "as an ai agent", "this agent", "autonomous agent"]

def hits(text, kws):
    t = " " + text.lower() + " "
    return [k for k in kws if k in t]

def bounty_is_agent_themed(b):
    text = (b.get("title", "") + " " + b.get("description", "")).lower()
    return bool(hits(text, STRONG))

# 1. debug accepted-ETH
acc_eth = sum(bounties[c["bountyId"]]["amount_eth"] for c in claims.values()
              if c["accepted"] and c["bountyId"] in bounties)
print("accepted-claim bounty value:", round(acc_eth, 4), "ETH")
print("accepted claims with bountyId missing from bounties dict:",
      sum(1 for c in claims.values() if c["accepted"] and c["bountyId"] not in bounties))

# 2. cross-tab: strong claim x bounty agent-themed, by month
print("\n== strong claims: on agent-themed bounty vs other bounty ==")
print(f"{'month':8} {'claims':>6} {'strong':>6} {'strong on agent-bounty':>22} {'strong on other':>15}")
for m in sorted(set(c["month"] for c in claims.values())):
    mc = [c for c in claims.values() if c["month"] == m]
    st = [c for c in mc if hits(c.get("title", "") + " " + c.get("description", ""), STRONG)]
    on_theme = [c for c in st if bounty_is_agent_themed(bounties.get(c["bountyId"], {}))]
    print(f"{m:8} {len(mc):>6} {len(st):>6} {len(on_theme):>22} {len(st)-len(on_theme):>15}")

# 3. where do Oct/Nov strong claims cluster? top bounties by strong-claim count
print("\n== top bounties by strong-claim count (all months) ==")
cnt = Counter()
for c in claims.values():
    if hits(c.get("title", "") + " " + c.get("description", ""), STRONG):
        cnt[c["bountyId"]] += 1
for bid, n in cnt.most_common(15):
    b = bounties.get(bid, {})
    print(f"  bounty {bid} ({b.get('month','?')}): {n} strong claims | {b.get('title','?')[:80]}")

# 4. narrow self-ID claims: list all with full text snippet
print("\n== NARROW self-ID claims (first-person agent disclosure) ==")
narrow = []
for c in claims.values():
    text = (c.get("title", "") + " " + c.get("description", ""))
    kws = hits(text, NARROW)
    if kws:
        narrow.append(c)
print("count:", len(narrow))
for c in sorted(narrow, key=lambda x: x["month"]):
    b = bounties.get(c["bountyId"], {})
    print(f"  claim {c['id']} {c['month']} bounty {c['bountyId']} ({b.get('title','?')[:50]}) accepted={c['accepted']}")
    print(f"    title: {c['title'][:120]}")
    print(f"    desc: {c['description'][:220].replace(chr(10),' ')}")

# 5. strong accepted claims: which won?
print("\n== STRONG accepted claims ==")
for c in sorted([c for c in claims.values() if c["accepted"] and hits(c.get("title", "") + " " + c.get("description", ""), STRONG)], key=lambda x: x["month"]):
    b = bounties.get(c["bountyId"], {})
    print(f"  claim {c['id']} {c['month']} bounty {c['bountyId']} {b.get('amount_eth')} ETH | {b.get('title','?')[:60]} | claim: {c['title'][:80]}")

# 6. claims-per-bounty max: which bounty has 269?
per_b = Counter(c["bountyId"] for c in claims.values())
top = per_b.most_common(5)
print("\n== most-claimed bounties ==")
for bid, n in top:
    b = bounties.get(bid, {})
    print(f"  bounty {bid} ({b.get('month','?')}): {n} claims | {b.get('title','?')[:80]}")
