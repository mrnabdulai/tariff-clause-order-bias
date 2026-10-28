"""Clause-order test v2: long tariff, key clauses moved to start / middle / end / scattered.

Same 12 key clauses and exact calculator as v1. Filler clauses come from the same PURC
publication (16 June 2026: electricity wholesale, natural gas, water and net metering),
so the model must find the electricity end-user rules among look-alike rules.

Run: python3 order_test_v2.py <model>   (needs OPENROUTER_API_KEY; writes results_v2_<model>.json)
"""
import json, os, random, sys, time
from order_test import CLAUSES, CASES, exact_bill, ask

FILLER = [
    "F. The Bulk Generation Charge is the weighted average rate at which distribution companies procure electricity from generation sources.",
    "F. VRA Bulk Generation Charge: 70.0726 GHp/kWh.",
    "F. Composite Bulk Generation Charge (VRA and IPPs): 118.2147 GHp/kWh.",
    "F. Transmission Service Charge TSC 1, for GRIDCo to recover the cost of its transmission network operations: 16.0274 GHp/kWh.",
    "F. Transmission Service Charge TSC 2, for GRIDCo to recover transmission losses: 4.8408 GHp/kWh.",
    "F. A distribution company or bulk customer that pays the full cost of electricity to the generator pays TSC 1 only to GRIDCo.",
    "F. Distribution Service Charge DSC 1, for distribution companies to recover network operating costs: 30.5595 GHp/kWh.",
    "F. Distribution Service Charge DSC 2, for distribution companies to recover distribution losses: 34.0460 GHp/kWh.",
    "F. Distribution Wheeling Charge (DWC), payable by embedded bulk customers for use of the distribution network: 64.6055 GHp/kWh.",
    "F. A bulk customer embedded in the distribution network that buys electricity through a distribution company pays the applicable SLT rate.",
    "F. SLT-MV2 customers pay an energy charge of 136.6512 GHp/kWh and a service charge of 50000.0000 GHp per month.",
    "F. SLT-HV customers pay an energy charge of 188.4762 GHp/kWh and a service charge of 50000.0000 GHp per month.",
    "F. Commercial EV charging point operators pay an energy charge of 208.6329 GHp/kWh and a service charge of 50000.0000 GHp per month.",
    "F. Electricity tariffs remain in force until reviewed by the Commission and are adjusted by the Automatic Adjustment (Indexation) Formula.",
    "F. Rates published in Gazette No. 134 of 14 April 2026 are revoked and replaced.",
    "F. Weighted Average Gas Commodity Charge (WAGCC): 74.1799 GHS/MMBtu.",
    "F. Weighted Average Gas Gathering Charge (WAGGC): 0.6154 GHS/MMBtu.",
    "F. Weighted Average Gas Processing Charge (WAGPC): 0.0998 GHS/MMBtu.",
    "F. Gas transmission charge WAGTSC 1, for GNGC to recover its gas transmission network costs: 9.0513 GHS/MMBtu.",
    "F. Gas transmission charge WAGTSC 2, for WAGP backhaul transmission from Takoradi to Tema: 4.3822 GHS/MMBtu.",
    "F. Weighted Average Gas Service Cost (WAGSC), recovered by GNPC: 1.1257 GHS/MMBtu.",
    "F. Weighted Average Cost of Gas (WACOG), used to compute each gas-fired plant's fuel recovery charge: 89.4542 GHS/MMBtu.",
    "F. Natural gas tariffs are denominated in Ghana Cedis (GHS).",
    "F. Water, residential: the first 0-5 cubic metres (exclusive band) are charged at 598.5381 GHp per 1000 litres.",
    "F. Water, residential: consumption above 5 cubic metres is charged at 1058.9413 GHp per 1000 litres.",
    "F. Water, residential service charge: 1000.0000 GHp per month.",
    "F. Water, non-residential: 1791.5225 GHp per 1000 litres, with a service charge of 2000.0000 GHp per month.",
    "F. Water, commercial: 3205.1425 GHp per 1000 litres, with a service charge of 2000.0000 GHp per month.",
    "F. Water, industrial: 3205.1425 GHp per 1000 litres, with a service charge of 25000.0000 GHp per month.",
    "F. Water, public institutions and government departments: 1538.4684 GHp per 1000 litres, with a service charge of 2000.0000 GHp per month.",
    "F. Water, public stand pipes: 717.0618 GHp per 1000 litres, with a service charge of 2000.0000 GHp per month.",
    "F. Water, bottled water and drinks producers: 3205.1425 GHp per 1000 litres, with a service charge of 25000.0000 GHp per month.",
    "F. Water, sachet water producers: 2820.5254 GHp per 1000 litres, with a service charge of 10000.0000 GHp per month.",
    "F. Water, bulk supply: 1016.2738 GHp per 1000 litres, with a service charge of 5000.0000 GHp per month.",
    "F. Water, ports and harbours: 4192.3264 GHp per 1000 litres, with a service charge of 50000.0000 GHp per month.",
    "F. Water tariffs are denominated in Ghana Pesewas (GHp) and adjusted by the Automatic Adjustment (Indexation) Formula.",
    "F. Net metering: where electricity imported from the distribution company equals electricity exported, the customer-generator pays the Import Tariff on energy imported.",
    "F. Net metering: where imports exceed exports, the customer-generator pays the Import Tariff on energy imported and the Export Tariff on net energy imported.",
    "F. Net metering tariffs apply to customer-generators under the Renewable Energy Act, 2011 (Act 832) as amended by Act 1045.",
    "F. A Special Load Tariff (SLT) applies to customers supplied at low, medium or high voltage.",
]


def layouts(seed=0):
    """Key clauses placed at start, middle, end, and scattered among the filler."""
    f = FILLER[:]
    mid = len(f) // 2
    yield "start", CLAUSES + f
    yield "middle", f[:mid] + CLAUSES + f[mid:]
    yield "end", f + CLAUSES
    mixed = f + CLAUSES
    random.Random(seed).shuffle(mixed)
    yield "scattered", mixed


def main(model):
    results = []
    for name, clauses in layouts():
        for category, kwh in CASES:
            got = ask(model, clauses, category, kwh)
            truth = exact_bill(category, kwh)
            ok = got is not None and abs(got - truth) <= 0.05
            results.append({"model": model, "layout": name, "category": category, "kwh": kwh,
                            "truth": truth, "got": got, "correct": ok})
            print(f"{model} {name:9} {category:15} {kwh:4} truth={truth:8.2f} got={got} {'OK' if ok else 'WRONG'}", flush=True)
            time.sleep(4)
    slug = model.replace("/", "_").replace(":", "_")
    json.dump(results, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"results_v2_{slug}.json"), "w"), indent=1)
    print(f"{model}: {sum(r['correct'] for r in results)}/{len(results)} correct", flush=True)


if __name__ == "__main__":
    assert len(CLAUSES) + len(FILLER) == 52
    main(sys.argv[1])
