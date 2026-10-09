/* Public NFL hub: rankings, weekly lineup scenarios and immutable 2026 results. */
(() => {
  'use strict';
  const embedded=document.getElementById('nfl-data');
  if(!embedded)return;
  const data=JSON.parse(embedded.textContent), shell=document.querySelector('[data-nfl-view]');
  const view=shell.dataset.nflView, $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const signed=(value,digits=1)=>Math.abs(value)<.5*10**(-digits)?(0).toFixed(digits):(value>0?'+':'')+value.toFixed(digits);
  const date=stamp=>new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZone:'America/New_York',timeZoneName:'short'}).format(new Date(stamp));
  const team=abbr=>data.teams.find(t=>t.abbr===abbr), params=new URLSearchParams(location.search);
  const rankingsUrl=document.querySelector('.nfl-tabs a[href*="/rankings/"]').getAttribute('href');
  const storageKey='dual-eights-nfl-scenarios';
  let state={generated_at:data.generated_at,qbs:{},rankTeams:[]};
  try{const saved=JSON.parse(sessionStorage.getItem(storageKey));if(saved?.generated_at===data.generated_at)state=saved;}catch{}
  state.rankTeams=state.rankTeams.filter(t=>team(t));
  for(const [abbr,id] of Object.entries(state.qbs)){if(!team(abbr)?.qb_options.some(q=>q.id===id))delete state.qbs[abbr];}
  const persist=()=>{try{sessionStorage.setItem(storageKey,JSON.stringify(state));}catch{}};
  const chosen=t=>t.qb_options.find(q=>q.id===state.qbs[t.abbr]);
  const delta=t=>chosen(t)?.points_change||0;
  const movement=value=>value>0?`<span class="nfl-up">↑ ${value}</span>`:value<0?`<span class="nfl-down">↓ ${-value}</span>`:'—';
  function ratings(){
    const shift=data.teams.reduce((sum,t)=>sum+(state.rankTeams.includes(t.abbr)?delta(t):0),0)/32;
    return data.teams.map(t=>{const change=(state.rankTeams.includes(t.abbr)?delta(t):0)-shift;return {...t,strength:t.strength+change,qb_points:t.qb_points+change};})
      .sort((a,b)=>b.strength-a.strength).map((t,i)=>({...t,rank:i+1,weekly_rank_change:t.previous_week_beta_rank-i-1}));
  }
  let sortKey=params.get('sort')==='efficiency'?'efficiency':'rank', ascending=sortKey==='rank';
  function renderRankings(){
    if(!$('nfl-ranking-rows'))return;
    const query=($('nfl-search')?.value||'').toLowerCase();
    let rows=ratings().filter(t=>`${t.name} ${t.abbr} ${t.abbr==='LA'?'LAR':''}`.toLowerCase().includes(query));
    rows.sort((a,b)=>{
      let x=a[sortKey],y=b[sortKey];
      if(sortKey==='record'){x=Number(x.split('-')[0]);y=Number(y.split('-')[0]);}
      const comparison=typeof x==='string'?x.localeCompare(y):x-y;
      return (ascending?comparison:-comparison)||a.rank-b.rank;
    });
    if(view==='overview')rows=rows.slice(0,8);
    $('nfl-ranking-rows').innerHTML=rows.length?rows.map(t=>`<tr><td>${t.rank}</td><th scope="row" class="nfl-team-cell"><a href="${esc(rankingsUrl)}?team=${esc(t.abbr)}#team-detail" data-team="${esc(t.abbr)}"><span class="nfl-team-code">${esc(t.abbr)}</span>${esc(t.name)}${state.rankTeams.includes(t.abbr)&&chosen(t)?' <span class="nfl-scenario-star" title="Ranking scenario">*</span>':''}</a></th><td>${esc(t.record)}</td><td class="nfl-tsi">${signed(t.strength)}</td><td>${movement(t.weekly_rank_change)}</td><td>${t.efficiency.toFixed(1)}</td><td>${t.efficiency_rank}</td>${view==='rankings'?['offense_points','defense_points','st_points','qb_points'].map(k=>`<td>${signed(t[k])}</td>`).join(''):''}</tr>`).join(''):'<tr><td colspan="11" class="nfl-empty">No teams match your search.</td></tr>';
    $('nfl-rank-status')?.replaceChildren(document.createTextNode(`${rows.length} ${rows.length===1?'team':'teams'} · ${state.rankTeams.length?'ranking scenarios active (*)':'default depth-chart quarterbacks'}`));
    document.querySelectorAll('[data-sort]').forEach(button=>{
      const th=button.closest('th');th.removeAttribute('aria-sort');
      const arrow=button.querySelector('span');if(arrow)arrow.remove();
      if(button.dataset.sort===sortKey){th.setAttribute('aria-sort',ascending?'ascending':'descending');const span=document.createElement('span');span.setAttribute('aria-hidden','true');span.textContent=ascending?' ↑':' ↓';button.append(span);}
    });
  }
  function qbControls(){
    if(!$('nfl-team-select'))return;
    const t=team($('nfl-team-select').value), option=chosen(t), first=t.qb_options.find(q=>q.id!==t.expected_qb.id);
    $('nfl-qb-select').innerHTML=t.qb_options.map(q=>`<option value="${esc(q.id)}">${esc(q.name)}${q.id===t.expected_qb.id?' · default':''}${q.injury_status?' · '+esc(q.injury_status):''}</option>`).join('');
    $('nfl-qb-select').value=option?.id||t.expected_qb.id;
    $('nfl-backup').checked=!!first&&option?.id===first.id;$('nfl-backup').disabled=!first;
    $('nfl-apply-ranks').checked=state.rankTeams.includes(t.abbr);$('nfl-apply-ranks').disabled=!option;
  }
  function detail(){
    if(!$('nfl-team-detail'))return;
    const original=team($('nfl-team-select').value), t=ratings().find(x=>x.abbr===original.abbr);
    const q=chosen(original)||original.qb_options.find(q=>q.id===original.expected_qb.id), change=delta(original);
    $('nfl-team-detail').innerHTML=`<div class="nfl-detail-header"><div><h3>${esc(t.name)}</h3><p class="nfl-small">TSI #${t.rank} · Efficiency #${t.efficiency_rank} (${t.efficiency.toFixed(1)}/100) · ${esc(t.record)}</p></div><strong class="nfl-detail-number">${signed(t.strength)} pts</strong></div><p class="nfl-detail-note"><strong>${esc(q.name)}</strong> · ${chosen(original)?'Scenario':'Depth-chart default'} · weekly margin adjustment ${signed(change)} points${state.rankTeams.includes(t.abbr)?' · applied to rankings':''}${q.injury_status?`<br>Week ${data.projection_week} injury designation: <strong>${esc(q.injury_status)}</strong>.`:''}</p><p class="nfl-small">${Math.round(q.effective_dropbacks)} weighted dropbacks in the QB estimate · ${esc(q.prior_group.replaceAll('_',' '))}. Player performance used by the model stops at Week ${data.rating_week}.</p><div class="nfl-detail-bars">${[['Offense',t.offense_points],['Defense',t.defense_points],['Special teams',t.st_points],['Lineup adj.',t.qb_points]].map(([label,v])=>`<div class="nfl-bar-row"><span>${label}</span><div class="nfl-bar-track"><span class="nfl-bar-fill ${v<0?'negative':''}" style="left:${v<0?50-Math.min(49,Math.abs(v)*5):50}%;width:${Math.min(49,Math.abs(v)*5)}%"></span></div><strong>${signed(v)}</strong></div>`).join('')}</div><dl class="nfl-detail-stats">${[['Offensive EPA/play',signed(t.offense_epa,3)],['Defensive EPA allowed',signed(t.defense_epa,3)],['Offensive success',t.offense_success.toFixed(1)+'%'],['Defensive success allowed',t.defense_success.toFixed(1)+'%']].map(([label,value])=>`<div><dt>${label}</dt><dd>${value}</dd></div>`).join('')}</dl><p class="nfl-small">${t.historical_context.new_head_coach?'New coach: historical offense and defense carry reduced. ':''}${t.historical_context.new_opening_qb?'New primary QB: historical offense carry also reduced. ':''}These raw season stats describe performance; the TSI contributions include opponent adjustments and historical pooling.</p>`;
  }
  const spread=(margin,home,away)=>margin==null?'Unavailable':Math.abs(margin)<.05?'Pick’em':`${margin>0?home:away} −${Math.abs(margin).toFixed(1)}`;
  function renderSpreads(){
    if(!$('nfl-spread-rows'))return;
    const games=data.games.filter(g=>g.week===data.projection_week);
    $('nfl-spread-rows').innerHTML=games.map(g=>{
      const h=team(g.home),a=team(g.away), final=g.status==='Final';
      const homeChoice=final?null:chosen(h),awayChoice=final?null:chosen(a);
      const baseHome=h.qb_options.find(q=>q.id===g.home_qb_id)?.points_change||0;
      const baseAway=a.qb_options.find(q=>q.id===g.away_qb_id)?.points_change||0;
      const change=final?0:(homeChoice?homeChoice.points_change-baseHome:0)-(awayChoice?awayChoice.points_change-baseAway:0);
      const margin=g.forecast_home_margin+change, gap=g.market_home_margin==null?null:margin-g.market_home_margin;
      const scenario=!!(homeChoice||awayChoice),homeName=homeChoice?.name||g.home_qb,awayName=awayChoice?.name||g.away_qb;
      const status=q=>{const match=(q===homeName?h:a).qb_options.find(x=>x.name===q);return match?.injury_status?` (${esc(match.injury_status)})`:'';};
      return `<tr class="${final?'nfl-game-final':''}"><th scope="row" class="nfl-team-cell">${esc(g.away)} ${g.neutral?'vs.':'at'} ${esc(g.home)}<small>${esc(new Date(g.kickoff_utc).toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'America/New_York'}))} · ${esc(g.time_et)} ET${g.neutral?' · Neutral field':''}</small></th><td>${spread(margin,g.home,g.away)}<small>${scenario?'QB scenario':'Saved '+esc(date(g.forecast_generated_at))}</small></td><td>${spread(g.market_home_margin,g.home,g.away)}<small>${esc(g.market_kind)}</small></td><td>${gap==null?'—':signed(gap)+' home pts'}</td><td class="nfl-team-cell">${esc(g.away)}: ${esc(awayName)}${final?'':status(awayName)}<br>${esc(g.home)}: ${esc(homeName)}${final?'':status(homeName)}<small>${final?'Pregame assumptions retained'+(g.actual_away_qb&&g.actual_home_qb?' · Actual: '+esc(g.actual_away_qb)+' / '+esc(g.actual_home_qb):''):'Depth-chart assumptions; availability may change'}</small></td><td><span class="nfl-status-pill ${scenario?'scenario':''}">${final?'Final':scenario?'Scenario':'Upcoming'}</span>${final?`<small>${g.away_score}–${g.home_score}<br>${g.forecast_kind==='saved'?'Saved forecast':'Retrospective'}</small>`:''}</td></tr>`;
    }).join('');
    $('nfl-market-time').textContent=games.length?`Market source: nflverse schedules · retrieved ${date(games[0].market_retrieved_at)}. Completed games show closing lines.`:'';
  }
  let resultsPage=0;
  function renderResults(){
    if(!$('nfl-result-rows'))return;
    const week=$('nfl-results-week').value,kind=$('nfl-results-kind').value,query=$('nfl-results-search').value.toLowerCase();
    const games=data.games.filter(g=>g.status==='Final'&&(week==='all'||g.week===Number(week))&&(kind==='all'||g.forecast_kind===kind)&&`${g.home} ${g.away} ${team(g.home).name} ${team(g.away).name} ${g.home==='LA'||g.away==='LA'?'LAR':''}`.toLowerCase().includes(query)).sort((a,b)=>b.kickoff_utc.localeCompare(a.kickoff_utc));
    const pages=Math.max(1,Math.ceil(games.length/20));resultsPage=Math.min(resultsPage,pages-1);
    $('nfl-result-rows').innerHTML=games.slice(resultsPage*20,resultsPage*20+20).map(g=>`<tr><td>${g.week}</td><th scope="row" class="nfl-team-cell">${esc(g.away)} ${g.neutral?'vs.':'at'} ${esc(g.home)}<small>${esc(g.date)}</small></th><td>${g.away_score}–${g.home_score}</td><td>${spread(g.forecast_home_margin,g.home,g.away)}</td><td>${spread(g.actual_home_margin,g.home,g.away)}</td><td>${g.forecast_home_margin==null?'—':Math.abs(g.forecast_home_margin-g.actual_home_margin).toFixed(1)}</td><td>${spread(g.market_home_margin,g.home,g.away)}</td><td class="nfl-team-cell">${g.forecast_kind==='saved'?'Saved before kickoff':'Retrospective replay'}<small>${g.forecast_kind==='saved'?esc(date(g.forecast_generated_at)):'Performance through Week '+g.forecast_rating_week}${g.home_qb&&g.away_qb?'<br>Assumed: '+esc(g.away_qb)+' / '+esc(g.home_qb):''}</small></td></tr>`).join('')||'<tr><td class="nfl-empty" colspan="8">No completed games match these filters.</td></tr>';
    $('nfl-results-status').textContent=`${games.length} completed ${games.length===1?'game':'games'} · 2026 only`;
    let pager=$('nfl-result-pager');if(!pager){pager=document.createElement('div');pager.id='nfl-result-pager';pager.className='nfl-pager';$('nfl-result-rows').closest('.nfl-table-scroll').after(pager);}
    pager.innerHTML=`<button class="nfl-button nfl-button-secondary" id="nfl-prev" ${resultsPage===0?'disabled':''}>Previous</button><span>Page ${resultsPage+1} of ${pages}</span><button class="nfl-button nfl-button-secondary" id="nfl-next" ${resultsPage===pages-1?'disabled':''}>Next</button>`;
    $('nfl-prev').addEventListener('click',()=>{resultsPage--;renderResults();});$('nfl-next').addEventListener('click',()=>{resultsPage++;renderResults();});
  }
  function refresh(){renderRankings();detail();renderSpreads();persist();}
  if($('nfl-team-select')){
    if(team(params.get('team')))$('nfl-team-select').value=params.get('team');
    $('nfl-team-select').addEventListener('change',()=>{qbControls();detail();});
    $('nfl-qb-select').addEventListener('change',()=>{const t=team($('nfl-team-select').value);if($('nfl-qb-select').value===t.expected_qb.id){delete state.qbs[t.abbr];state.rankTeams=state.rankTeams.filter(x=>x!==t.abbr);}else state.qbs[t.abbr]=$('nfl-qb-select').value;qbControls();refresh();});
    $('nfl-backup').addEventListener('change',()=>{const t=team($('nfl-team-select').value);if($('nfl-backup').checked)state.qbs[t.abbr]=t.qb_options.find(q=>q.id!==t.expected_qb.id).id;else{delete state.qbs[t.abbr];state.rankTeams=state.rankTeams.filter(x=>x!==t.abbr);}qbControls();refresh();});
    $('nfl-apply-ranks').addEventListener('change',()=>{const abbr=$('nfl-team-select').value;state.rankTeams=state.rankTeams.filter(x=>x!==abbr);if($('nfl-apply-ranks').checked)state.rankTeams.push(abbr);refresh();});
    $('nfl-reset').addEventListener('click',()=>{state.qbs={};state.rankTeams=[];qbControls();refresh();});qbControls();
  }
  document.querySelectorAll('[data-sort]').forEach(button=>button.addEventListener('click',()=>{const next=button.dataset.sort;if(next===sortKey)ascending=!ascending;else{sortKey=next;ascending=['rank','efficiency_rank','name'].includes(next);}if($('nfl-sort')&&[...$('nfl-sort').options].some(o=>o.value===next))$('nfl-sort').value=next;renderRankings();}));
  if($('nfl-sort')){$('nfl-sort').value=sortKey;$('nfl-sort').addEventListener('change',()=>{sortKey=$('nfl-sort').value;ascending=['rank','name','efficiency_rank'].includes(sortKey);renderRankings();});}
  $('nfl-search')?.addEventListener('input',renderRankings);
  if(view==='rankings')$('nfl-ranking-rows').addEventListener('click',event=>{const link=event.target.closest('[data-team]');if(link){event.preventDefault();$('nfl-team-select').value=link.dataset.team;qbControls();detail();location.hash='team-detail';$('nfl-team-select').focus({preventScroll:true});}});
  ['nfl-results-week','nfl-results-kind'].forEach(id=>$(id)?.addEventListener('change',()=>{resultsPage=0;renderResults();}));$('nfl-results-search')?.addEventListener('input',()=>{resultsPage=0;renderResults();});
  refresh();renderResults();
})();
