import csv, json, os, re
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'
QID_RE = re.compile(r'^Q\d+$')

# ── Load all sources ─────────────────────────────────────────────────────────
def load_csv(path, retag=None):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            label = r.get('label','') or r.get('eventLabel','')
            if QID_RE.match(label): continue
            rows.append({
                'id': r['id'],
                'label': label,
                'year': int(r['year']),
                'country': r.get('country',''),
                'tag': retag or r['tag'],
            })
    return rows

# Independence events 1000–1650 are kingdom/state foundings → empire
def smart_retag(rows):
    for r in rows:
        if r['tag'] == 'independence' and r['year'] < 1650:
            r['tag'] = 'empire'
    return rows

master   = load_csv(os.path.join(BASE, 'master_clean.csv'))
gap1     = smart_retag(load_csv(os.path.join(BASE, 'gap_fills.csv')))
gap2     = load_csv(os.path.join(BASE, 'gap_fills2.csv'))

# Dedup by id
seen = set()
combined = []
for r in master + gap1 + gap2:
    if r['id'] not in seen:
        seen.add(r['id'])
        combined.append(r)

# Also load existing events.json
with open('/Users/akshay/Desktop/Phone Game/events.json') as f:
    existing = json.load(f)
for e in existing:
    eid = e['id']
    if eid not in seen:
        seen.add(eid)
        combined.append({'id': eid, 'label': e['title'], 'year': e['year'],
                         'country': e.get('country',''), 'tag': e['tag'], '_existing': True})

print(f"Total combined: {len(combined)}")
tag_counts = Counter(r['tag'] for r in combined)
for t,n in sorted(tag_counts.items(), key=lambda x:-x[1]):
    print(f"  {t:15s}: {n}")

# ── Visualise ────────────────────────────────────────────────────────────────
COLORS = {
    'war':'#c0392b','revolution':'#e67e22','empire':'#8e44ad',
    'exploration':'#27ae60','technology':'#2980b9','science':'#16a085',
    'independence':'#f39c12','culture':'#d35400',
}

fig = plt.figure(figsize=(20, 16), facecolor='#1a1a2e')
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.48, wspace=0.3)

years = [r['year'] for r in combined]
centuries = sorted(set((y//100)*100 for y in years))
x = np.arange(len(centuries))
w = 0.65

# ── 1. Century bar (new vs existing) ────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
cnt_new = Counter((r['year']//100)*100 for r in combined if not r.get('_existing'))
cnt_ex  = Counter((r['year']//100)*100 for r in combined if r.get('_existing'))
ax1.bar(x, [cnt_new.get(c,0) for c in centuries], w, label='Wikidata/new', color='#3498db', alpha=0.85)
ax1.bar(x, [cnt_ex.get(c,0) for c in centuries], w,
        bottom=[cnt_new.get(c,0) for c in centuries],
        label='Existing (events.json)', color='#2ecc71', alpha=0.85)
for i,c in enumerate(centuries):
    total = cnt_new.get(c,0)+cnt_ex.get(c,0)
    ax1.text(i, total+1, str(total), ha='center', color='white', fontsize=8, fontweight='bold')
ax1.set_xticks(x); ax1.set_xticklabels([f"{c}s" for c in centuries], color='white', fontsize=9)
ax1.set_facecolor('#16213e'); ax1.set_title('Events by Century — Combined Dataset', color='white', fontsize=13, pad=10)
ax1.set_ylabel('Count', color='white'); ax1.tick_params(colors='white')
ax1.legend(facecolor='#1a1a2e', labelcolor='white')

# ── 2. Tag distribution ──────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
s_tags = sorted(tag_counts, key=tag_counts.get, reverse=True)
ax2.barh(s_tags, [tag_counts[t] for t in s_tags],
         color=[COLORS.get(t,'#95a5a6') for t in s_tags], alpha=0.9)
for t in s_tags:
    ax2.text(tag_counts[t]+2, s_tags.index(t), str(tag_counts[t]), va='center', color='white', fontsize=9)
ax2.set_facecolor('#16213e'); ax2.set_title('Events by Tag', color='white', fontsize=11, pad=8)
ax2.tick_params(colors='white')

# ── 3. 20-yr histogram ───────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
bins20 = list(range(1000, 2040, 20))
ax3.hist(years, bins=bins20, color='#9b59b6', alpha=0.85, edgecolor='#1a1a2e', linewidth=0.4)
ax3.axhline(y=15, color='#e74c3c', linestyle='--', linewidth=1.2, label='Floor (15)')
ax3.set_facecolor('#16213e'); ax3.set_title('Events per 20-year Bucket', color='white', fontsize=11, pad=8)
ax3.set_xlabel('Year', color='white'); ax3.set_ylabel('Count', color='white')
ax3.tick_params(colors='white'); ax3.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)

# ── 4. Stacked century by tag ────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[2, :])
all_tags = list(COLORS.keys())
cent_tag = defaultdict(Counter)
for r in combined:
    cent_tag[(r['year']//100)*100][r['tag']] += 1
bottom = np.zeros(len(centuries))
for tag in all_tags:
    vals = np.array([cent_tag[c].get(tag,0) for c in centuries])
    ax4.bar(x, vals, w, bottom=bottom, label=tag, color=COLORS[tag], alpha=0.85)
    bottom += vals
ax4.set_xticks(x); ax4.set_xticklabels([f"{c}s" for c in centuries], color='white', fontsize=9)
ax4.set_facecolor('#16213e'); ax4.set_title('Tag Composition by Century', color='white', fontsize=13, pad=10)
ax4.set_ylabel('Events', color='white'); ax4.tick_params(colors='white')
ax4.legend(facecolor='#1a1a2e', labelcolor='white', ncol=4, fontsize=9, loc='upper left')

fig.suptitle(f'Epoch — Combined Dataset ({len(combined)} events)', color='white', fontsize=16, y=1.01, fontweight='bold')
out = os.path.join(BASE, 'distribution_v2.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
print(f"\nSaved → {out}")

# ── Remaining gaps ───────────────────────────────────────────────────────────
print("\n=== Still below 15 events per 20-yr bucket ===")
dec_c = Counter((r['year']//20)*20 for r in combined)
for start in range(1000, 2020, 20):
    n = dec_c.get(start,0)
    if n < 15:
        print(f"  {start}–{start+19}: {n}")
