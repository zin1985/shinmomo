const world=await fetch('./data/world.json').then(r=>r.json());
const semanticOverrideDoc=await fetch('./data/actor_semantics.json').then(r=>r.ok?r.json():null).catch(()=>null);
if(semanticOverrideDoc?.actor_overrides){
  const semanticOverrideByKey=new Map(semanticOverrideDoc.actor_overrides.map(x=>[
    [x.config_id,x.record_id,x.selector_hex].join('|'),x.sprite_semantics
  ]));
  for(const e of world.entities||[]){
    if(e.entity_type!=='static_actor_candidate')continue;
    const sem=semanticOverrideByKey.get([e.map_config_id,e.record_id,e.selector_hex].join('|'));
    if(sem)e.sprite_semantics=sem;
  }
}
const actorBehaviorDoc=await fetch('./data/actor_behavior.json').then(r=>r.ok?r.json():null).catch(()=>null);
if(actorBehaviorDoc?.actor_behavior){
  const actorBehaviorByKey=new Map(actorBehaviorDoc.actor_behavior.map(x=>[
    [x.config_id,x.record_id,x.selector_hex].join('|'),x.behavior
  ]));
  for(const e of world.entities||[]){
    if(e.entity_type!=='static_actor_candidate')continue;
    const behavior=actorBehaviorByKey.get([e.map_config_id,e.record_id,e.selector_hex].join('|'));
    if(behavior)e.actor_behavior=behavior;
  }
}
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
let selectedPack=null;

const staticActors=world.entities.filter(e=>e.entity_type==='static_actor_candidate');
const catalogEdges=world.transition_edges||[];
const catalogCandidates=world.transition_candidates||[];
const transitionSummary=world.transition_catalog_summary||{};
const dialogueSummary=world.dialogue_summary||{};
const hotspotSummary=world.source_transition_hotspot_summary||{};
const audit=world.actor_seed_position_audit||{};
const sceneRequirementById=new Map(((world.scene_state_requirements||{}).scenes||[]).map(s=>[s.scene_id,s]));
const sceneStateValues=new Map();
q('#summary').textContent=
  String(world.maps.length)+' maps / '+String(transitionSummary.candidate_count||0)+' transition candidates ('+
  String(transitionSummary.confirmed_count||0)+' confirmed / '+String(transitionSummary.strong_candidate_count||0)+' strong) / '+
  String(staticActors.length)+' static actors / '+String(dialogueSummary.sequence_count||0)+' dialogue branches / '+
  String(hotspotSummary.hotspot_count||0)+' source hotspots / '+String((world.transition_arrivals||[]).length)+' grouped arrival points';
q('#positionNotice').textContent=
  `Actor coordinates are statically confirmed for the opcode 0x59 actor renderer: field0659/0699 -> $030B/$030D -> 81:B10F -> 16px render coordinates. `+
  `Corpus bounds check: ${audit.in_bounds??'?'} / ${audit.rows??'?'} in bounds. Sprite artwork uses a viewer bottom-center anchor approximation. `+
  `Scene-state controls are raw machine-state inputs; unknown values keep conditional actors/dialogue as candidates, while fully known values can filter actors and select a unique branch. `+
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

function mapActorPacks(m){
  return [...new Set(
    mapEntities(m)
      .filter(e=>e.entity_type==='static_actor_candidate'&&e.pack_id_hex)
      .map(e=>e.pack_id_hex)
  )].sort();
}

function sceneIdFor(m=selectedMap,pack=selectedPack){
  return m&&pack?`${m.config_id}@${pack}`:null;
}

function stateInputKey(input){
  if(!input)return '';
  if(input.kind==='flag'||input.kind==='bitset_bit')return `bit:${input.wram}:${input.bit}`;
  if(input.kind==='relation_resolver_condition')return `relation:${input.key}:${input.subkey||'0x00'}`;
  return `${input.kind||'state'}:${input.wram||input.key||input.operand||''}:${input.bit??''}`;
}

function stateInputLabel(input){
  if(input.kind==='flag')return `flag ${input.spec||''} ${input.wram}.bit${input.bit}`;
  if(input.kind==='bitset_bit')return `bitset ${input.wram}.bit${input.bit}`;
  if(input.kind==='relation_resolver_condition')return `relation ${input.key}/${input.subkey||'0x00'}`;
  return input.kind||'state';
}

function stateStore(sceneId){
  if(!sceneId)return null;
  if(!sceneStateValues.has(sceneId))sceneStateValues.set(sceneId,new Map());
  return sceneStateValues.get(sceneId);
}

function stateValue(input,sceneId=null){
  sceneId=sceneId||sceneIdFor();
  const store=sceneId?sceneStateValues.get(sceneId):null;
  const key=stateInputKey(input);
  return store&&store.has(key)?store.get(key):null;
}

function sceneActorCandidates(m,pack=selectedPack){
  const actors=mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate');
  const packs=mapActorPacks(m);
  if(pack)return actors.filter(e=>e.pack_id_hex===pack);
  if(packs.length===1)return actors.filter(e=>e.pack_id_hex===packs[0]);
  return [];
}

function evaluateActorSpawn(e){
  const spawn=e.spawn_condition||null;
  if(!spawn)return null;
  if(spawn.condition_status==='confirmed_static_unconditional')return true;
  if(spawn.condition_status==='confirmed_static_flag'&&spawn.flag_wram!=null){
    const v=stateValue({kind:'flag',wram:spawn.flag_wram,bit:spawn.flag_bit},e.scene_id);
    if(v==null)return null;
    return spawn.branch_opcode==='B4'?v===0:v!==0;
  }
  if(spawn.condition_status==='confirmed_static_bitset_expression'){
    const terms=spawn.terms||[];
    if(!terms.length)return null;
    for(const term of terms){
      const v=stateValue({kind:'bitset_bit',wram:term.wram,bit:term.bit},e.scene_id);
      if(v==null)return null;
      if(v!==Number(term.expected_value))return false;
    }
    return true;
  }
  return null;
}

function sceneActors(m,pack=selectedPack){
  return sceneActorCandidates(m,pack).filter(e=>evaluateActorSpawn(e)!==false);
}

function populateScenePack(m,requestedPack=null){
  const sel=q('#scenePack');
  const packs=mapActorPacks(m);
  const options=[...packs];
  if(requestedPack&&!options.includes(requestedPack))options.push(requestedPack);
  sel.replaceChildren();
  const placeholder=document.createElement('option');
  placeholder.value='';
  placeholder.textContent=packs.length>1?'select scene pack':'auto';
  sel.append(placeholder);
  for(const pack of options.sort()){
    const o=document.createElement('option');
    o.value=pack;
    const count=mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate'&&e.pack_id_hex===pack).length;
    o.textContent=pack+(count?' ('+count+' actors)':' (no mapped actor set)');
    sel.append(o);
  }
  sel.value=requestedPack||'';
}

function populateStateControls(m,pack=selectedPack){
  const controls=q('#stateControls'),status=q('#stateStatus'),reset=q('#stateReset');
  controls.replaceChildren();
  const sceneId=sceneIdFor(m,pack);
  if(!sceneId){
    status.textContent='scene pack is unresolved; state evaluation is unavailable';
    reset.disabled=true;
    return;
  }
  const req=sceneRequirementById.get(sceneId);
  if(!req){
    status.textContent=sceneId+' | state requirement譛ｪ逋ｻ骭ｲ';
    reset.disabled=true;
    return;
  }
  const unique=new Map();
  for(const input of req.state_inputs||[]){
    const key=stateInputKey(input);
    if(key&&!unique.has(key))unique.set(key,input);
  }
  const store=stateStore(sceneId);
  for(const [key,input] of unique){
    const lab=document.createElement('label');lab.className='stateField';
    const name=document.createElement('span');name.textContent=stateInputLabel(input);
    const sel=document.createElement('select');
    for(const [value,label] of [['?','?'],['0','0'],['1','1']]){
      const opt=document.createElement('option');opt.value=value;opt.textContent=label;sel.append(opt);
    }
    sel.value=store.has(key)?String(store.get(key)):'?';
    sel.title=JSON.stringify(input);
    sel.onchange=()=>{
      if(sel.value==='?')store.delete(key);else store.set(key,Number(sel.value));
      clearDialogue();
      renderActors(m);
      populateStateControls(m,pack);
    };
    lab.append(name,sel);controls.append(lab);
  }
  const assigned=[...unique.keys()].filter(k=>store.has(k)).length;
  const unresolved=(req.unresolved_predicates||[]).length;
  status.textContent=`${sceneId} | raw state ${assigned}/${unique.size} set${unresolved?' | unresolved predicate '+unresolved:''}`;
  reset.disabled=store.size===0;
  reset.onclick=()=>{
    store.clear();clearDialogue();renderActors(m);populateStateControls(m,pack);
  };
}

function mapDisplayName(m,pack=null){
  const actors=pack
    ? mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate'&&e.pack_id_hex===pack)
    : mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate');
  const labels=[...new Set(actors.map(e=>e.location_label).filter(Boolean))];
  if(labels.length===1)return labels[0];
  if(labels.length>1)return m.config_id+' ('+labels.join(' / ')+')';
  // Guard against the stale render-catalog label that was formerly injected
  // into the shared t04/l008 configuration. Location identity is pack/instance
  // context, not layout identity.
  if(m.config_id==='cfg_t04_l008_v2'){
    return m.config_id+' (location unresolved / shared village layout)';
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

function evaluateDialogueCondition(seq){
  const c=seq.condition_detail||null;
  if(!c){
    if(!seq.condition||seq.condition==='single validated source selection')return true;
    return null;
  }
  const id=c.condition_id||'';
  if(id==='always'||c.status==='confirmed_static_single_path')return true;
  if(!id.startsWith('common_'))return null;
  const primary=(c.flag_tests||[]).find(x=>x.spec==='0x65')||(c.flag_tests||[])[0];
  const rel=c.relation_test||null;
  if(!primary||!rel)return null;
  const flag=stateValue({kind:'flag',wram:primary.wram,bit:primary.bit},seq.scene_id);
  const relation=stateValue({kind:'relation_resolver_condition',key:rel.key,subkey:rel.subkey},seq.scene_id);
  if(flag==null||relation==null)return null;
  const common=(flag!==0)&&(relation===0);
  if(id==='common_true')return common;
  if(id==='common_false')return !common;
  if(id==='common_false_flag0B_clear'||id==='common_false_flag0B_set'){
    if(common)return false;
    const secondary=(c.flag_tests||[]).find(x=>x.spec==='0x0B');
    if(!secondary)return null;
    const v=stateValue({kind:'flag',wram:secondary.wram,bit:secondary.bit},seq.scene_id);
    if(v==null)return null;
    return id.endsWith('_clear')?v===0:v!==0;
  }
  return null;
}

function openDialogue(e){
  clearDialogue();
  const spawn=e.spawn_condition||null;
  const sequences=(e.dialogue_refs||[]).map(id=>dialogueById.get(id)).filter(Boolean);
  const win=document.createElement('div');
  win.className='dialogueWindow'+(e.y<140?' below':'');
  win.style.left=e.x+'px'; win.style.top=e.y+'px';
  win.onclick=ev=>ev.stopPropagation();

  const header=document.createElement('div'); header.className='dialogueHeader';
  const speaker=document.createElement('strong'); speaker.textContent=actorSpeaker(e);
  header.append(speaker);

  const branch=document.createElement('select'); branch.className='dialogueBranch';
  const sequenceState=sequences.map(evaluateDialogueCondition);
  const allBranchStateKnown=sequenceState.length>0&&sequenceState.every(v=>v!==null);
  const matchedBranches=sequenceState.map((v,i)=>v===true?i:-1).filter(i=>i>=0);
  if(sequences.length>1){
    const unresolved=document.createElement('option');
    unresolved.value='';
    unresolved.textContent=allBranchStateKnown?(matchedBranches.length?'state evaluated':'no matching state branch'):'state unresolved; choose a dialogue candidate';
    branch.append(unresolved);
    sequences.forEach((seq,i)=>{
      const opt=document.createElement('option');
      const cond=seq.condition&&seq.condition!=='single validated source selection'?seq.condition:'';
      const mark=sequenceState[i]===true?'OK ':sequenceState[i]===false?'NO ':'? ';
      opt.value=String(i);
      opt.textContent=mark+(seq.text_record_id||seq.event_source||('branch '+(i+1)))+(cond?' | 譚｡莉ｶ莉倥″':'');
      if(cond)opt.title=cond;
      branch.append(opt);
    });
    header.append(branch);
  }else if(sequences.length===1){
    const tag=document.createElement('span');
    tag.textContent=sequences[0].text_record_id||sequences[0].event_source||'dialogue';
    header.append(tag);
  }

  const actorMeta=document.createElement('div'); actorMeta.className='dialogueMeta actorSpriteMeta';
  const sem=e.sprite_semantics||{}, dir=e.directional_sprite||{}, beh=e.actor_behavior||{};
  const actorBits=[
    e.record_id,e.selector_hex,
    e.sprite_group!=null?'group '+e.sprite_group:null,
    sem.semantic_role&&sem.semantic_role!=='unknown'?'role '+sem.semantic_role:null,
    sem.confidence?'semantic '+sem.confidence:null,
    beh.behavior_class?'behavior '+beh.behavior_class:null,
    beh.record_body_shape?'body '+beh.record_body_shape:null,
    beh.initial_facing_candidate?'facing? '+beh.initial_facing_candidate:null,
    dir.direction_binding_status||null,
    spawn?.condition_status?'spawn '+spawn.condition_status:null,
  ].filter(Boolean);
  actorMeta.textContent=actorBits.join(' | ');
  actorMeta.title=[
    sem.appearance_class?'appearance: '+sem.appearance_class:null,
    sem.character_name?'identity: '+sem.character_name:null,
    dir.right_frames?'RIGHT '+dir.right_frames:null,
    dir.front_frames?'FRONT '+dir.front_frames:null,
    dir.left_frames?'LEFT '+dir.left_frames:null,
    dir.back_frames?'BACK '+dir.back_frames:null,
    dir.walk_animation?'walk '+dir.walk_animation:null,
    beh.controller_pointer?'controller: '+beh.controller_pointer:null,
    beh.controller_dispatch_grammar?'dispatch: '+beh.controller_dispatch_grammar:null,
    beh.record_body_size!=null?'body size: '+beh.record_body_size:null,
    beh.body_prefix_size!=null?'body prefix: '+beh.body_prefix_size:null,
    beh.body_suffix_size!=null?'body suffix: '+beh.body_suffix_size:null,
    beh.body_suffix_hex?'body suffix bytes: '+beh.body_suffix_hex:null,
    beh.field_0719_seed_hex?'field0719: '+beh.field_0719_seed_hex:null,
    beh.validated_event_source_count!=null?'validated sources: '+beh.validated_event_source_count:null,
    beh.decoded_dialogue_source_count!=null?'decoded dialogue sources: '+beh.decoded_dialogue_source_count:null,
    beh.evidence?'behavior evidence: '+beh.evidence:null,
    sem.evidence?'semantic evidence: '+sem.evidence:null,
    spawn?.condition_expr?'spawn condition: '+spawn.condition_expr:null,
    spawn?.predicate_bytecode?'spawn bytecode: '+spawn.predicate_bytecode:null,
    spawn?.evidence?'spawn evidence: '+spawn.evidence:null,
  ].filter(Boolean).join('\n');
  const text=document.createElement('div'); text.className='dialogueText';
  const meta=document.createElement('div'); meta.className='dialogueMeta';
  const controls=document.createElement('div'); controls.className='dialogueControls';
  const prev=document.createElement('button'); prev.textContent='笳';
  const next=document.createElement('button'); next.textContent='谺｡縺ｸ';
  const close=document.createElement('button'); close.textContent='髢峨§繧・;
  const page=document.createElement('span'); page.className='dialoguePage';
  controls.append(prev,next,close,page);
  win.append(header,actorMeta,text,meta,controls);
  dialogueLayer.append(win);

  let branchIndex=sequences.length===1?(sequenceState[0]===false?-1:0):(allBranchStateKnown&&matchedBranches.length===1?matchedBranches[0]:-1);
  let pageIndex=0;
  if(branch.options.length)branch.value=branchIndex>=0?String(branchIndex):'';

  function currentSequence(){
    return branchIndex>=0?(sequences[branchIndex]||null):null;
  }

  function renderPage(){
    const seq=currentSequence();
    if(!seq){
      if(sequences.length){
        text.textContent=allBranchStateKnown?'No dialogue branch matches the current raw state. You can inspect candidates manually.':'Story state is unresolved. Choose a conditional dialogue candidate.';
        meta.textContent=`${e.record_id||''} | ${e.selector_hex||''} | branch state ${allBranchStateKnown?'evaluated':'unresolved'}`;
        detail.textContent=JSON.stringify({actor:e,dialogue_candidates:sequences,condition_results:sequenceState},null,2);
      }else{
        text.textContent='・医％縺ｮactor縺ｫ縺ｯ莨夊ｩｱ繝・・繧ｿ縺後∪縺謗･邯壹＆繧後※縺・∪縺帙ｓ・・;
        meta.textContent=`${e.record_id||''} | ${e.selector_hex||''}`;
      }
      prev.disabled=true; next.disabled=true; page.textContent='0/0';
      return;
    }
    const pages=seq.pages||[];
    const p=pages[pageIndex];
    text.textContent=p?.text||'Event is linked, but dialogue text is not decoded yet.';
    const stateResult=sequenceState[branchIndex];
    const bits=[seq.text_record_id,seq.event_source,seq.confidence,seq.condition,stateResult===true?'state:match':stateResult===false?'state:not-match':'state:unknown'].filter(Boolean);
    meta.textContent=bits.join(' | ');
    prev.disabled=pageIndex<=0;
    next.disabled=pages.length===0;
    next.textContent=pageIndex+1<pages.length?'Next':'Close';
    page.textContent=pages.length?`${pageIndex+1}/${pages.length}`:'0/0';
    detail.textContent=JSON.stringify({actor:e,dialogue_sequence:seq},null,2);
  }

  branch.onchange=()=>{branchIndex=branch.value===''?-1:Number(branch.value);pageIndex=0;renderPage();};
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
      lab.textContent=entries.length<=2?`竊・{entries.join('/')}`:`竊・{entries.length} entries`; b.append(lab);
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
        },h.destination_pack||null);
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
  for(const e of sceneActors(m)){
    const b=document.createElement('button');
    const spawn=e.spawn_condition||null;
    const spawnEval=evaluateActorSpawn(e);
    const spawnNeedsState=spawn?.visibility_when_state_unknown==='candidate';
    const spawnConditional=spawnNeedsState&&spawnEval===null;
    const spawnResolved=spawnNeedsState&&spawnEval===true;
    b.className='actor candidate'+(spawnConditional?' stateConditional':'')+(spawnResolved?' stateResolved':'');
    b.style.left=e.x+'px'; b.style.top=e.y+'px';
    const role=e.sprite_semantics?.semantic_role&&e.sprite_semantics.semantic_role!=='unknown'?' '+e.sprite_semantics.semantic_role:'';
    b.title=`${e.record_id} ${e.selector_hex}${role} grid(${e.grid_x_seed},${e.grid_y_seed}) dialogue:${(e.dialogue_refs||[]).length} spawn:${spawn?.condition_status||'unknown'} eval:${spawnEval==null?'?':spawnEval}`;
    if(canonical&&e.sprite_asset){
      addTransparentSprite(b,e);
    }else{
      addDot(b);
    }
    if(labels){
      const lab=document.createElement('span'); lab.className='actorLabel';
      lab.textContent=`${spawnConditional?'? ':''}${e.selector_hex} ${e.record_id}`; b.append(lab);
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

function renderAnalysisEvidence(m){ const actors=sceneActorCandidates(m), visible=sceneActors(m), dialogues=visible.flatMap(e=>(e.dialogue_refs||[]).map(id=>dialogueById.get(id)).filter(Boolean)), unresolved=dialogues.filter(d=>d.condition_status==="predicate_unresolved_static"||d.branch_selection_policy==="preserve_all_candidates_until_state_resolved"), conditional=actors.filter(e=>(e.spawn_condition||{}).visibility_when_state_unknown==="candidate"), hotspots=mapHotspots(m), arrivals=mapArrivals(m), related=catalogEdges.filter(e=>e.source_config_id===m.config_id||e.destination_config_id===m.config_id); const cards=[["Scene / pack",selectedPack||"unresolved",mapActorPacks(m).length+" actor pack(s)",selectedPack?"confidenceConfirmed":"confidenceUnresolved"],["NPC actors",String(visible.length),conditional.length+" conditional/unresolved",conditional.length?"confidenceCandidate":"confidenceConfirmed"],["Dialogue",String(dialogues.length),unresolved.length+" unresolved branch(es)",unresolved.length?"confidenceUnresolved":"confidenceConfirmed"],["Transitions",String(related.length),hotspots.length+" hotspots / "+arrivals.length+" arrivals",related.length?"confidenceConfirmed":"confidenceCandidate"]]; const host=q("#analysisSummary"); host.replaceChildren(); for(const [title,value,note,cls] of cards){const d=document.createElement("div"),st=document.createElement("strong"),sm=document.createElement("small");d.className="analysisCard "+cls;st.textContent=title+": "+value;sm.textContent=note;d.append(st,sm);host.append(d);} q("#analysisDetail").textContent=JSON.stringify({map_config_id:m.config_id,active_scene_pack:selectedPack,available_actor_packs:mapActorPacks(m),evidence:{opcode59_coordinate_binding:"statically confirmed for opcode 0x59 actor renderer",actor_seed_position_audit:audit,active_actor_count:visible.length,conditional_actor_candidates:conditional.map(e=>({record_id:e.record_id,selector_hex:e.selector_hex,spawn_condition:e.spawn_condition})),dialogue_branch_count:dialogues.length,unresolved_dialogue_branches:unresolved.map(d=>({id:d.dialogue_sequence_id,condition_status:d.condition_status,policy:d.branch_selection_policy,event_source:d.event_source})),source_transition_hotspots:hotspots,transition_arrivals:arrivals,bound_transition_edges:related},interpretation_rule:"confirmed evidence and unresolved candidates are displayed separately; unresolved state is never promoted to current game state"},null,2); }

async function selectMap(m,focus=null,pack=undefined){
  const packs=mapActorPacks(m);
  selectedMap=m;
  selectedFocus=focus;
  selectedPack=(pack!==undefined&&pack!==null&&pack!=='') ? pack : (packs.length===1?packs[0]:null);
  populateScenePack(m,selectedPack);
  populateStateControls(m,selectedPack);
  clearDialogue();
  document.querySelectorAll('.mapButton').forEach(b=>b.classList.toggle('active',b.dataset.id===m.config_id));
  q('#title').textContent=mapDisplayName(m,selectedPack)+(selectedPack?' ['+selectedPack+']':(packs.length>1?' [scene pack unresolved]':''));
  renderMap(m);
  renderAnalysisEvidence(m);
  detail.textContent='loading structural layers...';
  detail.textContent=JSON.stringify({
    ...m,
    entity_count:mapEntities(m).length,
    active_scene_pack:selectedPack,
    available_actor_packs:mapActorPacks(m),
    static_actor_count:sceneActors(m).length,
    catalog_scene_actor_count:sceneActorCandidates(m).length,
    conditional_actor_candidate_count:sceneActorCandidates(m).filter(e=>e.spawn_condition?.visibility_when_state_unknown==='candidate'&&evaluateActorSpawn(e)==null).length,
    state_resolved_conditional_actor_count:sceneActorCandidates(m).filter(e=>e.spawn_condition?.visibility_when_state_unknown==='candidate'&&evaluateActorSpawn(e)===true).length,
    state_hidden_actor_count:sceneActorCandidates(m).filter(e=>evaluateActorSpawn(e)===false).length,
    unconditional_actor_count:sceneActorCandidates(m).filter(e=>e.spawn_condition?.visibility_when_state_unknown==='visible').length,
    all_static_actor_count:mapEntities(m).filter(e=>e.entity_type==='static_actor_candidate').length,
    dialogue_branch_count:sceneActors(m).reduce((n,e)=>n+(e.dialogue_refs||[]).length,0),
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
    div.append(document.createTextNode((forward?'竊・':'竊・')+otherName+' | '+(e.trigger_type||'transition')+arrival+' | '+e.confidence));
    const go=document.createElement('button'); go.className='edgeGo'; go.textContent='open map';
    go.onclick=ev=>{
      ev.stopPropagation();
      if(byId.has(other)){
        const focus=forward&&e.destination_x!=null&&e.destination_y!=null?{map_config_id:other,grid_x:e.destination_x,grid_y:e.destination_y}:null;
        const targetPack=forward?(e.destination_pack||null):(e.source_pack||null);
        selectMap(byId.get(other),focus,targetPack);
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
  q('#'+id).addEventListener('change',()=>selectedMap&&(id==='transitionsToggle'?selectMap(selectedMap,selectedFocus,selectedPack):renderMap(selectedMap)));
}
q('#scenePack').addEventListener('change',()=>{
  if(selectedMap)selectMap(selectedMap,selectedFocus,q('#scenePack').value||null);
});
q('#zoom').addEventListener('input',()=>{applyZoom();if(selectedMap)renderFocus(selectedMap);});
stage.addEventListener('click',()=>clearDialogue());
if(world.maps[0])selectMap(world.maps[0]);


