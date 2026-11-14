#!/usr/bin/env python3
"""Chart for poidh #1550: monthly claims, agent-signal share. Data: full on-chain census."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov*"]
claims = [121, 204, 305, 416, 338, 284, 394, 435, 599, 856, 331]
strong = [1, 0, 6, 0, 1, 2, 0, 4, 47, 96, 73]
narrow = [0, 0, 0, 0, 0, 1, 0, 0, 15, 30, 28]
other = [t - s for t, s in zip(claims, strong)]
share = [100 * s / t for s, t in zip(strong, claims)]

fig, ax = plt.subplots(figsize=(10, 5.2))
x = range(len(months))
ax.bar(x, other, color="#c9d1d9", label="other claims")
ax.bar(x, strong, bottom=other, color="#2da44e", label="agent-signal claims")
for i, (t, s, n) in enumerate(zip(claims, strong, narrow)):
    ax.text(i, t + 18, str(t), ha="center", va="bottom", fontsize=8, color="#24292f")
    if s:
        ax.text(i, other[i] + s / 2, str(s), ha="center", va="center",
                fontsize=8, color="white", fontweight="bold")
ax2 = ax.twinx()
ax2.plot(x, share, color="#8250df", marker="o", ms=4, lw=2, label="agent-signal share")
ax2.yaxis.set_major_formatter(PercentFormatter())
ax2.set_ylim(0, 26)
ax2.set_ylabel("agent-signal share of claims", fontsize=9, color="#8250df")
ax2.tick_params(axis="y", labelcolor="#8250df", labelsize=8)
ax.set_xticks(list(x))
ax.set_xticklabels(months, fontsize=9)
ax.set_ylabel("claims created per month", fontsize=9)
ax.set_title("Agent activity on poidh: the September 2026 inflection\n"
             "Monthly claims on PoidhV3 (Base), full on-chain census of 4,283 claims",
             fontsize=11, fontweight="bold")
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.set_ylim(0, 980)
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.01, -0.10,
         "* Nov is partial (through Nov 14, 22:47 UTC).  Agent-signal = claim title/description contains explicit agent keywords\n"
         "(e.g. 'AI agent', 'autonomous agent', 'Claude'); verified subset: 74 claims with first-person agent disclosure.\n"
         "Source: PoidhV3 0x5555Fa783936C260f77385b4E153B9725feF1719 — bounties(id) + claims(id) via Multicall3, 2026-11-15.",
         fontsize=7.5, color="#57606a")
plt.subplots_adjust(bottom=0.26)
plt.tight_layout()
plt.savefig("/home/hatch/workspace/taskmarket/poidh-1550/agent-activity-chart.png", dpi=150, bbox_inches="tight")
plt.savefig("/home/hatch/workspace/taskmarket/poidh-1550/agent-activity-chart.svg", bbox_inches="tight")
print("wrote chart png + svg")
