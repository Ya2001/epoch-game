import urllib.request, urllib.parse, json, time, csv, os, re, sys

ENDPOINT = 'https://query.wikidata.org/sparql'
BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'
QID_RE = re.compile(r'^Q\d+$')

HEADERS = {
    'Accept': 'application/sparql-results+json',
    'User-Agent': 'EpochGame/1.0 (history quiz; contact srivats66@gmail.com)'
}

BANDS = [
    (1000, 1200), (1200, 1350), (1350, 1500),
    (1500, 1650), (1650, 1800), (1800, 1900),
    (1900, 1970), (1970, 2027),
]

QUERIES = {
    'science': {
        'tag': 'science',
        'types': ['wd:Q12772819', 'wd:Q483247', 'wd:Q101965', 'wd:Q2725376'],
        'date_prop': 'wdt:P585',
    },
    'exploration': {
        'tag': 'exploration',
        'types': ['wd:Q83821', 'wd:Q2281788', 'wd:Q152571', 'wd:Q88', 'wd:Q2281788'],
        'date_prop': 'wdt:P580',
    },
    'independence': {
        'tag': 'independence',
        'types': ['wd:Q179023', 'wd:Q3024240', 'wd:Q11344118', 'wd:Q112099'],
        'date_prop': 'wdt:P571',
    },
}

def build_sparql(types, date_prop, year_min, year_max):
    type_vals = ' '.join(types)
    return f"""
SELECT DISTINCT ?event ?eventLabel (YEAR(?date) AS ?year) ?countryLabel WHERE {{
  VALUES ?type {{ {type_vals} }}
  ?event wdt:P31 ?type ;
         {date_prop} ?date .
  FILTER(YEAR(?date) >= {year_min} && YEAR(?date) < {year_max})
  OPTIONAL {{ ?event wdt:P17 ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY RAND()
LIMIT 60
""".strip()

def run_query(sparql):
    params = urllib.parse.urlencode({'query': sparql, 'format': 'json'})
    url = f"{ENDPOINT}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None

all_rows = []
seen_ids = set()

for cat_name, cfg in QUERIES.items():
    print(f"\n{'='*40}")
    print(f"Category: {cat_name.upper()}")
    cat_rows = []
    for (y_min, y_max) in BANDS:
        sparql = build_sparql(cfg['types'], cfg['date_prop'], y_min, y_max)
        print(f"  {y_min}–{y_max} ... ", end='', flush=True)
        data = run_query(sparql)
        if data is None:
            print("TIMEOUT/ERROR")
            time.sleep(3)
            continue
        results = data.get('results', {}).get('bindings', [])
        kept = 0
        for r in results:
            label = r.get('eventLabel', {}).get('value', '')
            if QID_RE.match(label):
                continue
            event_id = r.get('event', {}).get('value', '').split('/')[-1]
            if event_id in seen_ids:
                continue
            year_val = r.get('year', {}).get('value', '')
            if not year_val:
                continue
            country = r.get('countryLabel', {}).get('value', '')
            seen_ids.add(event_id)
            row = {
                'id': event_id,
                'label': label,
                'year': int(year_val),
                'country': country,
                'tag': cfg['tag'],
                'source_file': f'{cat_name}_gap',
            }
            cat_rows.append(row)
            kept += 1
        print(f"{kept} kept")
        time.sleep(1.5)  # be polite to Wikidata
    print(f"  Subtotal: {len(cat_rows)}")
    all_rows.extend(cat_rows)

# Write gap fills CSV
out_path = os.path.join(BASE, 'gap_fills.csv')
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id','label','year','country','tag','source_file'])
    writer.writeheader()
    writer.writerows(sorted(all_rows, key=lambda r: r['year']))

print(f"\n✓ {len(all_rows)} new events → gap_fills.csv")

# Print year distribution of new events
from collections import Counter
dec = Counter((r['year'] // 100) * 100 for r in all_rows)
for c in sorted(dec):
    print(f"  {c}s: {dec[c]}")
