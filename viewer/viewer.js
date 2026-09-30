const world=await fetch('./data/world.json').then(r=>r.json());
const byId=new Map(world.maps.map(m=>[m.config_id,m]));
const entityById=new Map(world.entities.map(e=>[e.entity_id,e]));
const arrivalById=new Map((world.transition_arrivals||[]).map(a=>[a.arrival_id,a]));
const q=s=>document.querySelector(s);
const list=q('#maps'), edges=q('#edges'), detail=q('#detail');
const stage=q('#mapStage'), sizer=q('#mapSizer'), mapImage=q('#mapImage');
const actorLayer=q('#actorLayer'), arrivalLayer=q('#arrivalLayer'), gridLayer=q('#gridLayer');
let selectedMap=null;

const staticActors=world.entities.filter(e=>e.entity_type==='static_actor_candidate');
const audit=world.actor_seed_position_audit||{};
q('#summary').textContent=
  `${world.maps.length} maps / ${world.transitions.length} confirmed transitions / `+
  `${staticActors.length} static actors / ${(world.transition_arrivals||[]).length} grouped arrival points`;
q('#positionNotice').textContent=
  `Actor coordinates are statically confirmed for the opcode 0x59 actor renderer: field0659/0699 -> $030B/$030D -> 81:B10F -> 16px render coordinates. `+
  `Corpus bounds check: ${audit.in_bounds??'?'} / ${audit.rows??'?'} in bounds. Sprite artwork uses a viewer bottom-center anchor approximation. `+
  `Arrival markers show resolved destination coordinates only; an unknown source map is never guessed from script-pack identity.`;

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

function mapArrivals(m){
  return (m.transition_arrivals||[]).map(id=>arrivalById.get(id)).filter(Boolean);
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

function renderArrivals(m){
  arrivalLayer.replaceChildren();
  if(!q('#arrivalsToggle').checked)return;
  const labels=q('#labelsToggle').checked;
  for(const a of mapArrivals(m)){
    const b=document.createElement('button');
    b.className='arrival'+(a.confidence_classes.includes('confirmed')?' confirmed':'');
    b.style.left=a.x+'px'; b.style.top=a.y+'px';
    const entries=a.destination_entry_ids||[];
    b.title=`${(a.destination_packs||[]).join(',')} entries ${entries.join(',')} grid(${a.grid_x},${a.grid_y}) x${a.candidate_row_count}`;
    if(labels){
      const lab=document.createElement('span'); lab.className='arrivalLabel';
      lab.textContent=entries.length<=2?`→${entries.join('/')}`:`→${entries.length} entries`; b.append(lab);
    }
    b.onclick=ev=>{ev.stopPropagation(); detail.textContent=JSON.stringify(a,null,2);};
    arrivalLayer.append(b);
  }
}

function addDot(button){
  const dot=document.createElement('span'); dot.className='dot'; button.prepend(dot);
}

function addTransparentSprite(button,e){
  const img=new Image();
  img.onload=()=>{
    const c=document.createElement('canvas');
    c.width=img.naturalWidth; c.height=img.naturalHeight;
    const ctx=c.getContext('2d',{willReadFrequently:true});
    ctx.drawImage(img,0,0);
    const frame=ctx.getImageData(0,0,c.width,c.height), d=frame.data;
    const bg=[d[0],d[1],d[2]], seen=new Uint8Array(c.width*c.height), stack=[];
    for(let x=0;x<c.width;x++){stack.push(x,(c.height-1)*c.width+x);}
    for(let y=0;y<c.height;y++){stack.push(y*c.width,y*c.width+c.width-1);}
    while(stack.length){
      const i=stack.pop(); if(i<0||i>=seen.length||seen[i])continue; seen[i]=1;
      const o=i*4; if(d[o]!==bg[0]||d[o+1]!==bg[1]||d[o+2]!==bg[2])continue;
      d[o+3]=0; const x=i%c.width, y=Math.floor(i/c.width);
      if(x)stack.push(i-1); if(x+1<c.width)stack.push(i+1);
      if(y)stack.push(i-c.width); if(y+1<c.height)stack.push(i+c.width);
    }
    ctx.putImageData(frame,0,0); c.title=e.selector_hex; button.prepend(c);
  };
  img.onerror=()=>addDot(button);
  img.src=e.sprite_asset;
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
      addTransparentSprite(b,e);
    }else{
      addDot(b);
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
  }
  renderArrivals(m); renderActors(m); applyZoom();
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
    transition_arrival_count:mapArrivals(m).length,
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
  const arrivals=(m.transition_arrivals||[]).length;
  b.textContent=(m.display_name||m.config_id)+(count?` [A:${count}]`:'')+(arrivals?` [T:${arrivals}]`:'');
  b.onclick=()=>selectMap(m); list.append(b);
}
for(const id of ['actorsToggle','arrivalsToggle','labelsToggle','gridToggle','profile']){
  q('#'+id).addEventListener('change',()=>selectedMap&&renderMap(selectedMap));
}
q('#zoom').addEventListener('input',applyZoom);
if(world.maps[0])selectMap(world.maps[0]);
