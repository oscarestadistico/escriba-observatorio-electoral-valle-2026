/* charts.js — helpers Plotly (barras horizontales, cambio) */
const PLOT_CFG={displayModeBar:false,responsive:true};
const PLOT_LAY={margin:{l:170,r:18,t:8,b:36},
  font:{family:"Inter, system-ui",size:12,color:"#0f1620"},
  paper_bgcolor:"transparent",plot_bgcolor:"transparent",
  xaxis:{gridcolor:"#eef1f6",zerolinecolor:"#e5e9f0",tickfont:{family:"IBM Plex Mono"}},
  yaxis:{automargin:true},bargap:0.28};

function barUnits(divId, rows, corp, vuelta, opt={}){
  // rows: resultados (unidad,votos,pct_validos)
  const noEsp = rows.filter(r=>r.unidad && !/BLANCO|NULOS|NO MARCADOS/.test(r.unidad));
  noEsp.sort((a,b)=>a.votos-b.votos);
  const top = opt.top? noEsp.slice(-opt.top): noEsp;
  const y=top.map(r=>r.unidad), x=top.map(r=>r.votos);
  const colors=top.map(r=>colorFor(corp,vuelta,r.unidad));
  const text=top.map(r=>pct(r.pct_validos));
  Plotly.newPlot(divId,[{type:"bar",orientation:"h",x,y,marker:{color:colors},
    text,textposition:"auto",hovertemplate:"%{y}<br>%{x:,} votos<extra></extra>"}],
    {...PLOT_LAY,xaxis:{title:"votos"}},PLOT_CFG);
}

function barChange(divId, rows){
  // rows: cambio_1v2v (unidad,delta_abs) a nivel municipio -> agregamos por unidad
  const by={};
  rows.forEach(r=>{const u=r.unidad; if(/BLANCO/.test(u)||!/BLANCO/.test(u)){
    by[u]=(by[u]||0)+ (r.delta_abs||0);}});
  const items=Object.entries(by).filter(([u])=>u&&u!=="undefined")
    .sort((a,b)=>a[1]-b[1]);
  const y=items.map(i=>i[0]), x=items.map(i=>i[1]);
  const colors=x.map(v=>v>=0?"#2a7f4f":"#b23b3b");
  Plotly.newPlot(divId,[{type:"bar",orientation:"h",x,y,marker:{color:colors},
    hovertemplate:"%{y}<br>Δ %{x:,}<extra></extra>"}],
    {...PLOT_LAY,xaxis:{title:"Δ votos (2V − 1V)"}},PLOT_CFG);
}
