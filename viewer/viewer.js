const world=await fetch('./data/world.json').then(r=>r.json());
const byId=new Map(world.maps.map(m=>[m.config_id,m]));
const list=document.querySelector('#maps'), edges=document.querySelector('#edges');
const detail=document.querySelector('#detail');
document.querySelector('#summary').textContent=
  world.maps.length+' maps / '+world.transitions.length+' confirmed transitions';

async function layerSummary(m){
  const out=[];
  for(const layer of m.layers){
    const d=await fetch('./data/'+layer.data).then(r=>r.json());
    out.push({
      bg:layer.bg||null, role:layer.role||'primary',
      tileset_id:d.tileset_id, layout_id:d.layout_id,
      metatile_size:[d.metatile_width,d.metatile_height],
      used_metatiles:Object.keys(d.metatile_definitions).length,
      pixel_data_included:d.pixel_data_included
    });
  }
  return out;
}

async function selectMap(m){
  document.querySelector('#title').textContent=m.display_name||m.config_id;
  detail.textContent='loading structural layers...';
  detail.textContent=JSON.stringify({...m,layer_summary:await layerSummary(m)},null,2);
  edges.replaceChildren();
  const es=world.transitions.filter(e=>
    e.source_config_id===m.config_id||e.destination_config_id===m.config_id);
  for(const e of es){
    const div=document.createElement('div'); div.className='edge';
    const forward=e.source_config_id===m.config_id;
    const other=forward?e.destination_config_id:e.source_config_id;
    div.textContent=(forward?'→ ':'← ')+other+' | '+(e.trigger||e.status||'transition');
    div.onclick=()=>byId.has(other)&&selectMap(byId.get(other)); edges.append(div);
  }
}
for(const m of world.maps){
  const b=document.createElement('button'); b.textContent=m.display_name||m.config_id;
  b.onclick=()=>selectMap(m); list.append(b);
}
if(world.maps[0]) selectMap(world.maps[0]);
