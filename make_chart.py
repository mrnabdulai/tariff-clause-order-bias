"""Stacked bar chart: correct vs wrong bills per key-clause position, one panel per model."""
import glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(here, "results_v2_*.json")))
layouts = ["start", "middle", "end", "scattered"]
fig, axes = plt.subplots(1, len(files), figsize=(4 * len(files), 3.6), sharey=True, squeeze=False)
for ax, f in zip(axes[0], files):
    rows = json.load(open(f))
    ok = [sum(r["correct"] for r in rows if r["layout"] == l) for l in layouts]
    bad = [sum(not r["correct"] and r["got"] is not None for r in rows if r["layout"] == l) for l in layouts]
    none = [sum(r["got"] is None for r in rows if r["layout"] == l) for l in layouts]
    ax.bar(layouts, ok, color="#2e7d32", label="Correct bill")
    ax.bar(layouts, bad, bottom=ok, color="#c62828", label="Wrong bill")
    ax.bar(layouts, none, bottom=[a + b for a, b in zip(ok, bad)], color="#bdbdbd", label="No answer (API error)")
    ax.set_title(rows[0]["model"].split("/")[-1].replace(":free", ""), fontsize=10)
    ax.set_xlabel("Position of key tariff clauses")
for ax in axes[0][:1]:
    ax.set_ylabel("Bills (out of 6)")
axes[0][-1].legend(loc="lower right", fontsize=8)
fig.suptitle("Do LLM electricity bills change with clause position? (PURC tariff, 52 clauses)", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(here, "order_bias_chart.png"), dpi=150)
print("saved")
