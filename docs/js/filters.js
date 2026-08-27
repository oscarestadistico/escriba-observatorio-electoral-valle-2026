/* filters.js — carga perezosa con cache, catalogo, utilidades de formato */
const DATA = "data/", GEO = "geo/";
const _cache = {};
let _pending = 0;
function _busy(on){
  const b=document.getElementById("loadbar"); if(!b) return;
  _pending += on?1:-1;
  if(_pending>0){ b.classList.add("on"); b.style.width="70%"; }
  else{ _pending=0; b.style.width="100%";
    setTimeout(()=>{b.classList.remove("on");b.style.width="0";},250); }
}
async function load(rel){
  if(_cache[rel]) return _cache[rel];
  _busy(true);
  try{
    const r = await fetch(DATA+rel);
    if(!r.ok) throw new Error("No se pudo cargar "+rel+" ("+r.status+")");
    const j = await r.json(); _cache[rel]=j; return j;
  } finally { _busy(false); }
}
async function loadGeo(name){
  const k="geo:"+name;
  if(_cache[k]) return _cache[k];
  const r = await fetch(GEO+name);
  if(!r.ok) throw new Error("No se pudo cargar geo "+name);
  const j = await r.json(); _cache[k]=j; return j;
}

let CAT=null, MAN=null;
async function boot(){ MAN=await load("manifest.json"); CAT=await load("catalogo.json"); }

const fmt = n => (n==null||isNaN(n))?"—":Number(n).toLocaleString("es-CO");
const pct = n => (n==null||isNaN(n))?"—":Number(n).toFixed(1)+"%";
const dec = (n,d=3) => (n==null||isNaN(n))?"—":Number(n).toFixed(d);
const corpCode = (corp,vuelta)=>({
  "Presidencia|1V":"PRE1","Presidencia|2V":"PRE2","Senado|NA":"SEN",
  "Cámara|NA":"CAM","Consultas|NA":"CON"}[corp+"|"+vuelta]);
function colorFor(corp,vuelta,unidad){
  const c=corpCode(corp,vuelta); const cc=CAT[c]&&CAT[c].colores[unidad];
  return cc||"#888";
}
// filtra registros por segmento
const seg = (rows,corp,vuelta,cir)=>rows.filter(r=>
  r.corporacion===corp && String(r.vuelta)===String(vuelta) &&
  String(r.circunscripcion)===String(cir));

// construye un <select>
function fillSelect(el,opts,val){
  el.innerHTML="";
  opts.forEach(o=>{const op=document.createElement("option");
    op.value=(typeof o==="object")?o.v:o; op.textContent=(typeof o==="object")?o.t:o;
    el.appendChild(op);});
  if(val!=null) el.value=val;
}
function mkControl(parent,label,id){
  const w=document.createElement("label"); w.textContent=label;
  const s=document.createElement("select"); s.id=id; w.appendChild(s);
  parent.appendChild(w); return s;
}

// --- barra de contexto trazable (firma) ---
const VUELTA_TXT={"1V":"1ª vuelta","2V":"2ª vuelta","NA":"única"};
function segLabel(corp,vuelta,cir){
  const v=VUELTA_TXT[vuelta]||vuelta;
  const parts=[corp];
  if(corp==="Presidencia") parts.push(v);
  parts.push("circ. "+cir);
  return parts.join("  ·  ");
}
function setContext(corp,vuelta,cir){
  const el=document.getElementById("ctx"); if(el) el.textContent=segLabel(corp,vuelta,cir);
}

// --- leyenda de color a partir del catalogo ---
function renderLegend(elId, corp, vuelta, units){
  const el=document.getElementById(elId); if(!el) return;
  const seen=new Set(); const items=[];
  units.forEach(u=>{ if(!u||seen.has(u)||/BLANCO|NULOS|NO MARCADOS/.test(u)) return;
    seen.add(u);
    items.push(`<span class="item"><span class="swatch" style="background:${colorFor(corp,vuelta,u)}"></span>${u}</span>`);
  });
  el.innerHTML=items.join("");
}
