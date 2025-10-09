# -*- coding: utf-8 -*-
import re, json, hashlib
from collections import defaultdict, Counter
from graphviz import Digraph
from pathlib import Path

# ===== 1) DÁN NGUYÊN KHỐI DỮ LIỆU CỦA BẠN VÀO ĐÂY (không để "..."!) =========
RAW_TEXT = r"""
[['Trần Văn Tỷ', 'date of birth', '10/02/1979'], ['Trần Văn Tỷ', 'place of birth', 'Xã Long Trị A, Thị xã Long Mỹ, Tỉnh Hậu Giang'], ['Trần Văn Tỷ', 'located in the administrative territorial entity', 'Nhà sole 10, Khu Tập thể Đại học Cần Thơ, Khu 1, Đường 30/4, Phường Hưng Lợi, Quận Ninh Kiều, TP. Cần Thơ'], ['Trần Văn Tỷ', 'located in the administrative territorial entity', 'Khoa Công nghệ, Trường Đại học Cần Thơ, Khu 2, Đường 3/2, Phường Xuân Khánh, Quận Ninh Kiều, TP. Cần Thơ']]
[['Trường Đại học Khoa học Ứng dụng Cologne', 'country', 'CHLB Đức']]
[['Trường Đại học Thủy lợi', 'country', 'Việt Nam']]
[['Bộ Giáo dục và Đào tạo', 'country', 'Việt Nam']]
[['Số 38/125 Thụy Khuê, Tây Hồ, Hà Nội', 'located in the administrative territorial entity', 'Số 38/125 Thụy Khuê'], ['Số 38/125 Thụy Khuê, Tây Hồ, Hà Nội', 'located in the administrative territorial entity', 'Tây Hồ'], ['Số 38/125 Thụy Khuê, Tây Hồ, Hà Nội', 'located in the administrative territorial entity', 'Hà Nội']]
[['Viện Khoa học Thủy lợi', 'start time', '2002']]
"""

# ===== 2) Parser ==============================================================
TRIPLE_RE = re.compile(r"\[\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*\]")

def parse_triples(raw: str):
    return [(s.strip(), p.strip(), o.strip()) for s, p, o in TRIPLE_RE.findall(raw)]

triples = parse_triples(RAW_TEXT)
if not triples:
    raise SystemExit("⚠️ Không tìm thấy triple nào. Hãy dán đúng khối RAW_TEXT (không để ...).")

# ===== 3) Lọc gọn & chuẩn hoá ngày cho dễ nhìn =================================
VISIBLE_P = {
    "date of birth", "place of birth", "country",
    "located in the administrative territorial entity", "start time",
}
triples = [t for t in triples if t[1] in VISIBLE_P]

def norm_date(d):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", d)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else d

norm_triples = []
for s, p, o in triples:
    if p in {"date of birth", "start time"}:
        o = norm_date(o)
    norm_triples.append((s, p, o))

edge_counter = Counter(norm_triples)

def is_resource_like(x: str) -> bool:
    return any(ch.isalpha() for ch in x) and len(x) >= 3

# ===== 4) ID an toàn cho Graphviz (không chứa ':', khoảng trắng, ký tự lạ) =====
def safe_id(prefix: str, label: str) -> str:
    # tạo slug ngắn + hash để đảm bảo duy nhất
    slug = re.sub(r"[^A-Za-z0-9_]", "_", label)[:40]
    h = hashlib.md5(label.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{slug}_{h}"

by_subj = defaultdict(list)
for (s, p, o), w in edge_counter.items():
    by_subj[s].append((p, o, w))

# ===== 5) Vẽ Graphviz PNG =====================================================
dot = Digraph("KG", format="png")  # engine mặc định 'dot'
dot.attr(rankdir="LR", fontsize="12", fontname="Helvetica")
dot.attr("node", shape="ellipse", style="filled", fillcolor="#f6faff", color="#6baed6")

# Tạo node cho subject
sid_map = {}
for s in by_subj:
    sid = safe_id("S", s)
    sid_map[s] = sid
    dot.node(sid, label=s, shape="oval", fillcolor="#e8f2ff")

# Tạo node cho object & literal
oid_map = {}
for s, pairs in by_subj.items():
    s_id = sid_map[s]
    for p, o, w in pairs:
        pw = str(1 + min(w, 3) * 0.4)
        if is_resource_like(o):
            if o not in oid_map:
                oid = safe_id("O", o)
                oid_map[o] = oid
                dot.node(oid, label=o, shape="box", fillcolor="#fff7e6", color="#fd8d3c")
            dot.edge(s_id, oid_map[o], label=p, fontsize="10", color="#666666", penwidth=pw)
        else:
            lid = safe_id("L", f"{s}|{p}|{o}")
            dot.node(lid, label=o, shape="note", fillcolor="#f0f0f0", color="#9e9e9e")
            dot.edge(s_id, lid, label=p, fontsize="10", color="#888888")

out_png = Path("kg_view.png")
dot.render(out_png.with_suffix(""), cleanup=True)
print(f"✅ Đã tạo: {out_png.resolve()}")

# ===== 6) HTML tương tác (canvas + d3-force) ==================================
nodes = {}
def add_node(id_, label, kind):
    if id_ not in nodes: nodes[id_] = {"id": id_, "label": label, "kind": kind}

links = []
for s in by_subj:
    s_id = sid_map[s]; add_node(s_id, s, "subject")
    for p, o, w in by_subj[s]:
        if is_resource_like(o):
            o_id = oid_map.setdefault(o, safe_id("O", o))
            add_node(o_id, o, "object")
            links.append({"source": s_id, "target": o_id, "label": p, "w": w})
        else:
            l_id = safe_id("L", f"{s}|{p}|{o}")
            add_node(l_id, o, "literal")
            links.append({"source": s_id, "target": l_id, "label": p, "w": 1})

data = {"nodes": list(nodes.values()), "links": links}

HTML = f"""<!doctype html>
<meta charset="utf-8"/>
<title>KG View</title>
<style>
  body {{ font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial; margin:0; }}
  #canvas {{ width: 100vw; height: 100vh; }}
  .tooltip {{ position:absolute; background:rgba(0,0,0,.75); color:#fff; padding:6px 8px; border-radius:4px; pointer-events:none; font-size:12px; }}
</style>
<div id="canvas"></div>
<div id="tip" class="tooltip" style="opacity:0"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {json.dumps(data, ensure_ascii=False)};
const W = innerWidth, H = innerHeight;
const c = document.createElement('canvas'); c.width=W; c.height=H; document.getElementById('canvas').appendChild(c);
const ctx = c.getContext('2d'); const tip = document.getElementById('tip');
function color(k){{return k==='subject'?'#6baed6':k==='object'?'#fd8d3c':'#9e9e9e';}}
function radius(k){{return k==='subject'?12:k==='object'?9:6;}}
const sim = d3.forceSimulation(data.nodes)
 .force('link', d3.forceLink(data.links).id(d=>d.id).distance(120).strength(0.2))
 .force('charge', d3.forceManyBody().strength(-180))
 .force('center', d3.forceCenter(W/2,H/2));
function draw(){{
  ctx.clearRect(0,0,W,H); ctx.save(); ctx.translate(.5,.5);
  ctx.globalAlpha=.7; data.links.forEach(l=>{{ctx.beginPath(); ctx.moveTo(l.source.x,l.source.y); ctx.lineTo(l.target.x,l.target.y); ctx.strokeStyle='#aaa'; ctx.lineWidth=Math.min(1+(l.w||1)*.4,3); ctx.stroke();}});
  ctx.globalAlpha=1; data.nodes.forEach(n=>{{ctx.beginPath(); ctx.arc(n.x,n.y,radius(n.kind),0,Math.PI*2); ctx.fillStyle=color(n.kind); ctx.fill();}});
  ctx.font='12px sans-serif'; ctx.fillStyle='#222'; ctx.textAlign='center'; ctx.textBaseline='top';
  data.nodes.forEach(n=>ctx.fillText(n.label,n.x,n.y+radius(n.kind)+3)); ctx.restore();
}}
sim.on('tick', draw);
c.addEventListener('mousemove', e=>{{
  const r=c.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
  let f=null; for(const n of data.nodes){{const dx=n.x-mx, dy=n.y-my; if(dx*dx+dy*dy<=Math.pow(radius(n.kind)+2,2)){{f=n;break;}}}}
  if(f){{tip.style.opacity=1; tip.style.left=(e.pageX+12)+'px'; tip.style.top=(e.pageY+12)+'px'; tip.textContent=f.label;}} else tip.style.opacity=0;
}});
</script>
"""
Path("kg_view.html").write_text(HTML, encoding="utf-8")
print("✅ Đã tạo:", Path("kg_view.html").resolve())