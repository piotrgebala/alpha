import re, json, time, io, zipfile, datetime as dt
import urllib.request as U
def get(url, timeout=40):
    req = U.Request(url, headers={"User-Agent": "clas5-probe/1.0"})
    with U.urlopen(req, timeout=timeout) as r:
        return r.read()
def s3all(prefix):
    keys=[]; marker=None
    while True:
        url = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=" + prefix + "&max-keys=1000"
        if marker: url += "&marker=" + marker
        xml = get(url).decode()
        k = re.findall(r"<Key>([^<]+)</Key>", xml); keys += k
        if "<IsTruncated>true" not in xml or not k: break
        marker = k[-1]
    return [x for x in keys if x.endswith(".zip")]
print("== A. metrics BTCUSDT: all daily files, gaps ==")
keys = s3all("data/futures/um/daily/metrics/BTCUSDT/")
dates = sorted(dt.date.fromisoformat(re.search(r"(\d{4}-\d{2}-\d{2})", k).group(1)) for k in keys)
print("files", len(keys), "first", dates[0], "last", dates[-1], "expected days", (dates[-1]-dates[0]).days+1)
missing = [d for d in (dates[0]+dt.timedelta(i) for i in range((dates[-1]-dates[0]).days+1)) if d not in set(dates)]
print("missing days", len(missing), missing[:15], "..." if len(missing)>15 else "")
print("== B. metrics earliest for ETH/SOL/BNB ==")
for s in ["ETHUSDT","SOLUSDT","BNBUSDT"]:
    try:
        xml = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/daily/metrics/"+s+"/&max-keys=2").decode()
        print(s, re.findall(r"<Key>([^<]+\.zip)</Key>", xml)[:1])
    except Exception as e: print(s, "ERR", e)
print("== C. metrics sample: duplicates and cadence in one file (2023-06-15) ==")
z = get("https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2023-06-15.zip")
zf = zipfile.ZipFile(io.BytesIO(z)); txt = zf.read(zf.namelist()[0]).decode().splitlines()
rows = [l.split(",") for l in txt[1:]]
ts = [r[0] for r in rows]; print("rows", len(rows), "unique ts", len(set(ts)), "first", ts[0], "last", ts[-1]); print(txt[1]); print(txt[-1])
print("== D. liquidationSnapshot BTCUSDT listing ==")
xml = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/daily/liquidationSnapshot/BTCUSDT/&max-keys=3").decode()
print(re.findall(r"<Key>([^<]+)</Key>", xml)[:3])
print("== E. COIN-M REST funding BTCUSD_PERP from 2020-08 ==")
try:
    j = json.loads(get("https://dapi.binance.com/dapi/v1/fundingRate?symbol=BTCUSD_PERP&startTime=1596240000000&limit=5"))
    print(len(j), j[0] if j else None)
except Exception as e: print("ERR", e)
print("== F. OKX funding history depth (after=2021-01-10) ==")
try:
    j = json.loads(get("https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=3&after=1610236800000"))
    d = j.get("data", []); print(j.get("msg"), len(d), [(x["fundingTime"], x["fundingRate"]) for x in d])
except Exception as e: print("ERR", e)
print("== G. Deribit DVOL ETH earliest; pagination size ==")
j = json.loads(get("https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=ETH&resolution=1D&start_timestamp=1500000000000&end_timestamp=1700000000000"))
d = j["result"]["data"]; print("ETH n", len(d), "first", dt.datetime.utcfromtimestamp(d[0][0]/1000).date(), "last", dt.datetime.utcfromtimestamp(d[-1][0]/1000).date(), "continuation", j["result"].get("continuation"))
print("== H. CoinMetrics community: all btc daily metrics ==")
j = json.loads(get("https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics?assets=btc&page_size=1"))
for m in j["data"][0]["metrics"]:
    f = [x for x in m["frequencies"] if x["frequency"]=="1d"]
    print(" ", m["metric"], f[0]["min_time"][:10] if f else "-", f[0]["max_time"][:10] if f else "-")
print("== I. dated contracts um list (all) ==")
xml = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/klines/BTCUSDT_&max-keys=100").decode()
pref = re.findall(r"<Prefix>data/futures/um/monthly/klines/(BTCUSDT_\d+)/</Prefix>", xml); print(len(pref), pref)
xml = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/klines/BTCUSDT_220325/&max-keys=100").decode()
print("intervals:", re.findall(r"<Prefix>data/futures/um/monthly/klines/BTCUSDT_220325/([^/]+)/</Prefix>", xml))
xml = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/monthly/klines/BTCUSDT_220325/8h/&max-keys=100").decode()
print("8h files:", re.findall(r"<Key>([^<]+\.zip)</Key>", xml))
print("== J. FRED other series quick ==")
for sid in ["DGS3MO","DTWEXBGS","SP500","SOFR"]:
    try:
        t = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=2020-12-01").decode().splitlines(); print(sid, len(t), t[1], t[-1])
    except Exception as e: print(sid, "ERR", e)
