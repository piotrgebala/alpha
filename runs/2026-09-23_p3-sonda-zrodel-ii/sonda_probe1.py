import re, sys, json, time, io, zipfile
import urllib.request as U
def get(url, timeout=30):
    req = U.Request(url, headers={"User-Agent": "clas5-probe/1.0"})
    with U.urlopen(req, timeout=timeout) as r:
        return r.read()
def s3list(prefix, marker=None, max_keys=5):
    base = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=" + prefix + f"&max-keys={max_keys}"
    if marker: base += "&marker=" + marker
    xml = get(base).decode()
    keys = re.findall(r"<Key>([^<]+)</Key>", xml)
    prefixes = re.findall(r"<Prefix>([^<]+)</Prefix>", xml)
    trunc = "<IsTruncated>true" in xml
    return keys, prefixes, trunc
print("== 1. Binance archive: metrics (OI, L/S ratios) earliest daily file for BTCUSDT ==")
try:
    keys, _, _ = s3list("data/futures/um/daily/metrics/BTCUSDT/", max_keys=3)
    print("earliest keys:", keys[:3])
    # last key: use marker far in future
    keys2, _, _ = s3list("data/futures/um/daily/metrics/BTCUSDT/", marker="data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2026-09-1", max_keys=3)
    print("around latest:", keys2[:3])
except Exception as e: print("ERR", e)
print("== 2. Binance archive: metrics sample content (first file) ==")
try:
    z = get("https://data.binance.vision/" + keys[0])
    zf = zipfile.ZipFile(io.BytesIO(z)); name = zf.namelist()[0]
    txt = zf.read(name).decode().splitlines()
    print(name, "rows:", len(txt)); print("\n".join(txt[:3]))
except Exception as e: print("ERR", e)
print("== 3. COIN-M funding (cm) BTCUSD_PERP earliest monthly ==")
try:
    keys, _, _ = s3list("data/futures/cm/monthly/fundingRate/BTCUSD_PERP/", max_keys=3)
    print(keys[:3])
except Exception as e: print("ERR", e)
print("== 4. Dated (quarterly) contracts um: symbols BTCUSDT_* ==")
try:
    _, prefixes, trunc = s3list("data/futures/um/monthly/klines/BTCUSDT_", max_keys=50)
    print(prefixes, "trunc", trunc)
    _, prefixes_cm, _ = s3list("data/futures/cm/monthly/klines/BTCUSD_", max_keys=50)
    print("cm:", prefixes_cm)
except Exception as e: print("ERR", e)
print("== 5. Deribit DVOL history earliest ==")
try:
    j = json.loads(get("https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&resolution=1D&start_timestamp=1500000000000&end_timestamp=1620000000000"))
    d = j["result"]["data"]; print("n", len(d), "first", d[0] if d else None, "last", d[-1] if d else None)
except Exception as e: print("ERR", e)
print("== 6. CoinMetrics community: btc metrics catalog (subset) ==")
try:
    j = json.loads(get("https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics?assets=btc&page_size=1"))
    mets = j["data"][0]["metrics"]; print("n metrics for btc:", len(mets))
    want = ["AdrActCnt","TxCnt","TxTfrValAdjUSD","CapMVRVCur","HashRate","SplyCur","FeeTotUSD","IssContNtv","NVTAdj","SplyAct1yr","FlowInExUSD","AdrBalCnt"]
    for m in mets:
        if m["metric"] in want:
            f = [x for x in m["frequencies"] if x["frequency"]=="1d"]
            print(m["metric"], f[0]["min_time"][:10] if f else None, f[0]["max_time"][:10] if f else None)
except Exception as e: print("ERR", e)
print("== 7. Fear & Greed earliest ==")
try:
    j = json.loads(get("https://api.alternative.me/fng/?limit=0&format=json"))
    d = j["data"]; print("n", len(d), "oldest", time.strftime("%Y-%m-%d", time.gmtime(int(d[-1]["timestamp"]))), "newest", time.strftime("%Y-%m-%d", time.gmtime(int(d[0]["timestamp"]))))
except Exception as e: print("ERR", e)
print("== 8. FRED DTB3 (3M T-bill) ==")
try:
    txt = get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3&cosd=2020-12-01").decode().splitlines()
    print("rows", len(txt), txt[0], txt[1], txt[-1])
except Exception as e: print("ERR", e)
print("== 9. Coinbase spot candles BTC-USD earliest (2021-01-01, 1d) ==")
try:
    j = json.loads(get("https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=2021-01-01T00:00:00Z&end=2021-01-05T00:00:00Z"))
    print("n", len(j), j[-1] if j else None)
except Exception as e: print("ERR", e)
print("== 10. Binance archive: premiumIndexKlines / indexPriceKlines / markPriceKlines earliest BTCUSDT ==")
for ds in ["premiumIndexKlines","indexPriceKlines","markPriceKlines"]:
    try:
        _, pref, _ = s3list(f"data/futures/um/monthly/{ds}/BTCUSDT/", max_keys=50)
        keys, _, _ = s3list(f"data/futures/um/monthly/{ds}/BTCUSDT/1d/", max_keys=2)
        print(ds, pref[:3], keys[:2])
    except Exception as e: print(ds, "ERR", e)
print("== 11. Binance spot archive BTCUSDT 1d earliest ==")
try:
    keys, _, _ = s3list("data/spot/monthly/klines/BTCUSDT/1d/", max_keys=2); print(keys[:2])
except Exception as e: print("ERR", e)
print("== 12. Bybit funding history public (BTCUSDT linear) earliest? ==")
try:
    j = json.loads(get("https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&startTime=1600000000000&endTime=1610000000000&limit=5"))
    print(j.get("retMsg"), len(j.get("result",{}).get("list",[])), (j.get("result",{}).get("list") or [None])[-1])
except Exception as e: print("ERR", e)
print("== 13. OKX funding history public ==")
try:
    j = json.loads(get("https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=3&before=1600000000000"))
    print(j.get("msg"), len(j.get("data",[])), (j.get("data") or [None])[-1])
except Exception as e: print("ERR", e)
print("== 14. blockchain.com charts (hash-rate, n-unique-addresses) ==")
try:
    j = json.loads(get("https://api.blockchain.info/charts/n-unique-addresses?timespan=all&format=json&sampled=false"))
    v = j["values"]; print("n", len(v), "first", time.strftime("%Y-%m-%d", time.gmtime(v[0]["x"])), "last", time.strftime("%Y-%m-%d", time.gmtime(v[-1]["x"])))
except Exception as e: print("ERR", e)
print("== 15. Binance archive: liquidationSnapshot? bookDepth earliest ==")
for ds in ["liquidationSnapshot","bookDepth","bookTicker"]:
    try:
        keys, pref, _ = s3list(f"data/futures/um/daily/{ds}/BTCUSDT/", max_keys=2); print(ds, keys[:2], pref[:2])
    except Exception as e: print(ds, "ERR", e)
