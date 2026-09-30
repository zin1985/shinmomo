const world=await fetch('./data/world.json').then(r=>r.json());
const byId=new Map(world.maps.map(m=>[m.config_id,m]));
const entityById=new Map(world.entities.map(e=>[e.entity_id,e]));
const q=s=>document.querySelector(s);
const list=q('#maps'), edges=q('#edges'), detail=q('#detail');
const stage=q('#mapStage'), sizer=q('#mapSizer'), mapImage=q('#mapImage');
const actorLayer=q('#actorLayer'), gridLayer=q('#gridLayer');
let selectedMap=null;

const staticActors=world.entities.filter(e=>e.entity_type==='static_actor_candidate');
const audit=world.actor_seed_position_audit||{};
q('#summary').textContent=
  `${world.maps.length} maps / ${world.transitions.length} confirmed transitions / `+
  `${staticActors.length} static actors`;
q('#positionNotice').textContent=
  `Actor placement layer is provisional: opcode 0x59 field0659/0699 seeds are plotted on each map's structural grid. `+
  `Corpus bounds check: ${audit.in_bounds??'?'} / ${audit.rows??'?'} in bounds; semantic coordinate proof remains open.`;

async function layerSummary(m){
  const out=[];
  for(const layer of m.layers){
    const d=await fetch('./data/'+layer.data).then(r=>r.json());
    out.push({
      bg:layer.bg||null,role:layer.role||'primary',
      tileset_id:d.tileset_id,layout_id:d.layout_id,      metatile_size:[d.metatile_width,d.metatile_height],
      used_metatiles:Object.keys(d.metatile_definitions).length,
      pixel_data_included:d.pixel_data_included
    });
  }
  return out;
}

function mapEntities(m){
  return (m.entities||[]).map(id=>entityById.get(id)).filter(Boolean);
}

function applyZoom(){
  if(!selectedMap)return;
  const z=Number(q('#zoom').value);
  q('#zoomValue').textContent=Math.round(z*100)+'%';
  stage.style.width=selectedMap.pixel_width+'px';
  stage.style.height=selectedMap.pixel_height+'px';
  stage.style.transform=`scale(${z})`;
  sizer.style.width=(selectedMap.pixel_width*z)+'px';
  sizer.style.height=(selectedMap.pixel_height*z)+'px';
}

function renderActors(m){
  actorLayer.replaceChildren();
  const show=q('#actorsToggle').checked;
  const labels=q('#labelsToggle').checked;
  if(!show)return;
  const canonical=q('#profile').value==='canonical';
  for(const e of mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate')){
    const b=document.createElement('button');
    b.className='actor candidate';
    b.style.left=e.x+'px'; b.style.top=e.y+'px';
    b.title=`${e.record_id} ${e.selector_hex} grid(${e.grid_x_seed},${e.grid_y_seed})`;    if(canonical&&e.sprite_asset){
      const img=document.createElement('img');
      img.src=e.sprite_asset; img.alt=e.selector_hex;
      img.onerror=()=>{img.remove(); const dot=document.createElement('span'); dot.className='dot'; b.prepend(dot);};
      b.append(img);
    }else{
      const dot=document.createElement('span'); dot.className='dot'; b.append(dot);
    }
    if(labels){
      const lab=document.createElement('span'); lab.className='actorLabel';
      lab.textContent=`${e.selector_hex} ${e.record_id}`; b.append(lab);
    }
    b.onclick=ev=>{ev.stopPropagation(); detail.textContent=JSON.stringify(e,null,2);};
    actorLayer.append(b);
  }
}

function renderMap(m){
  const canonical=q('#profile').value==='canonical';
  stage.style.width=m.pixel_width+'px'; stage.style.height=m.pixel_height+'px';
  gridLayer.classList.toggle('on',q('#gridToggle').checked);
  gridLayer.style.backgroundSize=`${m.grid_cell_px_x}px ${m.grid_cell_px_y}px`;
  if(canonical&&m.canonical_image){
    mapImage.hidden=false; mapImage.src=m.canonical_image;
    q('#assetStatus').textContent='canonical local map image + candidate static actor overlay';
    mapImage.onerror=()=>{
      mapImage.hidden=true;
      q('#assetStatus').textContent='canonical map PNG not found locally; actor overlay remains available';
    };
  }else{
    mapImage.hidden=true; mapImage.removeAttribute('src');
    q('#assetStatus').textContent='canonical assets disabled for this profile';
  }  renderActors(m); applyZoom();
}

async function selectMap(m){
  selectedMap=m;
  document.querySelectorAll('.mapButton').forEach(b=>b.classList.toggle('active',b.dataset.id===m.config_id));
  q('#title').textContent=m.display_name||m.config_id;
  renderMap(m);
  detail.textContent='loading structural layers...';
  detail.textContent=JSON.stringify({
    ...m,
    entity_count:mapEntities(m).length,
    static_actor_count:mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate').length,
    layer_summary:await layerSummary(m)
  },null,2);
  edges.replaceChildren();
  const es=world.transitions.filter(e=>e.source_config_id===m.config_id||e.destination_config_id===m.config_id);
  for(const e of es){
    const div=document.createElement('div'); div.className='edge';
    const forward=e.source_config_id===m.config_id;
    const other=forward?e.destination_config_id:e.source_config_id;
    div.textContent=(forward?'→ ':'← ')+(byId.get(other)?.display_name||other)+' | '+(e.trigger||e.status||'transition');
    div.onclick=()=>byId.has(other)&&selectMap(byId.get(other)); edges.append(div);
  }
}

for(const m of world.maps){
  const b=document.createElement('button'); b.className='mapButton'; b.dataset.id=m.config_id;
  const count=(m.entities||[]).map(id=>entityById.get(id)).filter(e=>e?.entity_type==='static_actor_candidate').length;
  b.textContent=(m.display_name||m.config_id)+(count?` [${count}]`:'');
  b.onclick=()=>selectMap(m); list.append(b);
}for(const id of ['actorsToggle','labelsToggle','gridToggle','profile']){
  q('#'+id).addEventListener('change',()=>selectedMap&&renderMap(selectedMap));
}
q('#zoom').addEventListener('input',applyZoom);
if(world.maps[0])selectMap(world.maps[0]);
