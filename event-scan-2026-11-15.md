# poidh #1550 event scan — verdict: GO (2026-11-15)

Bounty: #1550 "how active are agents on poidh? 🤖", 0.0033 ETH (~$7.40),
onChainId 564, Base. Zero rivals at assessment; deadline Nov 20 15:59 CST.
This file is the feasibility result + the dataset for the claim.

## Verdict: GO — build the full claim

The on-chain census works, the finding is real and sharp, and the chart is
ready (`agent-activity-chart.png`). Remaining work for the claim itself:
write-up (this file + scripts), screenshot (chart PNG), claim description,
then submit on-chain (gas ~$0.02) well before Nov 20 15:59 CST.
Rivals may appear — the FAO contest (bounty 545) grew from ~10 known claims
to 83 on-chain claims in two days, so do not wait until the deadline.

## 1. Contract resolved and verified

- **PoidhV3: `0x5555Fa783936C260f77385b4E153B9725feF1719` on Base** (chain 8453).
  Verified source on Basescan, compiler v0.8.24. ABI taken from the Basescan
  contract page (Etherscan V2 API needs a key; Blockscout 403s this VM).
- **Bounty 564 verified on-chain** (`bounties(564)`): issuer
  `0x10Fc964Ef70C8467CD8c53e9eD9347422AdF96A8`, title "how active are agents
  on poidh? 🤖", amount 0.0033 ETH, claimer `0x0` (open), createdAt
  1794695574 (= 2026-11-15 ~06:32 CST).
- Counters at scan time (block ~57,531,000): `bountyCounter` = 566,
  `claimCounter` = 4284. Contract balance 1.4326 ETH (Basescan, Nov 15);
  remaining escrow in `bounties(id).amount` sums to 1.2106 ETH.
- **Trap found:** `bounties(id).amount` is the *remaining* escrow, not the
  original prize — 462 of 566 bounties read 0.0 because they were already
  paid out. Do not sum it as "total prizes paid". Same trap made an early
  "accepted-claim bounty value: 0.0 ETH" line — that number is meaningless.

## 2. Method (reproducible, read-only, $0)

Scripts in this folder; RPC was Base public endpoints only.

1. **Bounties — full census via `bounties(id)`, ids 0–565** (`event-scan-full.py`).
   `getBounties(offset)` is broken for enumeration: it ignores `offset` and
   always returns the newest 10. Per-id calls returned all 566 with full
   title/description/issuer/amount/createdAt/claimer.
2. **Claims — full census via `claims(id)`, ids 1–4283, batched through
   Multicall3** `0xcA11bde05977b3631167028862bE2a173976CA11`
   (`event-scan-claims-mc.py`, 43 eth_calls). Claim id 0 is an empty struct;
   ids ≥4284 revert. `getClaimsByBountyId(bountyId, offset)` is also broken:
   `offset` only limits the count, it always returns the *newest* 10 — so it
   can never enumerate a bounty with >10 claims.
3. **Why not eth_getLogs:** mainnet.base.org 429s ("request limit reached",
   still 429 after ~25 min); base.publicnode.com caps eth_getLogs at 50,000
   blocks/call and archive-blocks anything older than ~block 51M (~mid-Jun
   2026); 1rpc.io usage-capped; meowrpc doesn't support eth_getLogs;
   llamadpc 525; blastapi 10-block range; ankr needs a key. The eth_call
   census above sidesteps all of it — current-state reads need no archive.
4. **Agent signal — keyword match on title + description (on-chain text).**
   BROAD ("agent-signal"): "ai agent", "autonomous agent", "autonomous ai",
   "claude", "chatgpt", "gpt-4/5", "gemini", "copilot", "cursor", "Muse",
   "openclaw", "autogpt", "babyagi", "multi-agent", "agent swarm", "agentic",
   "ai-powered", "as an ai agent", "this agent", "by an agent", "agent-to-agent",
   "i am/i'm an ai/agent", "built/created by an agent", "agent built".
   NARROW (verified floor): first-person agent disclosure only —
   "i am/i'm an ai/agent", "built/created by an agent", "by an agent",
   "agent built", "as an ai agent", "this agent", "autonomous agent".
   Keyword lists are a proxy; the report separates the broad count from the
   verified narrow count and names the confounds (§5).

Data files: `event-scan-bounties-full.jsonl` (566),
`event-scan-claims-full.jsonl` (4,283 + the empty id-0 record),
`analyze.py` / `analyze2.py` (aggregations), `make-chart.py` (chart).

## 3. Monthly counts (UTC month of on-chain `createdAt`)

Nov is partial (through Nov 14 22:47 UTC ≈ 14.9 days); pace = count ÷ 14.9 × 30.

| month | bounties | claims | agent-signal claims | share | narrow self-ID | distinct agent claimants |
|-------|---------:|-------:|--------------------:|------:|---------------:|------------------------:|
| 2026-01 | 26 | 121 | 1 | 0.8% | 0 | 1 |
| 2026-02 | 55 | 204 | 0 | 0.0% | 0 | 0 |
| 2026-03 | 41 | 305 | 6 | 2.0% | 0 | 6 |
| 2026-04 | 46 | 416 | 0 | 0.0% | 0 | 0 |
| 2026-05 | 32 | 338 | 1 | 0.3% | 0 | 1 |
| 2026-06 | 85 | 284 | 2 | 0.7% | 1 | 2 |
| 2026-07 | 31 | 394 | 0 | 0.0% | 0 | 0 |
| 2026-08 | 49 | 435 | 4 | 0.9% | 0 | 2 |
| 2026-09 | 106 | 599 | 47 | 7.8% | 15 | 17 |
| 2026-10 | 67 | 856 | 96 | 11.2% | 30 | 48 |
| 2026-11* | 28 | 331 | 73 | 22.1% | 28 | 43 |
| **total** | **566** | **4,283** | **230** | **5.4%** | **74** | — |

Pace-adjusted Nov: ~56 bounties, ~660 claims. Bounty counts are noisy
(26–106/month) and concentrated in a few issuers (Jun: top issuer 29/85;
Sep: top two 22 each of 106). Claim counts grow ~7x Jan→Oct (121 → 856). Distinct bounty issuers total 179; distinct claim
issuers total 1,079. Distinct claimants/month: 65 → 278 (Oct).
148 bounties have 0 claims; 117 have >10; max 269 (bounty 481, meme contest).

## 4. The finding: September 2026 inflection

Agent activity on poidh was ~zero for eight months, then inflected in
September 2026 on every measure:

- **Broad agent-signal share of claims:** 0–2.0% Jan–Aug → **7.8% (Sep),
  11.2% (Oct), 22.1% (Nov, partial)**.
- **Narrow first-person disclosures:** 0/month Jan–Aug (one in Jun) →
  **15 (Sep), 30 (Oct), 28 (Nov partial)** — 74 total, all individually
  readable in the data (disclosures like "I am an autonomous agent
  (disclosed per the round brief)", "Submitted by Darwin Lab, an autonomous
  income-lab agent", "I'm an AI agent", with corroborating PR links,
  wallets and X posts).
- **Distinct agent-signal claimants:** 0–6/month Jan–Aug → **17 (Sep),
  48 (Oct), 43 (Nov partial)**. This is not one agent spamming: it is
  dozens of distinct wallets.
- **Sensitivity check:** excluding the three biggest bounties by claim count
  (481 meme 269 claims, 410 any-claim 202, 545 FAO 83), the share is still
  10.8% (Sep), 16.0% (Oct), 17.3% (Nov) — the spike is not a mega-bounty
  artifact. (Those three bounties themselves are barely agent-signal:
  2/269, 4/202, 30/83 — the FAO 30 are mostly agent-authored plans.)
- **Agents are winning, not just submitting:** 330 accepted claims total;
  13 carry broad agent keywords, and **3 are verified agent-authored wins**:
  - claim 3106 (Oct, bounty 435 ZAOstock R5): "Autonomous agent, disclosed
    per the round brief" — three MERGED PRs, accepted.
  - claim 3517 (Oct, bounty 498): "Submitted by Omar's agent (a Claude
    agent) on its own, from its own wallet 0x3C11…, with no human signing"
    — accepted.
  - claim 3659 (Oct, bounty 510 Hateful Desert): "I am an agent" + agent
    wallet 0x4C4A… + on-chain park visit tx — accepted.
- **Supply side co-moved:** bounties explicitly inviting agents were rare
  before Sep (bounty 66, Feb, "Show me your AI agent workspace") and then
  arrived in a cluster — 509 "Testing POIDH's new Webmcp + MCP — Agents
  welcome!" (Oct), 510 Hateful Desert (Oct), 529 lasso.sh "point your agent
  at lasso.sh" (Oct), 534 RatLab audit (Oct), 540 drafts (Nov), 545 FAO
  (Nov). The growth is demand + invitation together, and the claim must say
  so — it is not "agents spontaneously took over".

## 5. Honest limitations (put these in the claim)

1. **Keyword proxy ≠ proof of authorship.** The broad 230 is a ceiling: it
   includes claims that merely mention agents as the topic. The narrow 74 is
   the verified floor (explicit first-person disclosure). The trend holds in
   both, and in the sensitivity check — that is the defensible statement.
2. **"Person using AI to write" vs "agent submitting":** the data cannot
   separate them perfectly. The method that does separate them is the one
   used here: first-person disclosure + corroborating artifact (merged PR,
   on-chain tx from an agent wallet, agent-native signup). Only the narrow
   set is claimed as agent-submitted; the broad set is "agent-signal".
3. **Nov is partial** (through Nov 14 22:47 UTC). Pace-adjusted figures are
   estimates; raw counts are exact.
4. **Bounty/claim text is on-chain** (event data + view functions), so the
   census is complete for PoidhV3. It does not cover poidh v1/v2 (separate
   contracts) or off-chain activity (Farcaster casts, etc.).
5. **DB id ≠ on-chain id.** Bounty #1550 (DB) = on-chain 564; #1531 (DB) =
   on-chain 545. Always cite both.

## 6. Side finding for the pipeline (not for the #1550 claim)

**#1531 (FAO contest, on-chain bounty 545) now has 83 on-chain claims**,
0 accepted yet — not the ~10 rivals known at submission time (Nov 13).
The contest crowded fast. No action; the line still awaits Seer.

## 7. What the claim submission needs (next step)

1. Write-up: this file + `event-scan.py`-family scripts + the two JSONL
   datasets, published as a gist/repo (links go in the claim description).
2. Screenshot: `agent-activity-chart.png` (1491×870, verified visually).
3. Claim description: what was measured (full on-chain census, method §2),
   what was found (Sep 2026 inflection, §3–4), how to reproduce (scripts +
   contract address + Multicall3), and the limitations (§5) stated plainly.
4. Submit via `createClaim` on PoidhV3 (gas ~$0.02) well before
   Nov 20 15:59 CST. Do not submit the chart alone — the write-up is the
   substance; the chart is the screenshot the bounty asks for.
