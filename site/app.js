const REPO="zin1985/shinmomo";
const RAW=`https://raw.githubusercontent.com/${REPO}/main/progress/project_progress.json`;
const API=`https://api.github.com/repos/${REPO}`;
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const fmt=d=>{try{return new Intl.DateTimeFormat("ja-JP",{dateStyle:"medium",timeStyle:"short",timeZone:"Asia/Tokyo"}).format(new Date(d))}catch{return d}};
async function get(url){const r=await fetch(url,{headers:{"Accept":"application/vnd.github+json"}});if(!r.ok)throw new Error(r.status);return r.json()}
function weighted(tracks){const w=tracks.reduce((a,t)=>a+Number(t.weight||1),0);return tracks.reduce((a,t)=>a+Number(t.percent)*Number(t.weight||1),0)/w}
function render(data){
 const overall=weighted(data.tracks);
 $("#overallValue").textContent=overall.toFixed(1);
 $("#overallGauge").style.setProperty("--p",overall);
 $("#overallNote").textContent=data.overall_note;
 $("#updatedAt").textContent=fmt(data.updated_at);
 $("#tracks").innerHTML=data.tracks.map(t=>`<article class="track"><div class="track-top"><div><span class="chip">${esc(t.status)}</span><h3>${esc(t.name)}</h3></div><div class="percent">${Number(t.percent).toFixed(t.percent%1?1:0)}%</div></div><div class="bar"><i style="width:${Math.max(0,Math.min(100,t.percent))}%"></i></div><p><strong>Scope:</strong> ${esc(t.scope)}</p><p><strong>Evidence:</strong> ${esc(t.evidence)}</p></article>`).join("");
 $("#schedule").innerHTML=data.schedule.sort((a,b)=>a.priority-b.priority).map(s=>`<li><div class="prio">#${s.priority}</div><div><h3>${esc(s.title)}</h3><p>${esc(s.target)}</p></div></li>`).join("");
 $("#sources").innerHTML=data.sources.map(s=>`<a href="https://github.com/${REPO}/blob/main/${encodeURI(s)}" target="_blank" rel="noreferrer">${esc(s)}</a>`).join("");
}
async function githubState(){
 const [commit,runs]=await Promise.all([get(`${API}/commits/main`),get(`${API}/actions/runs?branch=main&per_page=10`)]);
 const run=runs.workflow_runs?.find(x=>x.name==="Project CI and release")||runs.workflow_runs?.[0];
 $("#commitLink").textContent=commit.sha.slice(0,8);
 $("#commitLink").href=commit.html_url;
 $("#repoState").innerHTML=`main · <span class="ok">${esc(commit.sha.slice(0,7))}</span>`;
 if(run){const state=run.status==="completed"?(run.conclusion||"unknown"):run.status;$("#actionState").innerHTML=`<span class="${run.conclusion==="success"?"ok":run.status==="completed"?"bad":"warn"}">${esc(state)}</span>`;}
}
(async()=>{
 try{
  const data=await get(`${RAW}?t=${Date.now()}`);
  render(data);
  await githubState();
  $("#fetchedAt").textContent=fmt(new Date().toISOString());
 }catch(e){
  $("#repoState").innerHTML='<span class="bad">GitHub読込エラー</span>';
  console.error(e);
 }
})();
