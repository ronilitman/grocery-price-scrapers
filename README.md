# grocery-price-scrapers

Nightly scrapers for Israeli supermarket price transparency data: the price,
store and promotion files each chain is required by law to publish.

It does one thing. Once a day, GitHub Actions downloads every chain's newest
full files and publishes them per chain as a `raw-<CHAIN>` artifact. There is
no database, no merging across chains and no analysis here, only the chains'
own data in a convenient shape.

Downloading and parsing are done by
[`israeli-supermarket-scarpers`](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-scarpers)
and
[`israeli-supermarket-parsers`](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers).
This repo adds what they currently lack: a scraper for Netiv Hesed's new
portal, a converter for Super-Pharm's current XML, and handling for the ways a
chain's files break a scrape (see the notes in `scripts/`).

## What a `raw-<CHAIN>` artifact contains

```
manifest.json          what is inside, and when it was scraped
outputs/*.csv          prices (PRICE_FULL_FILE) and branches (STORE_FILE)
dumps/<folder>/PromoFull*.xml
                       the chain's promotion files, unmodified
_asof_<CHAIN>.json     only when the chain had not published today's files
                       and the scrape used an earlier day's
```

Artifacts are kept for 7 days. `scripts/package_raw.py` defines the layout,
and `tests/test_package_raw.py` pins it.

## Running it

```bash
pip install -r requirements.txt
python scripts/fetch.py RAMI_LEVY            # -> dumps/, outputs/
python scripts/package_raw.py --chain RAMI_LEVY --out raw
```

On GitHub: **Actions → Scrape → Run workflow**. A few chains refuse
datacenter addresses and are routed through a Tailscale exit node. A fork has
no access to it, so those chains will fail there.

## License

MIT. The data belongs to the chains that publish it.
