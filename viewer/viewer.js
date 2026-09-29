const world=await fetch('./data/world.json').then(r=>r.json());
const byId=new Map(world.maps.map(m=>[m.config_id,m]));
const list=document.querySelector('#maps'), edges=document.querySelector('#edges');
document.querySelector('#summary').textContent=
  world.maps.length+' maps / '+world.transitions.length+' confirmed transitions';
function selectMap(m){
  document.querySelector('#title').textContent=m.display_name||m.config_id;
  document.querySelector('#detail').textContent=JSON.stringify(m,null,2);
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
