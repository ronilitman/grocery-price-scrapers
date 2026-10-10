# grocery-price-scrapers

Public. Scrapes the Israeli supermarket chains' price transparency files once
a day and publishes each chain's raw files as a `raw-<CHAIN>` artifact. That
artifact is the **only** output.

## What does not belong here

Everything downstream of the raw files lives in a private repo. **Nothing
from that side is ever committed here** — not code, not data, and not a
description of what it does or how. Before any push, grep the tree for the
private module names (the list is kept in the private repo's CLAUDE.md) and
for credentials. When a comment here needs to mention a consumer, it says "a
consumer" and nothing more specific.

## The artifact is a contract

A private consumer downloads `raw-<CHAIN>` every night and depends on its
exact shape, as defined in `scripts/package_raw.py` and pinned by
`tests/test_package_raw.py`:

- `outputs/` — the price and store CSVs from `fetch.py`'s parser step.
- `dumps/**/PromoFull*.xml` — promotions as the chain's own XML. They are not
  converted to CSV (see `fetch.PARSE_TYPES`), so the XML is the only copy.
- `_asof_<CHAIN>.json` — present only when the scrape had to use an earlier
  day's files, so the files carry their real age.
- `manifest.json` — `contract` is 1. Bump it on any change to the layout, and
  change the consumer first.

Retention is 7 days, and the consumer relies on it: a chain that fails
tonight is served from its newest package still in retention.

## Things that will bite you

**Never pass `--limit` on a run whose artifacts will be consumed.** A limited
run publishes a partial chain that looks exactly like a complete one.

**A parser can fail silently.** The chains change their XML and the upstream
parser reports `errors: False` with zero rows — that is how Super-Pharm shipped
nothing for months (hence `scripts/superpharm.py`). Never trust the status
field; check row counts and whether a CSV was actually written.

**Seven chains cannot be scraped from a datacenter.** Super-Pharm (Reblaze,
HTTP 247), Hazi Hinam (Cloudflare 403), Victory, Mahsani Ashuk and Het Cohen
(laibcatalog never answers), Osher Ad, and Netiv Hesed (Cloudflare). They are
listed in `HOME_EGRESS` in `scrape.yml`, and their jobs leave through a
Tailscale exit node (`vars.TS_EXIT_NODE`, the owner's Raspberry Pi
running Home Assistant OS, tailnet name `homeassistant`). If
*exactly* those fail, suspect that the exit node is offline before you suspect
the chains. A headless browser does not help; only the egress does. The runners
join as `tag:scraper`, which can reach the internet through the exit node and
nothing else on the tailnet.

**Netiv Hesed is scraped by this repo, not by the library.** The library's
`NETIV_HASED` points at a host that answers 500, so the library drops the
chain. It publishes at `app.netiv-hesed.com`, and `scripts/netiv.py`
downloads from there; the library's *parser* for it is still used. Its portal
shows one day at a time, and on a late morning today holds only hourly
deltas. `netiv.py` walks back up to three days and writes the day it settled
on to `_asof_NETIV_HASED.json`.

**The chains serve a window of files, not one per branch.** `dumps.py` keeps
only each branch's newest file before anything reads them. A branch is
identified by the `<ChainID>`/`<StoreID>` inside the XML, never by the
filename, which lies at several chains.

**King Store** produces zero files, and this reproduces locally. Still open.

## Secrets

`TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` (a `tag:scraper` OAuth client),
variable `TS_EXIT_NODE`, and optionally `SUPERPHARM_PROXY_URL` for the
Super-Pharm probe. A fork's pull requests never receive them.

## Rules

- Edit in a git worktree. The owner's checkout may hold work in progress.
- No workflow run, merge or deploy without the owner's go.
