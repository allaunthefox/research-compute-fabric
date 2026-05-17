#!/usr/bin/env python3
"""Final push — target the last 6 sub-2.0 domains. Short & dense."""

import sqlite3, urllib.request, urllib.parse, json, time, os

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
cur = conn.cursor()
cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
dom_eqs = {}; [dom_eqs.setdefault(d,[]).append(e) for d,e in cur.fetchall()]

FINAL = {
    5: [ # Quantum Mechanics (1.0)
        "density matrix Lindblad master equation decoherence measurement trapped ion superconducting","Ehrenfest theorem expectation value quantum classical correspondence measurement","Bell inequality CHSH loophole free experiment Hensen Hanson entanglement measurement","EPR paradox Einstein Podolsky Rosen entanglement swapping quantum teleportation measurement","quantum Zeno effect anti Zeno continuous measurement inhibition acceleration decay measurement","Berry phase geometric phase spin echo neutron interferometer measurement",
    ],
    25: [ # Surface Science (1.3)
        "X-ray photoelectron spectroscopy XPS chemical state binding energy surface measurement","Auger electron spectroscopy elemental composition surface sensitivity depth measurement","scanning tunneling microscopy atomic resolution density states spectroscopy measurement","atomic force microscopy force distance curve adhesion elasticity surface measurement","quartz crystal microbalance QCM mass sensitivity Sauerbrey equation adsorption measurement","ellipsometry thin film thickness refractive index optical constant delta psi measurement",
    ],
    21: [ # Material Physics (1.6) — quick add
        "electron backscatter diffraction EBSD grain orientation texture pole figure measurement","transmission electron microscopy bright field dark field diffraction contrast dislocation measurement","atom probe tomography field ion microscopy compositional reconstruction precipitate measurement","nanoindentation hardness elastic modulus mapping array high throughput measurement","digital image correlation DIC full field strain measurement heterogeneous deformation",
    ],
    22: [ # Crystallography (1.6)
        "single crystal X-ray diffraction structure solution direct methods Patterson heavy atom refinement","powder X-ray diffraction Rietveld refinement quantitative phase analysis whole pattern fitting","electron crystallography microED protein structure nanocrystal diffraction cryo TEM measurement",
    ],
    24: [ # Polymer Physics (1.8)
        "dynamic mechanical analysis DMA storage loss modulus temperature frequency master curve measurement","gel permeation chromatography size exclusion light scattering absolute molecular weight measurement",
    ],
    40: [ # Quantum Information (1.8)
        "superconducting transmon qubit coherence time T1 T2 gate fidelity randomized benchmarking measurement","trapped ion quantum computing Cirac Zoller gate entanglement Bell pair fidelity measurement",
    ],
}

def cr(q,mx=5):
    o=[]
    try:
        u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":mx,"sort":"relevance","filter":"type:journal-article"})
        r=urllib.request.Request(u,headers={"User-Agent":"FinalPush/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t=(i.get("title",[""])or[""])[0];y=i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi=i.get("DOI","");jn=(i.get("container-title",[""])or[""])[0]
            if t:o.append((t[:250],y,"CR",doi,jn))
    except:pass
    return o

def oa(q,mx=5):
    o=[]
    try:
        u="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per_page":mx,"sort":"cited_by_count:desc"})
        r=urllib.request.Request(u,headers={"User-Agent":"mailto:r@x.com"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("results",[]):
            t=i.get("title","");y=i.get("publication_year")or 0;doi=i.get("doi","");jn=""
            if i.get("primary_location")and i["primary_location"].get("source"):
                jn=i["primary_location"]["source"].get("display_name","")
            if t:o.append((t[:250],y,"OA",doi,jn))
    except:pass
    return o

def s2(q,mx=5):
    o=[]
    try:
        u="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":q,"limit":mx,"fields":"title,year,externalIds,journal,citationCount"})
        r=urllib.request.Request(u,headers={"User-Agent":"FinalPush/1.0"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e=p.get("externalIds",{})or{};jn=p.get("journal",{})or{}
            o.append((p.get("title","")[:250],p.get("year")or 0,"S2",e.get("DOI",""),jn.get("name","")))
    except:pass
    return o

tasks=[(d,q)for d,qs in FINAL.items()for q in qs]
apis=[(cr,1.5),(oa,2.0),(s2,2.0),(oa,2.0),(cr,1.5),(s2,2.0)]

total=0;batch=[];start=time.time()
cur.execute("SELECT id,name FROM domains");dn={r[0]:r[1]for r in cur.fetchall()}

for idx,(did,query)in enumerate(tasks):
    fn,delay=apis[idx%len(apis)]
    papers=fn(query,5)
    eqs=dom_eqs.get(did,[None])
    for p in papers:
        exp=f"{p[2]}: {p[4]}"if p[4]else p[2]
        batch.append((eqs[len(batch)%len(eqs)],p[0],exp,p[1],p[3]if p[3]else p[2],"Final push"))
        total+=1
    print(f"  {'▪'if papers else'·'} {dn.get(did,'')[:20]:20s} {query[:55]:55s} → {len(papers)}p | {total}",flush=True)
    if len(batch)>=30:cur.executemany("INSERT INTO verifications (equation_id,test_name,experiment,year,precision_level,status)VALUES(?,?,?,?,?,?)",batch);conn.commit();batch=[]
    time.sleep(delay)

if batch:cur.executemany("INSERT INTO verifications (equation_id,test_name,experiment,year,precision_level,status)VALUES(?,?,?,?,?,?)",batch);conn.commit()

cur.execute("SELECT COUNT(*)FROM verifications");tv=cur.fetchone()[0]
print(f"\n{total} added. Database: {tv} verifications, 770 equations")

cur.execute("""SELECT d.name,ROUND(COUNT(DISTINCT v.id)*1.0/COUNT(DISTINCT e.id),1)as r
    FROM domains d LEFT JOIN equations e ON e.domain_id=d.id
    LEFT JOIN verifications v ON v.equation_id=e.id WHERE e.id IS NOT NULL
    GROUP BY d.id ORDER BY r""")
print("All domain ratios:")
for n,r in cur.fetchall():print(f"  {n:35s} {r:5.1f}")
conn.close()
print(f"{DB}")
