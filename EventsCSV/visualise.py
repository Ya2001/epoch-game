import csv, os
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'

# Load master + existing events.json
rows = []
with open(os.path.join(BASE, 'master_clean.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append({'year': int(r['year']), 'tag': r['tag'], 'country': r['country'], 'source': 'wikidata'})

import json
with open('/Users/akshay/Desktop/Phone Game/events.json', encoding='utf-8') as f:
    existing = json.load(f)
for e in existing:
    rows.append({'year': e['year'], 'tag': e['tag'], 'country': e.get('country',''), 'source': 'existing'})

years = [r['year'] for r in rows]
tags  = [r['tag']  for r in rows]

COLORS = {
    'war':         '#c0392b',
    'revolution':  '#e67e22',
    'empire':      '#8e44ad',
    'exploration': '#27ae60',
    'technology':  '#2980b9',
    'science':     '#16a085',
    'independence':'#f39c12',
    'culture':     '#d35400',
}

fig = plt.figure(figsize=(18, 14), facecolor='#1a1a2e')
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.3)

# ── 1. Total by century ──────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
centuries = sorted(set((y // 100) * 100 for y in years))
cent_counts_wiki = Counter((r['year'] // 100) * 100 for r in rows if r['source'] == 'wikidata')
cent_counts_exist = Counter((r['year'] // 100) * 100 for r in rows if r['source'] == 'existing')
x = np.arange(len(centuries))
w = 0.6
bars_w = ax1.bar(x, [cent_counts_wiki.get(c, 0) for c in centuries], w, label='Wikidata', color='#3498db', alpha=0.85)
bars_e = ax1.bar(x, [cent_counts_exist.get(c, 0) for c in centuries], w,
                  bottom=[cent_counts_wiki.get(c, 0) for c in centuries],
                  label='Existing (events.json)', color='#2ecc71', alpha=0.85)
ax1.set_xticks(x)
ax1.set_xticklabels([f"{c}s" for c in centuries], color='white', fontsize=9)
ax1.set_facecolor('#16213e')
ax1.set_title('Event Count by Century — Wikidata vs Existing', color='white', fontsize=13, pad=10)
ax1.set_ylabel('Events', color='white')
ax1.tick_params(colors='white')
ax1.legend(facecolor='#1a1a2e', labelcolor='white')
for bar in bars_w:
    h = bar.get_height()
    if h > 0:
        ax1.text(bar.get_x() + bar.get_width()/2, h/2, str(h), ha='center', va='center', color='white', fontsize=7, fontweight='bold')

# ── 2. Tag distribution (all events) ────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
tag_counts = Counter(tags)
sorted_tags = sorted(tag_counts, key=tag_counts.get, reverse=True)
colors_list = [COLORS.get(t, '#95a5a6') for t in sorted_tags]
bars = ax2.barh(sorted_tags, [tag_counts[t] for t in sorted_tags], color=colors_list, alpha=0.9)
ax2.set_facecolor('#16213e')
ax2.set_title('Events by Tag (all sources)', color='white', fontsize=11, pad=8)
ax2.tick_params(colors='white')
for bar, t in zip(bars, sorted_tags):
    ax2.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
             str(tag_counts[t]), va='center', color='white', fontsize=9)

# ── 3. Decade histogram (1000–2026) ─────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
decade_bins = list(range(1000, 2030, 20))
ax3.hist(years, bins=decade_bins, color='#9b59b6', alpha=0.85, edgecolor='#1a1a2e', linewidth=0.4)
ax3.set_facecolor('#16213e')
ax3.set_title('Events per 20-year Period', color='white', fontsize=11, pad=8)
ax3.set_xlabel('Year', color='white')
ax3.set_ylabel('Count', color='white')
ax3.tick_params(colors='white')
ax3.axhline(y=15, color='#e74c3c', linestyle='--', linewidth=1, label='Target floor (15)')
ax3.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)

# ── 4. Stacked century by tag ────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[2, :])
all_tags = list(COLORS.keys())
cent_tag = defaultdict(Counter)
for r in rows:
    cent_tag[(r['year'] // 100) * 100][r['tag']] += 1
bottom = np.zeros(len(centuries))
for tag in all_tags:
    vals = np.array([cent_tag[c].get(tag, 0) for c in centuries])
    ax4.bar(x, vals, w, bottom=bottom, label=tag, color=COLORS[tag], alpha=0.85)
    bottom += vals
ax4.set_xticks(x)
ax4.set_xticklabels([f"{c}s" for c in centuries], color='white', fontsize=9)
ax4.set_facecolor('#16213e')
ax4.set_title('Tag Composition by Century', color='white', fontsize=13, pad=10)
ax4.set_ylabel('Events', color='white')
ax4.tick_params(colors='white')
ax4.legend(facecolor='#1a1a2e', labelcolor='white', ncol=4, fontsize=9,
           loc='upper left', bbox_to_anchor=(0, 1))

fig.suptitle('Epoch — Event Dataset Distribution', color='white', fontsize=16, y=1.01, fontweight='bold')

out = '/Users/akshay/Desktop/Phone Game/EventsCSV/distribution.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
print(f"Saved → {out}")

# ── Text summary of gaps ─────────────────────────────────────────────────────
print("\n=== 20-year bucket gaps (< 15 events) ===")
from collections import Counter as C
dec_c = C((y // 20) * 20 for y in years)
for start in range(1000, 2020, 20):
    n = dec_c.get(start, 0)
    if n < 15:
        print(f"  {start}–{start+19}: {n} events  ← NEEDS FILLING")

print("\n=== Tag totals ===")
for t in sorted(tag_counts, key=tag_counts.get, reverse=True):
    print(f"  {t:15s}: {tag_counts[t]}")
