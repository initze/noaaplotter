"""Inspect the Fairbanks repro parquet: missing dates, dups, dtypes, values."""
import polars as pl
import pandas as pd
from datetime import datetime
from dateutil import rrule

OUT = r'C:\Users\initze\AppData\Local\Temp\noaa_repro\NOAA_USW00026411.parquet'
df = pl.read_parquet(OUT)
print("schema:")
for c, t in df.schema.items():
    print(f"  {c}: {t}")

print("\nnulls:", {c: df[c].null_count() for c in df.columns})
ndup = df.height - df['DATE'].n_unique()
print(f"duplicate DATE rows: {ndup}")
if ndup:
    dups = df.group_by('DATE').len().sort('len', descending=True).head(5)
    print(dups)

# expected full range
start = datetime(1981, 1, 1)
end = datetime(2026, 9, 4)
expected = {d.strftime("%Y-%m-%d") for d in rrule.rrule(rrule.DAILY, dtstart=start, until=end)}
have = set(df['DATE'].to_list())
missing = sorted(expected - have)
extra = sorted(have - expected)
print(f"\nexpected dates: {len(expected)}, have: {len(have)}")
print(f"missing: {missing[:20]}{' ...' if len(missing) > 20 else ''} (n={len(missing)})")
print(f"extra: {extra[:20]} (n={len(extra)})")

# the extra index column
if '__index_level_0__' in df.columns:
    col = df['__index_level_0__']
    print(f"\n__index_level_0__ dtype={col.dtype}, nulls={col.null_count()}")
    # how does it relate to DATE?
    same = (df['DATE'] == df['__index_level_0__']).sum() if col.dtype == pl.Utf8 else 'not str'
    print(f"  equals DATE for {same} rows")
    print("  head:", df.select(['DATE', '__index_level_0__']).head(3))

# SNOW sanity: values in winter
w = df.filter(pl.col('DATE').str.starts_with('2024-01'))
print(f"\n2024-01 rows={w.height}, SNOW>0: {w.filter(pl.col('SNOW') > 0).height}, "
      f"max TAVG={w['TAVG'].max()}, min TMIN={w['TMIN'].min()}")
# check TAVG vs (TMAX+TMIN)/2 agreement
check = df.filter(pl.col('TAVG').is_not_null() & pl.col('TMAX').is_not_null() & pl.col('TMIN').is_not_null())
diff = (check['TAVG'] - (check['TMAX'] + check['TMIN']) / 2).abs().max()
print(f"max |TAVG - (TMAX+TMIN)/2| = {diff}")
