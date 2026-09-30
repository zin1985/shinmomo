const world=await fetch('./data/world.json').then(r=>r.json());
const byId=new Map(world.maps.map(m=>[m.config_id,m]));
const entityById=new Map(world.entities.map(e=>[e.entity_id,e]));
const arrivalById=new Map((world.transition_arrivals||[]).map(a=>[a.arrival_id,a]));
const dialogueById=new Map((world.dialogue_sequences||[]).map(d=>[d.dialogue_sequence_id,d]));
const hotspotById=new Map((world.source_transition_hotspots||[]).map(h=>[h.hotspot_id,h]));
const q=s=>document.querySelector(s);
const list=q('#maps'), edges=q('#edges'), unbound=q('#unbound'), detail=q('#detail');
const stage=q('#mapStage'), sizer=q('#mapSizer'), mapImage=q('#mapImage'), viewport=q('#mapViewport');
const actorLayer=q('#actorLayer'), arrivalLayer=q('#arrivalLayer'), hotspotLayer=q('#hotspotLayer');
const focusLayer=q('#focusLayer'), dialogueLayer=q('#dialogueLayer'), gridLayer=q('#gridLayer');
let selectedMap=null;
let selectedFocus=null;

const staticActors=world.entities.filter(e=>e.entity_type==='static_actor_candidate');
const catalogEdges=world.transition_edges||[];
const catalogCandidates=world.transition_candidates||[];
const transitionSummary=world.transition_catalog_summary||{};
const dialogueSummary=world.dialogue_summary||{};
const hotspotSummary=world.source_transition_hotspot_summary||{};
const audit=world.actor_seed_position_audit||{};
q('#summary').textContent=
  String(world.maps.length)+' maps / '+String(transitionSummary.candidate_count||0)+' transition candidates ('+
  String(transitionSummary.confirmed_count||0)+' confirmed / '+String(transitionSummary.strong_candidate_count||0)+' strong) / '+
  String(staticActors.length)+' static actors / '+String(dialogueSummary.sequence_count||0)+' dialogue branches / '+
  String(hotspotSummary.hotspot_count||0)+' source hotspots / '+String((world.transition_arrivals||[]).length)+' grouped arrival points';
q('#positionNotice').textContent=
  `Actor coordinates are statically confirmed for the opcode 0x59 actor renderer: field0659/0699 -> $030B/$030D -> 81:B10F -> 16px render coordinates. `+
  `Corpus bounds check: ${audit.in_bounds??'?'} / ${audit.rows??'?'} in bounds. Sprite artwork uses a viewer bottom-center anchor approximation. `+
  `Click an actor to open linked event/dialogue branches above the character. Dialogue page splits are decoder-derived candidates unless separately confirmed. `+
  `Transition hotspots use independently resolved source-map coordinates; unknown source maps are never guessed from script-pack identity.`;

async function layerSummary(m){
  const out=[];
  for(const layer of m.layers){
    const d=await fetch('./data/'+layer.data).then(r=>r.json());
    out.push({
      bg:layer.bg||null,role:layer.role||'primary',
      tileset_id:d.tileset_id,layout_id:d.layout_id,
      metatile_size:[d.metatile_width,d.metatile_height],
      used_metatiles:Object.keys(d.metatile_definitions).length,
      pixel_data_included:d.pixel_data_included
    });
  }
  return out;
}

function mapEntities(m){
  return (m.entities||[]).map(id=>entityById.get(id)).filter(Boolean);
}

function mapDisplayName(m){
  const actors=mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate');
  const labels=[...new Set(actors.map(e=>e.location_label).filter(Boolean))];
  if(labels.length===1)return labels[0];
  if(labels.length>1)return m.config_id+' ('+labels.join(' / ')+')';
  // Guard against the stale render-catalog label that was formerly injected
  // into the shared t04/l008 configuration. Location identity is pack/instance
  // context, not layout identity.
  if(m.config_id==='cfg_t04_l008_v2'&&m.display_name==='旅立ちの村'){
    return m.config_id+' (場所名未確定 / shared village layout)';
  }
  return m.display_name||m.config_id;
}

function mapArrivals(m){
  return (m.transition_arrivals||[]).map(id=>arrivalById.get(id)).filter(Boolean);
}

function mapHotspots(m){
  return (m.source_transition_hotspots||[]).map(id=>hotspotById.get(id)).filter(Boolean);
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

function clearDialogue(){
  dialogueLayer.replaceChildren();
}

function actorSpeaker(e){
  const s=e.sprite_semantics||{};
  if(s.character_name)return s.character_name;
  if(s.appearance_class)return s.appearance_class;
  if(s.semantic_role&&s.semantic_role!=='unknown')return s.semantic_role;
  return e.record_id||e.selector_hex||'actor';
}

function openDialogue(e){
  clearDialogue();
  const sequences=(e.dialogue_refs||[]).map(id=>dialogueById.get(id)).filter(Boolean);
  const win=document.createElement('div');
  win.className='dialogueWindow'+(e.y<140?' below':'');
  win.style.left=e.x+'px'; win.style.top=e.y+'px';
  win.onclick=ev=>ev.stopPropagation();

  const header=document.createElement('div'); header.className='dialogueHeader';
  const speaker=document.createElement('strong'); speaker.textContent=actorSpeaker(e);
  header.append(speaker);

  const branch=document.createElement('select'); branch.className='dialogueBranch';
  if(sequences.length>1){
    sequences.forEach((seq,i)=>{
      const opt=document.createElement('option');
      const cond=seq.condition&&seq.condition!=='single validated source selection'?seq.condition:'';
      opt.value=String(i);
      opt.textContent=(seq.text_record_id||seq.event_source||('branch '+(i+1)))+(cond?' | condition':'');
      branch.append(opt);
    });
    header.append(branch);
  }else if(sequences.length===1){
    const tag=document.createElement('span');
    tag.textContent=sequences[0].text_record_id||sequences[0].event_source||'dialogue';
    header.append(tag);
  }

  const text=document.createElement('div'); text.className='dialogueText';
  const meta=document.createElement('div'); meta.className='dialogueMeta';
  const controls=document.createElement('div'); controls.className='dialogueControls';
  const prev=document.createElement('button'); prev.textContent='◀';
  const next=document.createElement('button'); next.textContent='次へ';
  const close=document.createElement('button'); close.textContent='閉じる';
  const page=document.createElement('span'); page.className='dialoguePage';
  controls.append(prev,next,close,page);
  win.append(header,text,meta,controls);
  dialogueLayer.append(win);

  let branchIndex=sequences.findIndex(seq=>(seq.pages||[]).length);
  if(branchIndex<0)branchIndex=0;
  let pageIndex=0;
  if(branch.options.length)branch.value=String(branchIndex);

  function currentSequence(){
    return sequences[branchIndex]||null;
  }

  function renderPage(){
    const seq=currentSequence();
    if(!seq){
      text.textContent='（このactorには会話データがまだ接続されていません）';
      meta.textContent=`${e.record_id||''} | ${e.selector_hex||''}`;
      prev.disabled=true; next.disabled=true; page.textContent='0/0';
      return;
    }
    const pages=seq.pages||[];
    const p=pages[pageIndex];
    text.textContent=p?.text||'（イベントは接続済みですが、会話本文は未解読です）';
    const bits=[seq.text_record_id,seq.event_source,seq.confidence,seq.condition].filter(Boolean);
    meta.textContent=bits.join(' | ');
    prev.disabled=pageIndex<=0;
    next.disabled=pages.length===0;
    next.textContent=pageIndex+1<pages.length?'次へ':'閉じる';
    page.textContent=pages.length?`${pageIndex+1}/${pages.length}`:'0/0';
    detail.textContent=JSON.stringify({actor:e,dialogue_sequence:seq},null,2);
  }

  branch.onchange=()=>{branchIndex=Number(branch.value);pageIndex=0;renderPage();};
  prev.onclick=ev=>{ev.stopPropagation();if(pageIndex>0){pageIndex--;renderPage();}};
  next.onclick=ev=>{
    ev.stopPropagation();
    const pages=currentSequence()?.pages||[];
    if(!pages.length)return;
    if(pageIndex+1<pages.length){pageIndex++;renderPage();}else clearDialogue();
  };
  close.onclick=ev=>{ev.stopPropagation();clearDialogue();};
  text.onclick=ev=>{
    ev.stopPropagation();
    const pages=currentSequence()?.pages||[];
    if(!pages.length)return;
    if(pageIndex+1<pages.length){pageIndex++;renderPage();}else clearDialogue();
  };
  renderPage();
}

function renderFocus(m){
  focusLayer.replaceChildren();
  if(!selectedFocus||selectedFocus.map_config_id!==m.config_id)return;
  if(selectedFocus.grid_x==null||selectedFocus.grid_y==null)return;
  const marker=document.createElement('div'); marker.className='focusMarker';
  marker.style.left=(selectedFocus.grid_x*m.grid_cell_px_x)+'px';
  marker.style.top=(selectedFocus.grid_y*m.grid_cell_px_y)+'px';
  focusLayer.append(marker);
  requestAnimationFrame(()=>{
    const z=Number(q('#zoom').value);
    const x=selectedFocus.grid_x*m.grid_cell_px_x*z;
    const y=selectedFocus.grid_y*m.grid_cell_px_y*z;
    viewport.scrollTo({left:Math.max(0,x-viewport.clientWidth/2),top:Math.max(0,y-viewport.clientHeight/2),behavior:'smooth'});
  });
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

function renderHotspots(m){
  hotspotLayer.replaceChildren();
  if(!q('#transitionsToggle').checked)return;
  for(const h of mapHotspots(m)){
    if(h.source_grid_x==null||h.source_grid_y==null)continue;
    const b=document.createElement('button');
    b.className='hotspot'+((h.confidence||'').startsWith('confirmed')?' confirmed':'');
    b.style.left=(h.source_grid_x*m.grid_cell_px_x)+'px';
    b.style.top=(h.source_grid_y*m.grid_cell_px_y)+'px';
    b.style.width=((h.source_width||1)*m.grid_cell_px_x)+'px';
    b.style.height=((h.source_height||1)*m.grid_cell_px_y)+'px';
    const dest=h.destination_config_id?(byId.has(h.destination_config_id)?mapDisplayName(byId.get(h.destination_config_id)):h.destination_config_id):'destination unresolved';
    b.title=`${dest} | ${h.trigger_type||h.hotspot_type||'transition'} | ${h.confidence}`;
    b.onclick=ev=>{
      ev.stopPropagation(); clearDialogue(); detail.textContent=JSON.stringify(h,null,2);
      if(h.destination_config_id&&byId.has(h.destination_config_id)){
        selectMap(byId.get(h.destination_config_id),{
          map_config_id:h.destination_config_id,
          grid_x:h.destination_x,
          grid_y:h.destination_y,
          source_hotspot_id:h.hotspot_id
        });
      }
    };
    hotspotLayer.append(b);
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
    const role=e.sprite_semantics?.semantic_role&&e.sprite_semantics.semantic_role!=='unknown'?' '+e.sprite_semantics.semantic_role:'';
    b.title=`${e.record_id} ${e.selector_hex}${role} grid(${e.grid_x_seed},${e.grid_y_seed}) dialogue:${(e.dialogue_refs||[]).length}`;
    if(canonical&&e.sprite_asset){
      addTransparentSprite(b,e);
    }else{
      addDot(b);
    }
    if(labels){
      const lab=document.createElement('span'); lab.className='actorLabel';
      lab.textContent=`${e.selector_hex} ${e.record_id}`; b.append(lab);
    }
    b.onclick=ev=>{ev.stopPropagation(); openDialogue(e);};
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
    q('#assetStatus').textContent='canonical local map image + static actor / event / transition overlays';
    mapImage.onerror=()=>{
      mapImage.hidden=true;
      q('#assetStatus').textContent='canonical map PNG not found locally; structural overlays remain available';
    };
  }else{
    mapImage.hidden=true; mapImage.removeAttribute('src');
    q('#assetStatus').textContent='canonical assets disabled for this profile';
  }
  renderHotspots(m); renderArrivals(m); renderActors(m); renderFocus(m); applyZoom();
}

async function selectMap(m,focus=null){
  selectedMap=m; selectedFocus=focus; clearDialogue();
  document.querySelectorAll('.mapButton').forEach(b=>b.classList.toggle('active',b.dataset.id===m.config_id));
  q('#title').textContent=mapDisplayName(m);
  renderMap(m);
  detail.textContent='loading structural layers...';
  detail.textContent=JSON.stringify({
    ...m,
    entity_count:mapEntities(m).length,
    static_actor_count:mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate').length,
    dialogue_branch_count:mapEntities(m).reduce((n,e)=>n+(e.dialogue_refs||[]).length,0),
    source_transition_hotspot_count:mapHotspots(m).length,
    transition_arrival_count:mapArrivals(m).length,
    layer_summary:await layerSummary(m)
  },null,2);
  edges.replaceChildren();
  unbound.replaceChildren();
  const showTransitions=q('#transitionsToggle').checked;
  if(!showTransitions){ q('#unboundCount').textContent=''; return; }
  const es=catalogEdges.filter(e=>e.source_config_id===m.config_id||e.destination_config_id===m.config_id);
  for(const e of es){
    const div=document.createElement('div');
    div.className='edge '+(e.confidence==='confirmed'?'confirmed':'strong');
    const forward=e.source_config_id===m.config_id;
    const other=forward?e.destination_config_id:e.source_config_id;
    const otherName=byId.has(other)?mapDisplayName(byId.get(other)):other;
    const arrival=(e.destination_x!=null&&e.destination_y!=null)?' @ ('+e.destination_x+','+e.destination_y+')':'';
    div.append(document.createTextNode((forward?'→ ':'← ')+otherName+' | '+(e.trigger_type||'transition')+arrival+' | '+e.confidence));
    const go=document.createElement('button'); go.className='edgeGo'; go.textContent='open map';
    go.onclick=ev=>{
      ev.stopPropagation();
      if(byId.has(other)){
        const focus=forward&&e.destination_x!=null&&e.destination_y!=null?{map_config_id:other,grid_x:e.destination_x,grid_y:e.destination_y}:null;
        selectMap(byId.get(other),focus);
      }
    };
    div.append(go);
    div.onclick=()=>{detail.textContent=JSON.stringify(e,null,2);};
    edges.append(div);
  }
  if(!es.length){ const p=document.createElement('div'); p.className='muted'; p.textContent='No bound transition edge for this map yet.'; edges.append(p); }
  const us=catalogCandidates.filter(e=>!e.source_config_id&&e.destination_config_id===m.config_id);
  q('#unboundCount').textContent='('+us.length+')';
  for(const e of us){
    const div=document.createElement('div'); div.className='unboundRow';
    const arrival=(e.destination_x!=null&&e.destination_y!=null)?' @ ('+e.destination_x+','+e.destination_y+')':'';
    div.textContent=(e.destination_pack||'?')+' entry '+(e.destination_entry_id||'?')+arrival+' | '+(e.trigger_type||'transition')+' | '+e.confidence;
    div.onclick=()=>{detail.textContent=JSON.stringify(e,null,2);};
    unbound.append(div);
  }
  if(!us.length){ const p=document.createElement('div'); p.className='muted'; p.textContent='No destination-bound/source-unresolved rows for this map.'; unbound.append(p); }
}

for(const m of world.maps){
  const b=document.createElement('button'); b.className='mapButton'; b.dataset.id=m.config_id;
  const actors=(m.entities||[]).map(id=>entityById.get(id)).filter(e=>e?.entity_type==='static_actor_candidate');
  const count=actors.length;
  const dialogueCount=actors.reduce((n,e)=>n+(e.dialogue_refs||[]).length,0);
  const arrivals=(m.transition_arrivals||[]).length;
  const hotspots=(m.source_transition_hotspots||[]).length;
  b.textContent=mapDisplayName(m)+(count?` [A:${count}]`:'')+(dialogueCount?` [D:${dialogueCount}]`:'')+(hotspots?` [H:${hotspots}]`:'')+(arrivals?` [T:${arrivals}]`:'');
  b.onclick=()=>selectMap(m); list.append(b);
}
for(const id of ['transitionsToggle','actorsToggle','arrivalsToggle','labelsToggle','gridToggle','profile']){
  q('#'+id).addEventListener('change',()=>selectedMap&&(id==='transitionsToggle'?selectMap(selectedMap,selectedFocus):renderMap(selectedMap)));
}
q('#zoom').addEventListener('input',()=>{applyZoom();if(selectedMap)renderFocus(selectedMap);});
stage.addEventListener('click',()=>clearDialogue());
if(world.maps[0])selectMap(world.maps[0]);
