"""The raw package is this repo's only output, so its layout is a contract."""

import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import package_raw  # noqa: E402

NOW = datetime.datetime(2026, 9, 24, 3, 0, tzinfo=datetime.timezone.utc)


def write(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


@pytest.fixture
def scrape(tmp_path):
    outputs, dumps, notes = tmp_path / "outputs", tmp_path / "dumps", tmp_path / "notes"
    write(str(outputs / "price_full_file_rami_levy.csv"), "itemcode\n1\n")
    write(str(outputs / "store_file_rami_levy.csv"), "storeid\n1\n")
    write(str(outputs / "status" / "parser.json"), "{}")
    write(str(dumps / "RamiLevy" / "PromoFull7290058140886-001-202609240300.xml"), "<Root/>")
    write(str(dumps / "RamiLevy" / "PriceFull7290058140886-001-202609240300.xml"), "<Root/>")
    write(str(dumps / "status" / "PromoFull-ignored.xml"), "<Root/>")
    return tmp_path


def test_layout(scrape):
    out = scrape / "raw"
    manifest = package_raw.package("RAMI_LEVY", str(scrape / "outputs"), str(scrape / "dumps"),
                                   str(scrape / "notes"), str(out), now=NOW)

    assert sorted(os.listdir(out / "outputs")) == [
        "price_full_file_rami_levy.csv", "store_file_rami_levy.csv"]
    # PromoFull XML keeps its path under dumps/; PriceFull XML and the
    # scraper's status folder are not shipped.
    assert os.listdir(out / "dumps") == ["RamiLevy"]
    assert os.listdir(out / "dumps" / "RamiLevy") == [
        "PromoFull7290058140886-001-202609240300.xml"]

    on_disk = json.load(open(out / "manifest.json", encoding="utf-8"))
    assert on_disk == manifest
    assert manifest["contract"] == 1
    assert manifest["chain"] == "RAMI_LEVY"
    assert manifest["scraped_at"] == "2026-09-24T03:00:00+00:00"
    assert manifest["published_as_of"] is None
    assert (manifest["price_csv_count"], manifest["store_csv_count"],
            manifest["promo_xml_count"]) == (1, 1, 1)


def test_as_of_note_travels(scrape):
    note = {"NETIV_HASED": "2026-09-23T12:00:00+00:00"}
    write(str(scrape / "notes" / "_asof_NETIV_HASED.json"), json.dumps(note))
    out = scrape / "raw"
    manifest = package_raw.package("NETIV_HASED", str(scrape / "outputs"), str(scrape / "dumps"),
                                   str(scrape / "notes"), str(out), now=NOW)

    assert json.load(open(out / "_asof_NETIV_HASED.json", encoding="utf-8")) == note
    assert manifest["published_as_of"] == "2026-09-23T12:00:00+00:00"


def test_no_prices_is_refused(tmp_path):
    os.makedirs(tmp_path / "outputs")
    with pytest.raises(SystemExit):
        package_raw.package("RAMI_LEVY", str(tmp_path / "outputs"), str(tmp_path / "dumps"),
                            str(tmp_path / "notes"), str(tmp_path / "raw"), now=NOW)
    assert not os.path.exists(tmp_path / "raw")
