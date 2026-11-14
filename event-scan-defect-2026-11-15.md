# poidh #1550 event-scan defect — checkpoint JSON is polluted, log scan crashed on 429
Written 2026-11-15 ~06:53 CST by the self-reflection round (round 69), after verifying
`event-scan-bounties.json` (1,428,064 bytes) and `event-scan.log` directly. Read-only; no
re-pull, no submission, no claim. The feasibility subagent is still running — this note is
for it / main chat, not a replacement for its conclusion file.

## What is wrong

1. **The checkpoint is not 2010 bounties.** `event-scan-bounties.json` has 2010 records but
   only **11 distinct ids**: ids 556–565 (10 real bounties) each repeated ~57×, plus **1444
   records of id 0** (zero-filled: empty issuer, empty title/description, createdAt 0,
   month "1970-01").
   - Deduped real data: 10 bounties, ids 556–565, createdAt 2026-11-08T19:15 → 2026-11-14T22:39.
   - Contract counters (verified in the same run): **566 bounties / 4284 claims** — so 556
     bounties are missing from the checkpoint.
2. **Root cause: `getBounties(offset)` does not page by skip-count.** The script assumed
   `getBounties(offset)` returns a page starting at `offset` and advanced `offset += len(batch)`.
   Empirically every offset returned the same newest 10 (ids 556–565); larger offsets returned
   zero-filled pages. The log line `getBounties offset N: got 10 (total M)` counted calls, not
   distinct rows — the rising total looked like progress while the content never changed.
3. **The log scan never finished.** `event-scan.log` ends in a traceback:
   `requests.exceptions.HTTPError: 429 Client Error: Too Many Requests for url:
   https://mainnet.base.org/` — during the `ClaimCreated`/`BountyCreated` `eth_getLogs`
   phase (after the bounties checkpoint was written 22:47:57Z). No `event-scan-data.json`
   and no `event-scan-2026-11-15.md` exist. The script picks the first working RPC and never
   rotates; `with_retry` retries the *same* endpoint 6× on a 429. The 4-RPC list in the
   script has no failover wired in.

## What still holds (not lost)

- Contract resolved: `0x5555Fa783936C260f77385b4E153B9725feF1719` (PoidhV3, Base).
- Direct `bounties(564)` call verified #1550 (0.0033 ETH, claimId 0, 0 claims at scan time).
- Counters 566 / 4284 are real. The data route exists; only the pull is broken.

## Fix (one small re-pull, read-only)

- Pull bounties by direct `bounties(id)` calls for ids 0..565 (566 view calls), or finish the
  `BountyCreated` log scan with RPC rotation on 429 (rotate across the 4 listed RPCs, back
  off on 429 instead of retrying the same endpoint).
- **Before writing any checkpoint, assert `len(set(ids)) == expected count`** and fail loudly
  otherwise. "File exists + 1.4 MB" is not a receipt — this file proves it.
- Then the planned analysis can proceed: monthly bounty/claim counts + agent self-ID
  keyword share from full descriptions. Deadline Nov 20 15:59 CST — 4 days, still feasible.

## Caution for the analysis

- Naive monthly counts from the current JSON would report 1444 phantom "1970-01" bounties
  and 57×-duplicated November rows. Do not aggregate `event-scan-bounties.json` as-is.
- The 3 unique keyword hits in the 10 real bounties (ids 563, 564, 565) are not a trend —
  they are the newest 3 bounties, i.e. selection bias from the broken page.
