/* app.js — navegacion por pestañas y render de modulos (MVP) */
const CALI_CENTER=[3.42,-76.53], VALLE_CENTER=[3.9,-76.4];
const inited={};

function tabButtons(){
  document.querySelectorAll("#tabs button").forEach(b=>{
    b.onclick=()=>{
      document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(x=>x.classList.remove("active"));
      b.classList.add("active");
      document.getElementById("tab-"+b.dataset.tab).classList.add("active");
      render(b.dataset.tab);
    };
  });
}

// ---- controles de segmento reutilizables ----
function segControls(container, rows, opts, onChange){
  container.innerHTML="";
  const corps = opts.corps || [...new Set(rows.map(r=>r.corporacion))];
  const sCorp=mkControl(container,"Corporación","c-corp");
  fillSelect(sCorp,corps);
  const sVue=mkControl(container,"Vuelta","c-vue");
  const sCir=mkControl(container,"Circunscripción","c-cir");
  function refresh(){
    const corp=sCorp.value;
    const vs=[...new Set(rows.filter(r=>r.corporacion===corp).map(r=>String(r.vuelta)))];
    fillSelect(sVue,vs); 
    const cirs=[...new Set(rows.filter(r=>r.corporacion===corp&&String(r.vuelta)===sVue.value)
      .map(r=>String(r.circunscripcion)))];
    fillSelect(sCir,cirs);
    onChange({corp,vuelta:sVue.value,cir:sCir.value});
  }
  sCorp.onchange=refresh; sVue.onchange=()=>{ 
    const corp=sCorp.value;
    const cirs=[...new Set(rows.filter(r=>r.corporacion===corp&&String(r.vuelta)===sVue.value)
      .map(r=>String(r.circunscripcion)))];
    fillSelect(sCir,cirs); onChange({corp,vuelta:sVue.value,cir:sCir.value});
  };
  sCir.onchange=()=>onChange({corp:sCorp.value,vuelta:sVue.value,cir:sCir.value});
  refresh();
}

function kpis(el, items){
  el.innerHTML=items.map(i=>`<div class="kpi"><div class="v">${i.v}</div><div class="l">${i.l}</div></div>`).join("");
}
function table(el, cols, rows){
  const h="<tr>"+cols.map(c=>`<th class="${c.num?'num':''}">${c.t}</th>`).join("")+"</tr>";
  const b=rows.map(r=>"<tr>"+cols.map(c=>`<td class="${c.num?'num':''}">${c.f(r)}</td>`).join("")+"</tr>").join("");
  el.innerHTML=`<table>${h}${b}</table>`;
}

// =================== PANORAMA VALLE ===================
async function renderValle(){
  const comp=await load("valle/competencia.json");
  const res=await load("valle/resultados.json");
  const muni=await load("municipio/competencia.json");
  segControls(document.getElementById("ctrl-valle"),comp,{},({corp,vuelta,cir})=>{
    setContext(corp,vuelta,cir);
    const cv=seg(comp,corp,vuelta,cir)[0];
    if(cv) kpis(document.getElementById("kpi-valle"),[
      {v:cv.ganador||"—",l:"1º lugar"},
      {v:pct(cv.top1_pp),l:"% del ganador (válidos)"},
      {v:pct(cv.margen_pp),l:"margen 1º–2º"},
      {v:dec(cv.nep,2),l:"núm. efectivo (NEP)"},
      {v:fmt(cv.total_marcas),l:"total marcas"}]);
    // mapa municipal
    const mrows=seg(muni,corp,vuelta,cir);
    const win={}; mrows.forEach(r=>win[String(r.dane_codigo)]=r);
    loadGeo("valle_municipios.geojson").then(g=>
      choropleth("map-valle",VALLE_CENTER,8,g,"MPIO_CDPMP",win,corp,vuelta));
    document.getElementById("map-valle-note").textContent=
      "Color = candidato/lista ganador por municipio.";
    // ranking
    const rk=[...mrows].sort((a,b)=>b.top1_pp-a.top1_pp);
    table(document.getElementById("rank-valle"),
      [{t:"Municipio",f:r=>r.municipio},{t:"Ganador",f:r=>r.ganador},
       {t:"%",num:1,f:r=>pct(r.top1_pp)},{t:"Margen pp",num:1,f:r=>pct(r.margen_pp)}],rk);
    // barra departamental
    const rv=seg(res,corp,vuelta,cir);
    barUnits("bar-valle",rv,corp,vuelta,{top:15});
    renderLegend("leg-valle",corp,vuelta,rv.map(r=>r.unidad));
  });
}

// =================== PRESIDENCIA ===================
async function renderPres(){
  const comp=(await load("valle/competencia.json")).filter(r=>r.corporacion==="Presidencia");
  const res=await load("valle/resultados.json");
  const muni=await load("municipio/competencia.json");
  const chg=await load("cambio/municipio.json");
  segControls(document.getElementById("ctrl-pres"),comp,{corps:["Presidencia"]},
    ({corp,vuelta,cir})=>{
    setContext(corp,vuelta,cir);
    const cv=seg(comp,corp,vuelta,cir)[0];
    if(cv) kpis(document.getElementById("kpi-pres"),[
      {v:cv.ganador,l:"1º lugar"},{v:pct(cv.top1_pp),l:"% ganador"},
      {v:pct(cv.margen_pp),l:"margen"},{v:fmt(cv.total_marcas),l:"total marcas"}]);
    const rp=seg(res,corp,vuelta,cir);
    barUnits("bar-pres",rp,corp,vuelta);
    renderLegend("leg-pres",corp,vuelta,rp.map(r=>r.unidad));
    barChange("chg-pres",chg);
    const win={}; seg(muni,"Presidencia",vuelta,cir).forEach(r=>win[String(r.dane_codigo)]=r);
    loadGeo("valle_municipios.geojson").then(g=>
      choropleth("map-pres",VALLE_CENTER,8,g,"MPIO_CDPMP",win,"Presidencia",vuelta));
  });
}

// =================== CONGRESO ===================
async function renderCong(){
  const comp=(await load("valle/competencia.json")).filter(r=>r.corporacion!=="Presidencia");
  const res=await load("valle/resultados.json");
  const muni=await load("municipio/competencia.json");
  segControls(document.getElementById("ctrl-cong"),comp,
    {corps:["Senado","Cámara","Consultas"]},({corp,vuelta,cir})=>{
    setContext(corp,vuelta,cir);
    const cv=seg(comp,corp,vuelta,cir)[0];
    if(cv){
      kpis(document.getElementById("kpi-cong"),[
        {v:cv.ganador,l:"1ª lista"},{v:pct(cv.top1_pp),l:"% lista líder"},
        {v:dec(cv.hhi,3),l:"HHI"},{v:dec(cv.nep,2),l:"NEP"},
        {v:fmt(cv.total_marcas),l:"total marcas"}]);
      table(document.getElementById("frag-cong"),
        [{t:"Indicador",f:r=>r.k},{t:"Valor",num:1,f:r=>r.v}],
        [{k:"Listas efectivas (NEP)",v:dec(cv.nep,2)},{k:"HHI",v:dec(cv.hhi,3)},
         {k:"Fragmentación",v:dec(cv.fragmentacion,3)},{k:"% en blanco",v:pct(cv.blanco_pp)},
         {k:"Nº listas",v:fmt(cv.n_unidades)}]);
    }
    const rc=seg(res,corp,vuelta,cir);
    barUnits("bar-cong",rc,corp,vuelta,{top:15});
    renderLegend("leg-cong",corp,vuelta,rc.map(r=>r.unidad).slice(-15));
    const mr=seg(muni,corp,vuelta,cir).sort((a,b)=>b.top1_pp-a.top1_pp);
    table(document.getElementById("rank-cong"),
      [{t:"Municipio",f:r=>r.municipio},{t:"Lista ganadora",f:r=>r.ganador},
       {t:"%",num:1,f:r=>pct(r.top1_pp)}],mr);
  });
}

// =================== CALI ===================
async function renderCali(){
  document.getElementById("cali-warn").textContent=
    "Aviso: 102 puestos presentan conflicto entre la comuna del rótulo electoral y la comuna geográfica (REQUIERE_VALIDACION). El mapa por comuna usa la etiqueta electoral y debe validarse con DIVIPOL.";
  const comp=await load("cali/comuna_competencia.json");
  const res=await load("cali/comuna_resultados.json");
  segControls(document.getElementById("ctrl-cali"),comp,{},({corp,vuelta,cir})=>{
    setContext(corp,vuelta,cir);
    const rows=seg(comp,corp,vuelta,cir);
    const win={}; rows.forEach(r=>win[r.territorio_nombre]=r);
    renderLegend("leg-cali",corp,vuelta,rows.map(r=>r.ganador));
    loadGeo("cali_comunas.geojson").then(g=>
      choropleth("map-cali",CALI_CENTER,11,g,"nombre",win,corp,vuelta));
    const rk=[...rows].sort((a,b)=>b.top1_pp-a.top1_pp);
    table(document.getElementById("rank-cali"),
      [{t:"Comuna",f:r=>r.territorio_nombre},{t:"Ganador",f:r=>r.ganador},
       {t:"%",num:1,f:r=>pct(r.top1_pp)},{t:"NEP",num:1,f:r=>dec(r.nep,2)}],rk);
    // barra: sumar comunas por unidad
    const rr=seg(res,corp,vuelta,cir); const by={};
    rr.forEach(r=>{if(r.unidad){by[r.unidad]=(by[r.unidad]||0)+r.votos;}});
    const agg=Object.entries(by).map(([unidad,votos])=>({unidad,votos,pct_validos:null}));
    barUnits("bar-cali",agg,corp,vuelta,{top:15});
  });
}

// =================== EXPLORADOR ===================
async function renderExp(){
  const muni=await load("municipio/competencia.json");
  const munis=[...new Map(muni.map(r=>[r.dane_codigo,r.municipio])).entries()]
    .map(([v,t])=>({v,t})).sort((a,b)=>a.t.localeCompare(b.t));
  const cont=document.getElementById("ctrl-exp"); cont.innerHTML="";
  const sM=mkControl(cont,"Municipio","e-m"); fillSelect(sM,munis);
  const sZ=mkControl(cont,"Zona","e-z");
  const sP=mkControl(cont,"Puesto","e-p");
  const sMe=mkControl(cont,"Mesa","e-me");
  let estruct=null;
  async function onM(){ if(!sM.value){return;} estruct=await load("estructura/"+sM.value+".json");
    fillSelect(sZ,Object.keys(estruct.zonas).sort()); onZ(); }
  function onZ(){ if(!estruct||!sZ.value){return;} const z=estruct.zonas[sZ.value]||{};
    fillSelect(sP,Object.keys(z).sort().map(p=>({v:p,t:p+" — "+z[p].n}))); onP(); }
  function onP(){ if(!estruct||!sZ.value){return;} const z=estruct.zonas[sZ.value]||{};
    const mesas=(z[sP.value]&&z[sP.value].mesas)||[];
    fillSelect(sMe,mesas); showMesa(); }
  async function showMesa(){
    if(!sM.value||!sZ.value||!sP.value||!sMe.value){return;}
    const d=await load("mesa/"+sM.value+"_"+sZ.value+".json");
    const out=document.getElementById("exp-result");
    const rowsAll=[];
    Object.keys(d.votos).forEach(k=>{
      const [p,m,corp]=k.split("|");
      if(p!==sP.value||m!==sMe.value) return;
      const uni=CAT[corp]?CAT[corp].unidades:[];
      Object.entries(d.votos[k]).forEach(([idx,v])=>
        rowsAll.push({corp,unidad:uni[+idx]||("#"+idx),votos:v}));
      const e=d.especiales[k]||{};
      Object.entries(e).forEach(([t,v])=>rowsAll.push({corp,unidad:"("+t+")",votos:v}));
    });
    rowsAll.sort((a,b)=>a.corp.localeCompare(b.corp)||b.votos-a.votos);
    if(!rowsAll.length){ out.innerHTML='<p class="note">Sin datos para esa mesa.</p>'; return; }
    table(out,[{t:"Corp.",f:r=>r.corp},{t:"Unidad",f:r=>r.unidad},
      {t:"Votos",num:1,f:r=>fmt(r.votos)}],rowsAll);
  }
  sM.onchange=onM; sZ.onchange=onZ; sP.onchange=onP; sMe.onchange=showMesa;
  await onM();
}

// =================== LECTURA ANALÍTICA (descriptiva) ===================
function clasifMargen(pp){ if(pp==null||isNaN(pp)) return "no determinada";
  if(pp<5) return "muy estrecha (competitiva)"; if(pp<10) return "estrecha";
  if(pp<20) return "moderada"; return "amplia"; }
function clasifNEP(n){ if(n==null||isNaN(n)) return "no determinado";
  if(n<2.5) return "concentrado (pocas fuerzas efectivas)"; if(n<4) return "moderadamente fragmentado";
  return "muy fragmentado (muchas fuerzas efectivas)"; }

async function renderLectura(){
  const comp=await load("valle/competencia.json");
  const muni=await load("municipio/competencia.json");
  const comu=await load("cali/comuna_competencia.json");
  // guía estática (metodológica, descriptiva)
  document.getElementById("lect-guia").innerHTML=`
    <h4>Qué mide cada indicador</h4>
    <ul>
      <li><b>% del ganador (sobre válidos):</b> peso de la primera fuerza. Alto = predominio; bajo = territorio disputado.</li>
      <li><b>Margen 1º–2º (pp):</b> distancia entre las dos primeras fuerzas. &lt;5 pp = muy competitivo; &gt;20 pp = holgado.</li>
      <li><b>HHI (0–1):</b> concentración del voto. Cercano a 1 = concentrado en pocas fuerzas; cercano a 0 = repartido.</li>
      <li><b>NEP (nº efectivo de listas):</b> cuántas fuerzas “cuentan” de verdad. Bajo = pocas; alto = muchas.</li>
      <li><b>% en blanco:</b> señal de inconformidad/indecisión agregada, no de intención individual.</li>
    </ul>
    <h4>Cómo usarlo en la discusión estratégica</h4>
    <ul>
      <li>Priorizar el análisis por <b>competitividad</b> (margen) y <b>estructura</b> (NEP/HHI) del territorio, no por rasgos de las personas.</li>
      <li>Comparar cada territorio con el <b>promedio departamental</b> para ubicar dónde el resultado es atípico y merece estudio adicional.</li>
      <li>Leer el cambio 1V→2V como <b>desplazamiento agregado</b> del resultado, nunca como transferencia individual de votos.</li>
    </ul>
    <h4>Límites (no hace)</h4>
    <ul>
      <li>No infiere el voto ni el perfil de personas (falacia ecológica).</li>
      <li>No sugiere mensajes dirigidos a comunidades concretas ni microtargeting.</li>
      <li>No afirma causas: una diferencia territorial no explica por sí sola el porqué.</li>
    </ul>
    <p class="note">Marca IMPACTO · <span class="hand">La gente primero, ¡siempre!</span> — El dato es el protagonista; las decisiones son del equipo.</p>`;

  // controles: corporación/vuelta/cir + nivel + territorio
  const cont=document.getElementById("ctrl-lect");
  let sNivel, sTerr;
  function terrList(){
    const s=window._lectSeg||{}; const niv=sNivel?sNivel.value:"valle";
    if(niv==="valle") return [{v:"VALLE DEL CAUCA",t:"Valle del Cauca"}];
    if(niv==="municipio") return seg(muni,s.corp,s.vuelta,s.cir)
      .map(r=>({v:r.dane_codigo,t:r.municipio})).sort((a,b)=>a.t.localeCompare(b.t));
    return seg(comu,s.corp,s.vuelta,s.cir).map(r=>({v:r.territorio_nombre,t:r.territorio_nombre}))
      .sort((a,b)=>a.t.localeCompare(b.t));
  }
  function refreshTerr(){ if(!sTerr) return; fillSelect(sTerr,terrList()); }
  // segControls limpia el contenedor y dispara onChange: por eso va primero,
  // y Nivel/Territorio se crean DESPUÉS (con guardas para el disparo inicial).
  segControls(cont,comp,{},({corp,vuelta,cir})=>{ window._lectSeg={corp,vuelta,cir}; refreshTerr(); });
  sNivel=mkControl(cont,"Nivel","l-niv"); fillSelect(sNivel,[
    {v:"valle",t:"Valle (departamento)"},{v:"municipio",t:"Municipio"},{v:"comuna",t:"Comuna (Cali)"}]);
  sTerr=mkControl(cont,"Territorio","l-terr");
  sNivel.onchange=refreshTerr; refreshTerr();

  document.getElementById("btn-lectura").onclick=()=>{
    const s=window._lectSeg||{}; const niv=sNivel.value; const key=sTerr.value;
    let row, nombre, prom;
    const segRows=(rows)=>seg(rows,s.corp,s.vuelta,s.cir);
    if(niv==="valle"){ row=segRows(comp)[0]; nombre="Valle del Cauca"; prom=row; }
    else if(niv==="municipio"){ const rs=segRows(muni); row=rs.find(r=>r.dane_codigo===key);
      nombre=row?row.municipio:key; prom=segRows(comp)[0]; }
    else { const rs=segRows(comu); row=rs.find(r=>r.territorio_nombre===key);
      nombre=key; prom=avgComp(rs); }
    render(row,nombre,prom,s);
  };
  function avgComp(rs){ if(!rs.length) return null;
    const m=(f)=>rs.reduce((a,r)=>a+(r[f]||0),0)/rs.length;
    return {top1_pp:m("top1_pp"),margen_pp:m("margen_pp"),hhi:m("hhi"),nep:m("nep")}; }

  function render(row,nombre,prom,s){
    const t=document.getElementById("lect-title");
    const out=document.getElementById("lect-out");
    if(!row){ t.textContent=nombre||"—"; out.innerHTML='<p class="note">Sin datos para esta combinación.</p>'; return; }
    const corpTxt=s.corp+(s.corp==="Presidencia"?" ("+(VUELTA_TXT[s.vuelta]||s.vuelta)+")":"")+" · circ. "+s.cir;
    t.textContent=nombre+" — "+corpTxt;
    const cmpNep = prom&&prom.nep? (row.nep>prom.nep?"más fragmentado":"menos fragmentado")+" que el promedio":"";
    const cmpMar = prom&&prom.margen_pp!=null? (row.margen_pp<prom.margen_pp?"más competitivo":"menos competitivo")+" que el promedio":"";
    const items=[
      {tag:"hecho",txt:`En ${nombre}, la primera fuerza fue <b>${row.ganador}</b> con ${fmt(row.votos_ganador)} votos; la segunda, ${row.segundo||"—"} con ${fmt(row.votos_segundo)}. Total de marcas: ${fmt(row.total_marcas)}; válidos: ${fmt(row.validos)}.`},
      {tag:"indicador",txt:`% del ganador (válidos): <b>${pct(row.top1_pp)}</b> · margen 1º–2º: <b>${pct(row.margen_pp)}</b> · HHI: <b>${dec(row.hhi,3)}</b> · NEP: <b>${dec(row.nep,2)}</b> · % en blanco: ${pct(row.blanco_pp)}.`},
      {tag:"lectura",txt:`La competencia entre las dos primeras fuerzas es <b>${clasifMargen(row.margen_pp)}</b>. La estructura de competencia es <b>${clasifNEP(row.nep)}</b>${cmpNep?` — ${cmpNep} departamental`:""}${cmpMar?`; en competitividad, ${cmpMar} departamental`:""}. Lectura descriptiva y agregada; no implica causas ni comportamiento individual.`}
    ];
    out.innerHTML=items.map(i=>`<div class="lectura-item"><span class="tag ${i.tag}">${i.tag}</span><p>${i.txt}</p></div>`).join("");
  }
}

// =================== SOBRE LOS DATOS ===================
function renderDatos(){
  const m=MAN; const el=document.getElementById("datos-info");
  el.innerHTML=`<p><b>Fuente:</b> ${m.fuente}</p>
    <p><b>Cobertura:</b> ${m.cobertura}</p>
    <p><b>Elecciones:</b> ${m.elecciones.join(", ")}</p>
    <p><b>Niveles:</b> ${m.niveles.join(", ")}</p>
    <p><b>Generado:</b> ${m.generado} · ${m.archivos.length} archivos · ${(m.total_bytes/1e6).toFixed(1)} MB</p>
    <h4>Advertencias</h4><ul>${m.advertencias.map(a=>`<li>${a}</li>`).join("")}</ul>
    <p class="note">Los resultados representan información electoral agregada. Las diferencias territoriales no permiten inferir el comportamiento individual de los electores ni relaciones causales sin análisis adicional.</p>`;
}

// ---- dispatcher ----
function render(tab){
  const map={valle:renderValle,presidencia:renderPres,congreso:renderCong,
    cali:renderCali,explorador:renderExp,lectura:renderLectura,datos:renderDatos};
  if(inited[tab]) { if(tab==="datos") renderDatos(); return; }
  inited[tab]=true;
  try{ map[tab](); }catch(e){ console.error(e); alert("Error en módulo "+tab+": "+e.message); }
}

(async function(){
  try{
    await boot();
    document.getElementById("foot-text").textContent=
      "Fuente: "+MAN.fuente+" · Generado "+MAN.generado+" · Datos agregados, uso descriptivo.";
    tabButtons(); render("valle");
  }catch(e){ console.error(e);
    document.getElementById("foot-text").textContent="Error al iniciar: "+e.message; }
})();
