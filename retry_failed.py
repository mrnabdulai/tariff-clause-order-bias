"""Re-ask only rows where the model gave no answer (network failure), then save in place."""
import glob, json, sys, time
from order_test import exact_bill, ask
from order_test_v2 import layouts

for path in sorted(glob.glob("results_v2_*.json")):
    rows = json.load(open(path)); clauses = dict(layouts())
    for r in rows:
        if r["got"] is None:
            r["got"] = ask(r["model"], clauses[r["layout"]], r["category"], r["kwh"])
            r["correct"] = r["got"] is not None and abs(r["got"] - r["truth"]) <= 0.05
            print(r["model"], r["layout"], r["kwh"], r["got"], "OK" if r["correct"] else "WRONG", flush=True)
            time.sleep(4)
    json.dump(rows, open(path, "w"), indent=1)
    print(path, sum(r["correct"] for r in rows), "/", len(rows), "still missing:", sum(r["got"] is None for r in rows), flush=True)
