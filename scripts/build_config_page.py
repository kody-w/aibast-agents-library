#!/usr/bin/env python3
"""Generate config.html — the configuration-guide deck viewer.

The page is GENERATED rather than hand-written for one reason: its header,
footer and design tokens must be byte-identical to every other page on the
site. Copying them by hand is how a site ends up with four slightly different
navs, and nobody can tell which one is right.

So the shared blocks are lifted out of roadmap.html at build time and this file
only owns what is genuinely this page's own: the slide renderers, the deck
chrome, and the export button.

Run it after changing the shared theme or the page's own parts:
    python3 scripts/build_config_page.py
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The shared blocks, taken from the page that already carries them, so this
# page cannot drift from the rest of the site.
_src = (ROOT / "roadmap.html").read_text(encoding="utf-8")
CSS = _src[_src.index("/* ══ ms-rapp shared design language"):
           _src.index("/* ══ page-specific")]
HEADER = _src[_src.index("<!-- ══ shared site header"):
              _src.index("</header>") + len("</header>")]
FOOTER = _src[_src.index('<footer class="site">'):
              _src.index("</footer>") + len("</footer>")]

PAGE_CSS = """/* ══ page-specific ══════════════════════════════════════════════════════ */

/* The deck is the page. The header names it and gets out of the way — a title
   block repeating what the title slide already says costs a third of the
   screen and earns nothing. The standing note moves below the deck, where it
   is still on the page but is not competing with the argument. */
.head{padding:18px 0 10px;display:flex;gap:18px;align-items:flex-end;flex-wrap:wrap}
.head .crumb{font-size:11.5px;color:var(--text-faint);letter-spacing:.05em;text-transform:uppercase;
  font-weight:600;margin-bottom:4px}
.head h1{font-size:clamp(20px,2.6vw,26px);font-weight:700;letter-spacing:-.02em;line-height:1.15}
.head p{color:var(--text-dim);font-size:14px;margin-top:3px}
.actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-left:auto}
.foot-note{font-size:12.5px;color:var(--text-faint);max-width:86ch;margin:10px 0 30px;
  padding-left:12px;border-left:2px solid var(--border)}
.deck-status{font-size:13px;color:var(--text-faint);min-height:1em}
.exp-count{font-size:12px;color:var(--text-faint)}

/* The stage is a real 16:9 box so what is on screen is what lands in the file. */
/* The stage is capped to what is left of the viewport, so a whole slide is
   visible without scrolling — a deck you have to scroll is not a deck. */
.stage{position:relative;width:100%;aspect-ratio:16/9;max-height:calc(100vh - 210px);
  margin:0 auto;background:var(--panel);
  border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow);
  overflow:hidden}
.slide{position:absolute;inset:0;padding:4.2% 4.6%;display:none;flex-direction:column;
  container-type:size}
.slide.on{display:flex}
/* Type scales with the stage, so a slide reads the same at any window size. */
.slide .kick{font-size:2.4cqh;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--accent);margin-bottom:1.6cqh}
.slide h2{font-size:6.4cqh;font-weight:700;letter-spacing:-.02em;line-height:1.14}
.slide .body{font-size:3.5cqh;color:var(--text-dim);max-width:80ch;margin-top:1.8cqh;
  line-height:1.5}
.slide .sub{font-size:3.1cqh;color:var(--text-faint);margin-top:1.2cqh}
/* The "so what". Every page states its own conclusion rather than leaving the
   reader to derive it — the single biggest difference between a slide that
   informs and one that argues. */
.slide .takeaway{margin-top:auto;flex:0 0 auto;padding-top:1.6cqh;border-top:1px solid var(--border);
  display:flex;gap:1.4cqh;align-items:baseline;font-size:2.9cqh;line-height:1.4}
.slide .takeaway b{color:var(--accent);font-weight:700;white-space:nowrap;letter-spacing:.04em;
  font-size:2.4cqh;text-transform:uppercase}
.slide .takeaway span{color:var(--text)}

.sumgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:2cqh;margin-top:2.4cqh}
.sumgrid .col{border-top:3px solid var(--accent);padding-top:1.6cqh}
.sumgrid .col b{display:block;font-size:3.1cqh;line-height:1.25;margin-bottom:1cqh}
.sumgrid .col span{font-size:2.7cqh;color:var(--text-dim);line-height:1.45}

.slide.dark{background:linear-gradient(140deg,#070f26,#141a3c 60%,#25184a);color:#fff;
  justify-content:center}
.slide.dark h2{color:#fff;font-size:9cqh}
.slide.dark .kick{color:#e2669a}
.slide.dark .body,.slide.dark .sub{color:#c7cbe6}
.slide.dark .rule{width:7cqh;height:.9cqh;border-radius:1cqh;background:#e2669a;margin-bottom:2.4cqh}
/* The title slide named two products and showed neither. The chips are white
   so a monochrome mark (GitHub's) and a full-colour one (Microsoft's) both
   read on the dark ground. */
.titlemarks{display:flex;gap:1.6cqh;margin-top:4cqh;align-items:center}
.titlemarks .tm{display:flex;gap:1.2cqh;align-items:center;background:#fff;
  border-radius:8px;padding:1.2cqh 1.8cqh}
.titlemarks .tm img{width:3.6cqh;height:3.6cqh;object-fit:contain}
.titlemarks .tm span{font-size:2.4cqh;font-weight:650;color:#1a1d3f;white-space:nowrap}

.tiles{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:1.8cqh;margin-top:auto}
.tile{background:var(--panel-2);border:1px solid var(--border);border-radius:10px;padding:2.4cqh}
.tile .lab{font-size:2.3cqh;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  color:var(--accent)}
.tile .val{font-size:3cqh;margin-top:1cqh;line-height:1.35}

.prows{display:flex;flex-direction:column;gap:1.2cqh;margin-top:2.4cqh}
.prow{display:flex;gap:2cqh;align-items:center;background:var(--panel);border:1px solid var(--border);
  border-radius:9px;padding:1.8cqh 2.2cqh}
.prow img{width:5.2cqh;height:5.2cqh;object-fit:contain;flex:0 0 auto}
.prow .chip{width:5.2cqh;height:5.2cqh;border-radius:8px;background:var(--accent-soft);
  color:var(--accent);display:flex;align-items:center;justify-content:center;font-weight:700;
  font-size:3cqh;flex:0 0 auto}
.prow b{font-size:3.1cqh;display:block}
.prow span{font-size:2.7cqh;color:var(--text-dim);line-height:1.4}

table.adv{width:100%;border-collapse:separate;border-spacing:0 .8cqh;margin-top:1.5cqh}
table.adv th{font-size:2.2cqh;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  color:var(--text-faint);text-align:left;padding:0 1.4cqh}
table.adv th:last-child{color:var(--accent)}
table.adv td{background:var(--panel);border:1px solid var(--border);padding:1.2cqh 1.3cqh;
  font-size:2.6cqh;vertical-align:top;line-height:1.35}
table.adv td:first-child{border-radius:8px 0 0 8px;font-weight:650;font-size:2.9cqh}
table.adv td:last-child{border-radius:0 8px 8px 0;background:var(--accent-soft);
  border-color:var(--accent)}
table.adv td b{display:block;font-size:2.9cqh;margin-bottom:.5cqh}
table.adv td small{color:var(--text-dim);font-size:2.4cqh}
table.adv td .with{display:flex;gap:1.2cqh;align-items:flex-start}
table.adv td .with img{width:3.4cqh;height:3.4cqh;object-fit:contain;margin-top:.3cqh;flex:0 0 auto}

ol.steps{list-style:none;margin-top:2.4cqh;display:flex;flex-direction:column;gap:1.4cqh}
ol.steps li{display:flex;gap:1.8cqh;align-items:flex-start;font-size:3cqh;line-height:1.4}
ol.steps .n{flex:0 0 auto;width:4.4cqh;height:4.4cqh;border-radius:50%;background:var(--accent);
  color:#fff;font-size:2.4cqh;font-weight:700;display:flex;align-items:center;justify-content:center}

.synth{display:grid;grid-template-columns:1.25fr 1fr;gap:3cqh;margin-top:2cqh;flex:1;min-height:0}
.synth ul{list-style:none;margin-top:1.8cqh;display:flex;flex-direction:column;gap:1.4cqh}
.synth ul li{font-size:2.9cqh;color:var(--text-dim);line-height:1.4;padding-left:2.6cqh;
  position:relative}
.synth ul li::before{content:"";position:absolute;left:0;top:1.4cqh;width:1.1cqh;height:1.1cqh;
  border-radius:50%;background:var(--accent-2)}
/* The prompt, ready to copy. This panel used to advertise an internal file
   format by name — "toasted skill", "brainstem" — to an audience that has
   never heard either word and does not need to. What they need is the thing
   they paste. */
.onefile{background:#070f26;border-radius:12px;padding:2.2cqh;display:flex;flex-direction:column;
  gap:1.2cqh;min-height:0}
.onefile .fname{display:flex;align-items:center;gap:1.2cqh;font-size:2.5cqh;font-weight:700;
  color:#fff}
.onefile .fname .cp{margin-left:auto;font-size:2.1cqh;font-weight:600;color:#070f26;
  background:#fff;border:0;border-radius:6px;padding:.7cqh 1.4cqh;cursor:pointer;
  font-family:inherit}
.onefile .fname .cp:hover{background:#e2669a;color:#fff}
.onefile pre{flex:1;min-height:0;overflow:auto;background:#0d1730;border:1px solid #2a3a66;
  border-radius:8px;padding:1.6cqh;color:#c7cbe6;font-family:Consolas,ui-monospace,monospace;
  font-size:1.95cqh;line-height:1.45;white-space:pre-wrap}

/* The architecture, drawn on the slide. It used to be a box saying the real
   one was on another page, which is not a slide — it is a note apologising for
   the absence of one, and it exported as an empty rectangle. */
.arch{display:grid;grid-template-columns:1fr 1.15fr 1.1fr .95fr;gap:1.2cqh;
  flex:1;min-height:0;margin-top:1.6cqh}
.arch .col{background:var(--panel-2);border:1px solid var(--border);border-radius:8px;
  padding:1.2cqh;display:flex;flex-direction:column;gap:.8cqh;min-height:0;overflow:hidden}
.arch .col h4{font-size:2.3cqh;font-weight:700;text-align:center;letter-spacing:-.01em;
  padding-bottom:.6cqh;border-bottom:1px solid var(--border)}
.arch .it{display:flex;gap:.9cqh;align-items:flex-start;background:var(--panel);
  border:1px solid var(--border);border-radius:6px;padding:.8cqh .9cqh;font-size:2.1cqh;
  line-height:1.3}
.arch .it img{width:2.8cqh;height:2.8cqh;object-fit:contain;flex:0 0 auto}
.arch .it .n{flex:0 0 auto;width:2.6cqh;height:2.6cqh;border-radius:50%;background:var(--accent);
  color:#fff;font-size:1.8cqh;font-weight:700;display:flex;align-items:center;
  justify-content:center}
.arch .note{font-size:1.95cqh;color:var(--text-faint);line-height:1.3}
.arch .orch{text-align:center;font-size:2.2cqh;font-weight:700;padding:.5cqh 0}
.arch .agents{display:flex;flex-direction:column;gap:.5cqh;min-height:0;overflow:hidden}
.arch .agents .a{display:flex;gap:.8cqh;align-items:baseline;font-size:2.05cqh;line-height:1.25}
/* Sub-steps of step 3, deliberately NOT the same badge as the flow numbers.
   Two independent sequences drawn in one visual language is why "3" appeared
   to mean two different things on the same slide. */
.arch .agents .a i{flex:0 0 auto;min-width:3.4cqh;font-style:normal;font-size:1.75cqh;
  font-weight:700;color:var(--accent);letter-spacing:-.02em;text-align:right}
.arch .agents .a b{font-weight:650}
.arch .gov{background:var(--gold-soft,rgba(184,145,45,.09));border:1px solid rgba(184,145,45,.35);
  border-radius:6px;padding:.8cqh .9cqh;font-size:2.05cqh;line-height:1.3}
.arch .gov b{display:block;font-size:2.15cqh}

.controls{display:flex;align-items:center;gap:14px;margin:14px 0 6px;flex-wrap:wrap}
.controls .pos{font-size:13px;color:var(--text-dim);font-variant-numeric:tabular-nums}
.controls .spacer{margin-left:auto}
.dots{display:flex;gap:6px;flex-wrap:wrap}
.dots button{width:9px;height:9px;padding:0;border-radius:50%;border:1px solid var(--border);
  background:var(--panel-2);cursor:pointer}
.dots button[aria-current=true]{background:var(--accent);border-color:var(--accent)}
.hint{font-size:12.5px;color:var(--text-faint);margin-bottom:34px}
@media (max-width:700px){
  .tiles{grid-auto-flow:row}
  .synth{grid-template-columns:1fr}
}
@media print{header.site,.controls,.actions,footer.site,.hint{display:none}
  body{background:#fff}.slide{display:flex!important;position:static;page-break-after:always}
  .stage{aspect-ratio:auto;height:auto;border:0;box-shadow:none}}
"""

BODY = """
<main class="wrap">
  <section class="head">
    <div>
      <div class="crumb" id="cCrumb">Configuration guide</div>
      <h1 id="cTitle">Configuration guide</h1>
      <p id="cLede"></p>
    </div>
    <div class="actions">
      <button class="btn primary" id="deckBtn">Export to PowerPoint</button>
      <a class="btn" id="archLink" href="#">Reference architecture</a>
      <a class="btn" id="solLink" href="#">The solution</a>
      <span class="deck-status" id="deckStatus"></span>
      <span class="exp-count" id="expCount"></span>
    </div>
  </section>

  <div class="controls">
    <button class="btn" id="prevBtn" aria-label="Previous slide">&larr; Back</button>
    <button class="btn" id="nextBtn" aria-label="Next slide">Next &rarr;</button>
    <span class="pos" id="pos"></span>
    <span class="spacer"></span>
    <div class="dots" id="dots" role="tablist" aria-label="Slides"></div>
  </div>

  <div class="stage" id="stage" tabindex="0" aria-live="polite"></div>
  <p class="hint">Use the arrow keys to move through the slides. Export takes the same
     slides away as a PowerPoint file you can edit and present yourself.</p>
  <p class="foot-note" id="cNote"></p>
</main>
"""

SCRIPT = r"""
<!-- The version stamp is not decoration. GitHub Pages serves these with a
     cache header, so without it a returning visitor keeps yesterday's deck.js
     against today's data — which fails silently, as a slide that renders
     through the wrong branch rather than an error anyone would notice. -->
<script src="vendor/jszip.min.js"></script>
<script src="vendor/pptxgen.min.js"></script>
<script src="export-signal.js?v=__BUILD__"></script>
<script src="deck.js?v=__BUILD__"></script>
<script>
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}

var GUIDE=null, PRODUCTS={products:[]}, ARCH=null, AT=0, MARKINDEX={};

function slug(){
  var m=/[?&]solution=([^&]+)/.exec(location.search);
  return m?decodeURIComponent(m[1]):"contract-review-agent";
}

/* A real mark when one exists, an initial chip when one does not. An
   approximated logo on a Microsoft page is worse than a word. */
function markOf(id){
  var l=PRODUCTS.products||[];
  for(var i=0;i<l.length;i++){ if(l[i].id===id && l[i].mark_status==="mark") return l[i].mark; }
  /* Not every mark belongs to a catalog product. GitHub Copilot is a harness,
     not an entry in the library, so the products list has no row for it and the
     title slide silently drew nothing. The marks index is the authority on what
     is on disk; the products list only says which of them a catalog entry uses. */
  var r=MARKINDEX[id];
  return r&&r.file?r.file:null;
}
function markTag(id,name,cls){
  var p=markOf(id);
  if(p) return '<img src="'+esc(p)+'" alt="'+esc(name)+'">';
  return '<span class="'+(cls||"chip")+'">'+esc(String(name).replace(/^Microsoft /,"").charAt(0))+'</span>';
}

var R={
  title:function(s){
    var harness=(s.harness||[]).map(function(h){
      var p=markOf(h.id);
      return p?'<div class="tm"><img src="'+esc(p)+'" alt="'+esc(h.name)+'"><span>'+
        esc(h.name)+'</span></div>':'';
    }).join("");
    return '<div class="rule"></div><div class="kick">'+esc(s.kicker||"")+'</div>'+
      '<h2>'+esc(s.title)+'</h2><div class="sub">'+esc(s.sub||"")+'</div>'+
      (harness?'<div class="titlemarks">'+harness+'</div>':"");
  },
  summary:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      '<div class="body">'+esc(s.body||"")+'</div><div class="sumgrid">'+
      (s.points||[]).map(function(p){
        return '<div class="col"><b>'+esc(p.lead)+'</b><span>'+esc(p.detail)+'</span></div>';
      }).join("")+'</div>';
  },
  statement:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      '<div class="body">'+esc(s.body||"")+'</div>'+
      ((s.tiles||[]).length?'<div class="tiles">'+(s.tiles||[]).map(function(t){
        return '<div class="tile"><div class="lab">'+esc(t.label)+'</div>'+
               '<div class="val">'+esc(t.value)+'</div></div>';}).join("")+'</div>':"");
  },
  products:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      (s.body?'<div class="body">'+esc(s.body)+'</div>':"")+
      '<div class="prows">'+(s.rows||[]).map(function(r){
        return '<div class="prow">'+markTag(r.id,r.product)+
          '<div><b>'+esc(r.product)+'</b><span>'+esc(r.role)+'</span></div></div>';
      }).join("")+'</div>';
  },
  adventure:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      (s.body?'<div class="body">'+esc(s.body)+'</div>':"")+
      '<table class="adv"><thead><tr><th>The need</th>'+
      '<th>If you already run something else</th><th>The Microsoft path</th></tr></thead><tbody>'+
      (s.rows||[]).map(function(r){
        return '<tr><td>'+esc(r.need)+'</td>'+
          '<td><b>'+esc(r.outside)+'</b><small>'+esc(r.outside_how)+'</small></td>'+
          '<td><div class="with">'+markTag(r.microsoft_id,r.microsoft,"chip")+
          '<div><b>'+esc(r.microsoft)+'</b><small>'+esc(r.why)+'</small></div></div></td></tr>';
      }).join("")+'</tbody></table>';
  },
  steps:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      (s.body?'<div class="body">'+esc(s.body)+'</div>':"")+
      '<ol class="steps">'+(s.steps||[]).map(function(t,i){
        return '<li><span class="n">'+(i+1)+'</span><span>'+esc(t)+'</span></li>';
      }).join("")+'</ol>';
  },
  synthetic:function(s){
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      '<div class="synth"><div><div class="body">'+esc(s.body||"")+'</div><ul>'+
      (s.points||[]).map(function(p){return "<li>"+esc(p)+"</li>";}).join("")+
      '</ul></div><div class="onefile">'+
      '<div class="fname">'+esc(s.prompt_title||"Paste this into Copilot")+
        '<button class="cp" data-copy="1">Copy</button></div>'+
      '<pre>'+esc(s.prompt||"")+'</pre></div></div>';
  },
  architecture:function(s){
    if(!ARCH){
      return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
        '<div class="body">No generated architecture is on file for this solution yet.</div>';
    }
    var c=ARCH.columns, K=c.knowledge||{}, P=c.processing||{},
        U=c.interface||{}, Rp=c.reporting||{};
    function it(x,n){
      var m=x&&x.mark?'<img src="'+esc(x.mark)+'" alt="'+esc(x.label)+'">':'';
      return '<div class="it">'+(n?'<span class="n">'+n+'</span>':m)+
        '<span>'+esc(x&&x.label?x.label:x)+'</span></div>';
    }
    var agents=(P.agents||[]);
    var flow1=(ARCH.flow&&ARCH.flow[0]&&ARCH.flow[0].text)||"Natural language input";
    return '<div class="kick">'+esc(s.kicker||"")+'</div><h2>'+esc(s.title)+'</h2>'+
      (s.note?'<div class="body" style="font-size:2.6cqh;margin-top:1cqh">'+esc(s.note)+'</div>':"")+
      '<div class="arch">'+
        '<div class="col"><h4>'+esc(K.title||"Knowledge")+'</h4>'+
          (K.grounding||[]).slice(0,4).map(function(x){return it(x);}).join("")+
          '<div class="note">'+esc(K.note||"")+'</div>'+
          it({label:(ARCH.flow&&ARCH.flow[4]?ARCH.flow[4].text:"Action taken in the system of record")},5)+
        '</div>'+
        '<div class="col"><h4>'+esc(P.title||"Processing")+'</h4>'+
          it({label:(ARCH.flow&&ARCH.flow[2]?"Formulates a plan across the agents below":"Formulates a plan")},3)+
          '<div class="orch">'+esc(P.orchestration||"Multi-agent orchestration")+'</div>'+
          '<div class="agents">'+(agents.length
            ? agents.map(function(a,i){return '<div class="a"><i>3.'+(i+1)+'</i>'+
                '<span><b>'+esc(a.name)+'</b> — '+esc(a.does)+'</span></div>';}).join("")
            : (P.actions||[]).slice(0,6).map(function(a,i){return '<div class="a"><i>3.'+(i+1)+
                '</i><span>'+esc(a)+'</span></div>';}).join(""))+
          '</div>'+
          it({label:(ARCH.flow&&ARCH.flow[3]?ARCH.flow[3].text:"NL response after guideline checks")},4)+
        '</div>'+
        '<div class="col"><h4>'+esc(U.title||"User Interface")+'</h4>'+
          (U.surfaces||[]).slice(0,3).map(function(x){return it(x);}).join("")+
          it({label:flow1},1)+
          it({label:U.checks||""},2)+
          it({label:"Feedback"},6)+
        '</div>'+
        '<div class="col"><h4>'+esc(Rp.title||"Reporting")+'</h4>'+
          '<div class="gov"><b>Governance, risk &amp; compliance</b>'+esc(Rp.governance||"")+'</div>'+
          (Rp.systems||[]).slice(0,2).map(function(x){return it(x);}).join("")+
          '<div class="gov"><b>Insights</b>'+esc(Rp.insights||"")+'</div>'+
        '</div>'+
      '</div>';
  },
  close:function(s){
    return '<h2>'+esc(s.title)+'</h2><div class="sub">'+esc(s.sub||"")+'</div>';
  }
};

function render(){
  var stage=document.getElementById("stage"), dots=document.getElementById("dots");
  stage.innerHTML=(GUIDE.slides||[]).map(function(s,i){
    var fn=R[s.kind]||R.statement;
    var dark=(s.kind==="title"||s.kind==="close");
    var tw=s.takeaway?'<div class="takeaway"><b>So what</b><span>'+esc(s.takeaway)+'</span></div>':"";
    return '<section class="slide'+(dark?" dark":"")+(i===0?" on":"")+'" data-i="'+i+'" '+
      'role="tabpanel" aria-label="Slide '+(i+1)+'">'+fn(s)+tw+'</section>';
  }).join("");
  dots.innerHTML=(GUIDE.slides||[]).map(function(s,i){
    return '<button role="tab" data-i="'+i+'" aria-current="'+(i===0)+'" '+
      'title="'+esc(s.title||("Slide "+(i+1)))+'"></button>';
  }).join("");
  dots.onclick=function(e){ var b=e.target.closest("button"); if(b) go(+b.dataset.i); };
  go(0);
}

function go(i){
  var n=(GUIDE.slides||[]).length; if(!n) return;
  AT=Math.max(0,Math.min(n-1,i));
  Array.prototype.forEach.call(document.querySelectorAll(".slide"),function(el){
    el.classList.toggle("on",+el.dataset.i===AT); });
  Array.prototype.forEach.call(document.querySelectorAll(".dots button"),function(el){
    el.setAttribute("aria-current",String(+el.dataset.i===AT)); });
  document.getElementById("pos").textContent=(AT+1)+" / "+n;
  document.getElementById("prevBtn").disabled=AT===0;
  document.getElementById("nextBtn").disabled=AT===n-1;
}

/* Copy the prompt. The whole point of the slide is that they leave with it. */
document.addEventListener("click",function(e){
  var b=e.target.closest("[data-copy]"); if(!b) return;
  var pre=b.closest(".onefile").querySelector("pre");
  navigator.clipboard.writeText(pre.textContent).then(function(){
    var t=b.textContent; b.textContent="Copied"; setTimeout(function(){b.textContent=t;},1600);
  }).catch(function(){ b.textContent="Select and copy"; });
});

document.getElementById("prevBtn").onclick=function(){go(AT-1);};
document.getElementById("nextBtn").onclick=function(){go(AT+1);};
document.addEventListener("keydown",function(e){
  if(e.target.matches("input,textarea")) return;
  if(e.key==="ArrowRight"||e.key==="PageDown"){go(AT+1);e.preventDefault();}
  if(e.key==="ArrowLeft"||e.key==="PageUp"){go(AT-1);e.preventDefault();}
});

/* The deck is built from the same object this page rendered from, so a slide
   on screen and a slide in the file cannot disagree. */
document.getElementById("deckBtn").onclick=function(){
  var btn=this, st=document.getElementById("deckStatus");
  var say=function(m){ st.textContent=m; };
  if(!GUIDE){ say("Guide not loaded yet."); return; }
  btn.disabled=true;
  RappDeck.exportConfigGuide({guide:GUIDE, arch:ARCH, onStatus:say})
    .catch(function(){})
    .then(function(){ btn.disabled=false;
      if(window.RappExport) RappExport.label(document.getElementById("expCount"),GUIDE.slug);
    });
};

var s=slug();
Promise.all([
  fetch("api/v1/config-guides/"+s+".json",{cache:"no-cache"})
    .then(function(r){ return r.ok?r.json():fetch("data/config_guides/"+s+".json")
      .then(function(x){return x.json();}); }),
  fetch("data/products.json",{cache:"no-cache"}).then(function(r){return r.ok?r.json():null;})
    .catch(function(){return null;}),
  fetch("data/architectures.json",{cache:"no-cache"}).then(function(r){return r.ok?r.json():null;})
    .catch(function(){return null;}),
  fetch("assets/products/index.json",{cache:"no-cache"}).then(function(r){return r.ok?r.json():null;})
    .catch(function(){return null;})
]).then(function(r){
  GUIDE=r[0]; PRODUCTS=r[1]||{products:[]}; MARKINDEX=(r[3]&&r[3].marks)||{};
  ARCH=((r[2]&&r[2].architectures)||[]).filter(function(a){return a.slug===GUIDE.slug;})[0]||null;
  document.title=GUIDE.display_name+" — configuration guide — AIBAST Agent Library";
  document.getElementById("cCrumb").textContent=
    "Configuration guide · "+(GUIDE.industries||[]).join(" · ");
  document.getElementById("cTitle").textContent=GUIDE.display_name;
  document.getElementById("cLede").textContent=GUIDE.lede||"";
  document.getElementById("cNote").textContent=GUIDE.note||"";
  document.getElementById("archLink").href="architecture.html?solution="+encodeURIComponent(GUIDE.slug);
  document.getElementById("solLink").href="onepager.html?solution="+encodeURIComponent(GUIDE.slug);
  render();
  if(window.RappExport) RappExport.label(document.getElementById("expCount"),GUIDE.slug);
}).catch(function(){
  document.getElementById("stage").innerHTML=
    '<section class="slide on"><div class="body">No configuration guide is published for '+
    esc(s)+' yet.</div></section>';
});

/* Shared theme toggle — same behaviour on every page. */
(function(){
  var k="aibast:theme", b=document.getElementById("themeToggle");
  var t=localStorage.getItem(k)||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
  document.documentElement.setAttribute("data-theme",t);
  if(b) b.onclick=function(){
    t=(document.documentElement.getAttribute("data-theme")==="dark")?"light":"dark";
    document.documentElement.setAttribute("data-theme",t);
    localStorage.setItem(k,t);
  };
})();
</script>
</body>
</html>
"""

BUILD = subprocess.run(["git","-C",str(ROOT),"rev-parse","--short","HEAD"],
                       capture_output=True, text=True).stdout.strip() or "dev"
SCRIPT = SCRIPT.replace("__BUILD__", BUILD)

html = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Configuration guide — AIBAST Agent Library</title>\n'
        '<meta name="description" content="How to configure an industry solution on the '
        'Copilot Studio and GitHub Copilot harness: the Microsoft path end to end, the '
        'alternatives where another system is already in place, and synthetic data to '
        'demo on. Slides, exportable to PowerPoint.">\n'
        '<style>\n' + CSS + PAGE_CSS + '</style>\n</head>\n<body>\n'
        + HEADER + '\n' + BODY + '\n' + FOOTER + '\n' + SCRIPT)

(ROOT / "config.html").write_text(html, encoding="utf-8")
print("config.html", len(html), "bytes")
