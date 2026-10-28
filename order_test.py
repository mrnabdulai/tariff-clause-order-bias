"""Clause-order test: does shuffling tariff clauses change an LLM's bill?

Tariff: PURC Fourth Schedule end-user tariffs effective 1 July 2026 (unchanged for Q4 2026),
https://purc.com.gh/attachment/346541-20260729120703.pdf. Levies and taxes are left out;
the clauses below are the whole rulebook the model sees, so the exact calculator is ground truth.

Run: python3 order_test.py [model ...]   (needs OPENROUTER_API_KEY)
"""
import json, os, random, re, sys, time, urllib.request

CLAUSES = [
    "C1. Residential lifeline: a residential customer whose consumption for the month is 30 kWh or less pays 89.9315 GHp/kWh on all units.",
    "C2. Lifeline is exclusive: once a residential customer uses more than 30 kWh in the month, the lifeline rate does not apply to any units.",
    "C3. Residential lifeline service charge: 213.0000 GHp per month, charged only to lifeline customers.",
    "C4. Residential band 1: the first 300 kWh of a non-lifeline residential customer are charged at 203.7509 GHp/kWh.",
    "C5. Residential band 2: residential units above 300 kWh are charged at 269.2235 GHp/kWh. Bands are incremental: only the units above 300 use this rate.",
    "C6. Service charge for other residential consumers: 1073.0886 GHp per month.",
    "C7. Non-residential band 1: the first 300 kWh are charged at 183.9549 GHp/kWh.",
    "C8. Non-residential band 2: non-residential units above 300 kWh are charged at 224.0395 GHp/kWh, incrementally.",
    "C9. Non-residential service charge: 1242.8245 GHp per month.",
    "C10. SLT-LV customers pay an energy charge of 240.2104 GHp/kWh and a service charge of 50000.0000 GHp per month.",
    "C11. SLT-MV customers pay an energy charge of 208.6329 GHp/kWh and a service charge of 50000.0000 GHp per month.",
    "C12. 100 GHp = 1 Ghana cedi (GH₵). Bills are stated in GH₵ rounded to two decimal places.",
]

CASES = [("residential", 25), ("residential", 30), ("residential", 31),
         ("residential", 300), ("residential", 450), ("non-residential", 900)]


def exact_bill(category, kwh):
    """Ground truth in GH₵ from the clauses above."""
    if category == "residential":
        if kwh <= 30:
            ghp = kwh * 89.9315 + 213.0
        else:
            ghp = min(kwh, 300) * 203.7509 + max(kwh - 300, 0) * 269.2235 + 1073.0886
    else:
        ghp = min(kwh, 300) * 183.9549 + max(kwh - 300, 0) * 224.0395 + 1242.8245
    return round(ghp / 100, 2)


def orderings(seed_count=4):
    yield "original", CLAUSES
    yield "reversed", CLAUSES[::-1]
    for s in range(seed_count):
        c = CLAUSES[:]
        random.Random(s).shuffle(c)
        yield f"shuffle{s}", c


def ask(model, clauses, category, kwh):
    prompt = ("You calculate electricity bills using only these tariff clauses:\n\n"
              + "\n".join(clauses)
              + f"\n\nA {category} customer used {kwh} kWh this month. Work it out, then end with a final line "
                "exactly like: TOTAL: <amount in GH₵ to two decimals>")
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            out = json.load(urllib.request.urlopen(req, timeout=180))
            text = out["choices"][0]["message"]["content"] or ""
            m = re.findall(r"TOTAL:\s*(?:GH₵|GHS|GH¢)?\s*([\d,]+\.?\d*)", text)
            return float(m[-1].replace(",", "")) if m else None
        except Exception as e:  # ponytail: plain retry with backoff; free models rate-limit
            print(f"  retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(15 * (attempt + 1))
    return None


def main(models):
    results = []
    for model in models:
        for name, clauses in orderings():
            for category, kwh in CASES:
                got = ask(model, clauses, category, kwh)
                truth = exact_bill(category, kwh)
                ok = got is not None and abs(got - truth) <= 0.05
                results.append({"model": model, "order": name, "category": category, "kwh": kwh,
                                "truth": truth, "got": got, "correct": ok})
                print(f"{model} {name:9} {category:15} {kwh:4} truth={truth:8.2f} got={got} {'OK' if ok else 'WRONG'}")
                time.sleep(4)
    path = os.path.join(os.path.dirname(__file__), os.environ.get("OUT", "results.json"))
    json.dump(results, open(path, "w"), indent=1)
    for model in models:
        rows = [r for r in results if r["model"] == model]
        print(f"\n{model}: {sum(r['correct'] for r in rows)}/{len(rows)} correct")
        for category, kwh in CASES:
            answers = {r["got"] for r in rows if r["kwh"] == kwh and r["category"] == category}
            if len(answers) > 1:
                print(f"  {category} {kwh} kWh: {len(answers)} different bills across orderings: {sorted(map(str, answers))}")


if __name__ == "__main__":
    # self-check of the exact calculator
    assert exact_bill("residential", 25) == 24.61
    assert exact_bill("residential", 31) == round((31 * 203.7509 + 1073.0886) / 100, 2)
    assert exact_bill("residential", 450) == round((300 * 203.7509 + 150 * 269.2235 + 1073.0886) / 100, 2)
    main(sys.argv[1:] or ["google/gemma-4-31b-it:free"])
