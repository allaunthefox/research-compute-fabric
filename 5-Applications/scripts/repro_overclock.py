#!/usr/bin/env python3
"""Add reproductive overclocking / semelparity as a radical adaptation."""

import sqlite3, urllib.request, urllib.parse, json, time, os

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Get Radical Adaptations domain id
cur.execute("SELECT id FROM domains WHERE name='Radical Adaptations'")
rad_did = cur.fetchone()
rad_did = rad_did[0] if rad_did else 52

# Get max equation IDs
cur.execute("SELECT MAX(id) FROM equations"); eid = cur.fetchone()[0]
cur.execute("SELECT MAX(eq_number) FROM equations"); enum = cur.fetchone()[0]

# ================================================================
# MAIN EQUATION
# ================================================================
eid += 1; enum += 1
eq_id = eid

sig = "A life-history strategy where an organism temporarily exceeds sustainable somatic maintenance limits to maximize reproductive output in a single catastrophic breeding season, followed by programmed death. The antechinus (Australian marsupial) is the cleanest mammalian example: males flood with testosterone/cortisol during a 2-3 week breeding window, mating for up to 14 hours per session, losing fur, developing ulcers, and dying before the young are born. Silver-headed, dusky, and Tasman Peninsula antechinus all exhibit this. Kaluta (Dasykaluta rosamondae) does the same. Beyond mammals: Pacific salmon undergo total somatic degeneration during upstream migration → spawn → die. Octopus mothers guard eggs for months without eating, then die via optic gland hormone cascade (removing the optic gland prevents death). Male orb-weaving spiders consumed during/after mating. Agave and bamboo flower once after decades, drain resources into a massive reproductive stalk, then die."

prec = "Tradeoff limit: d(fitness)/d(survival) → ∞ at reproduction event. Glucocorticoid storm: cortisol exceeds renal clearance capacity. Immune collapse: neutrophil/lymphocyte ratio inverted. Mammalian semelparity independently evolved at least twice in Dasyuridae."

cur.execute("INSERT INTO equations VALUES (?,?,?,?,?,?,?,?)", (
    eq_id, enum,
    "Reproductive Overclocking (Semelparity / Suicidal Reproduction) — Antechinus, Salmon, Octopus, Spiders, Agave, Kaluta",
    rad_did, "various", "Proven", sig, prec))

# ================================================================
# API FETCHERS
# ================================================================
def crossref(q, lim=5):
    out = []
    try:
        u = "https://api.crossref.org/works?" + urllib.parse.urlencode({
            "query": q, "rows": lim, "sort": "relevance", "filter": "type:journal-article"})
        r = urllib.request.Request(u, headers={"User-Agent": "ReproOverclock/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t = (i.get("title",[""]) or [""])[0]
            y = i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi = i.get("DOI","")
            j = (i.get("container-title",[""]) or [""])[0]
            if t: out.append({"title":t[:250],"year":y,"doi":doi,"journal":j,"src":"Crossref"})
    except: pass
    return out

def openalex(q, lim=5):
    out = []
    try:
        u = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": q, "per_page": lim, "sort": "cited_by_count:desc"})
        r = urllib.request.Request(u, headers={"User-Agent": "mailto:r@x.com"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for i in d.get("results",[]):
            t = i.get("title","")
            y = i.get("publication_year")or 0
            doi = i.get("doi","")
            j = ""
            if i.get("primary_location") and i["primary_location"].get("source"):
                j = i["primary_location"]["source"].get("display_name","")
            if t: out.append({"title":t[:250],"year":y,"doi":doi,"journal":j,"src":"OpenAlex"})
    except: pass
    return out

def s2(q, lim=5):
    out = []
    try:
        u = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
            "query": q, "limit": lim, "fields": "title,year,externalIds,journal,citationCount"})
        r = urllib.request.Request(u, headers={"User-Agent": "ReproOverclock/1.0"})
        with urllib.request.urlopen(r, timeout=20) as resp:
            d = json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e = p.get("externalIds",{}) or {}
            j = p.get("journal",{}) or {}
            out.append({"title":p.get("title","")[:250],"year":p.get("year")or 0,
                       "doi":e.get("DOI",""),"journal":j.get("name",""),"src":"S2"})
    except: pass
    return out

# ================================================================
# SEARCH QUERIES — diverse taxa
# ================================================================
QUERIES = [
    ("antechinus semelparity male die off after breeding marsupial suicidal reproduction", "Antechinus mammal"),
    ("salmon semelparity programmed death upstream migration cortisol degeneration senescence", "Pacific salmon"),
    ("octopus maternal semelparity optic gland death after egg hatching programmed senescence", "Octopus maternal"),
    ("semelparity iteroparity life history evolution trade off reproduction survival", "Semelparity theory"),
    ("suicidal reproduction spider male sacrifice sexual cannibalism orb weaver", "Spider sexual cannibalism"),
    ("dasyurid marsupial semelparity antechinus kaluta phascogale die off breeding", "Dasyurid marsupials"),
    ("programmed death semelparous plant agave century plant bamboo monocarpic senescence", "Monocarpic plants"),
    ("glucocorticoid cortisol stress induced mortality reproduction trade off physiology", "Glucocorticoid mechanism"),
    ("terminal investment hypothesis reproduction senescence trade off life history theory", "Terminal investment"),
    ("pacific salmon Oncorhynchus spawning migration programmed cell death organ failure", "Salmon mechanism"),
    ("octopus vulgaris optic gland senescence removal lifespan extension reproduction behavior", "Octopus optic gland"),
    ("antechinus stuartii flavipes argentus male die off stress hormones cortisol testosterone", "Antechinus physiology"),
]

print(f"Fetching {len(QUERIES)} reproductive-overclocking queries across 3 APIs...\n")
total, rows = 0, []
start = time.time()

apis = [(crossref,1.5),(openalex,1.5),(s2,2.0),(crossref,1.5),(openalex,1.5),(s2,2.0)]

for i, (q, label) in enumerate(QUERIES):
    fn, delay = apis[i % len(apis)]
    papers = fn(q, 5)
    for p in papers:
        rows.append((eq_id, p['title'],
            f"{p['src']}: {p.get('journal','')}" if p.get('journal') else p['src'],
            p['year'], p.get('doi', p['src']), "Radical adaptation ref."))
        total += 1
    print(f"  {'✓' if papers else '○'} {label:25s} | {fn.__name__:8s} → {len(papers):2d}p | {total:3d} total | {time.time()-start:.0f}s", flush=True)
    time.sleep(delay)

cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", rows)
conn.commit()

cur.execute("SELECT COUNT(*) FROM verifications WHERE status='Radical adaptation ref.'")
print(f"\nRadical adaptation refs (total): {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM verifications")
print(f"Total verifications in DB: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM equations WHERE domain_id=?", (rad_did,))
print(f"Radical Adaptations equations: {cur.fetchone()[0]}")

print(f"\nNew equation #{enum}: Reproductive Overclocking (Semelparity)")
print(f"  Species covered:")
for q, label in QUERIES:
    print(f"    - {label}")
conn.close()
print(f"  Database: {DB}")
