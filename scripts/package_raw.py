"""Gather one chain's scrape into the raw package the workflow publishes.

This is the whole output of the repo, so its shape is a contract: whoever
downloads a ``raw-<CHAIN>`` artifact reads exactly this layout.

    raw/
      manifest.json         what is inside, and when it was scraped
      outputs/*.csv         PRICE_FULL_FILE and STORE_FILE, as fetch.py's
                            parser step wrote them
      dumps/<folder>/PromoFull*.xml
                            the chain's own promotion files, byte for byte
      _asof_<CHAIN>.json    only when the chain had not published today's
                            files and the scrape reached back a day

Promotions ship as the chain's XML rather than as CSV: the generic converter
flattens a promotion's nested items into an unreadable, enormous JSON column
(see fetch.PARSE_TYPES). PriceFull and Stores XML are not shipped, because
their CSVs carry the same data at a fraction of the size.

Everything in here is what the chain itself publishes under the price
transparency regulations - nothing is derived beyond the CSV conversion.
"""

import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csvutil import find_csvs  # noqa: E402

CONTRACT_VERSION = 1


def _promo_files(dumps_dir):
    found = []
    for root, _dirs, files in os.walk(dumps_dir):
        if os.path.basename(root) in ("status", "outputs"):
            continue
        for name in files:
            if name.lower().startswith("promofull") and name.endswith(".xml"):
                found.append(os.path.join(root, name))
    return sorted(found)


def package(chain, outputs, dumps, notes, out, now=None):
    """Build ``out`` for ``chain``. Returns the manifest dict.

    Raises SystemExit when there are no price CSVs: an empty package would
    look like a chain that sells nothing, which is worse than no package.
    """
    prices = find_csvs(outputs, "PRICE_FULL_FILE")
    stores = find_csvs(outputs, "STORE_FILE")
    if not prices:
        raise SystemExit(f"[package] {chain}: no price CSV in {outputs}/ - refusing to publish")

    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "outputs"))

    csvs = []
    for path in prices + stores:
        shutil.copy2(path, os.path.join(out, "outputs", os.path.basename(path)))
        csvs.append({"name": os.path.basename(path), "bytes": os.path.getsize(path)})

    promos = _promo_files(dumps)
    for path in promos:
        target = os.path.join(out, "dumps", os.path.relpath(path, dumps))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(path, target)

    as_of = None
    note = os.path.join(notes, f"_asof_{chain}.json")
    if os.path.exists(note):
        shutil.copy2(note, os.path.join(out, os.path.basename(note)))
        with open(note, encoding="utf-8") as handle:
            as_of = json.load(handle).get(chain)

    now = now or datetime.datetime.now(datetime.timezone.utc)
    manifest = {
        "contract": CONTRACT_VERSION,
        "chain": chain,
        "scraped_at": now.replace(microsecond=0).isoformat(),
        # The day the chain actually published these files, when that is not
        # today; null means the files are from the scrape itself.
        "published_as_of": as_of,
        "csv": csvs,
        "price_csv_count": len(prices),
        "store_csv_count": len(stores),
        "promo_xml_count": len(promos),
        "promo_xml_bytes": sum(os.path.getsize(p) for p in promos),
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)

    if not stores:
        print(f"::warning::{chain}: no store CSV - branches will be nameless downstream")
    if not promos:
        print(f"::warning::{chain}: no PromoFull files - the package carries prices only")
    print(f"[package] {chain}: {len(prices)} price CSV, {len(stores)} store CSV, "
          f"{len(promos)} PromoFull XML" + (f", published as of {as_of}" if as_of else ""))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--chain", required=True)
    parser.add_argument("--outputs", default="outputs")
    parser.add_argument("--dumps", default="dumps")
    parser.add_argument("--notes", default="notes")
    parser.add_argument("--out", default="raw")
    args = parser.parse_args()
    package(args.chain, args.outputs, args.dumps, args.notes, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
