/* maps.js — coropletas Leaflet (municipios Valle, comunas Cali) */
const _maps={};
function ensureMap(id, center, zoom){
  if(_maps[id]){ return _maps[id]; }
  const m=L.map(id,{scrollWheelZoom:false}).setView(center,zoom);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {maxZoom:18,attribution:"© OpenStreetMap © CARTO"}).addTo(m);
  _maps[id]=m; return m;
}
function clearLayer(m){ if(m._data){ m.removeLayer(m._data); m._data=null; } }

// pinta coropleta por ganador. keyProp: propiedad geojson que empata con winByKey
function choropleth(id,center,zoom,geo,keyProp,winByKey,corp,vuelta){
  const m=ensureMap(id,center,zoom); clearLayer(m);
  const layer=L.geoJSON(geo,{
    style:f=>{
      const k=String(f.properties[keyProp]);
      const w=winByKey[k];
      return {weight:1,color:"#fff",fillOpacity:w?0.8:0.3,
        fillColor: w? colorFor(corp,vuelta,w.ganador):"#cfd6df"};
    },
    onEachFeature:(f,l)=>{
      const k=String(f.properties[keyProp]); const w=winByKey[k];
      const nm=f.properties.MPIO_CNMBR||f.properties.nombre||f.properties.corregimie||k;
      l.bindPopup(w? `<b>${nm}</b><br>${w.ganador}<br>${fmt(w.votos_ganador)} votos`+
        `<br>margen ${pct(w.margen_pp)}` : `<b>${nm}</b><br>sin dato`);
    }
  }).addTo(m);
  m._data=layer;
  try{ m.fitBounds(layer.getBounds(),{padding:[8,8]});}catch(e){}
  setTimeout(()=>m.invalidateSize(),50);
}
