/* Timestamped market comparisons; best recorded never reads the final score. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.NFLResults=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function comparison(game,mode='closing'){
    if(mode==='closing')return {model:game.display_home_margin??game.forecast_home_margin,market:game.market_home_margin,
      label:game.status==='Final'?'Closing line':'Latest snapshot',observedAt:game.market_retrieved_at,count:null};
    if(!['first','best'].includes(mode))throw new Error('Unknown market comparison');
    const model=game.forecast_home_margin,forecast=Date.parse(game.forecast_generated_at),kickoff=Date.parse(game.kickoff_utc);
    const history=game.forecast_kind==='saved'&&Number.isFinite(model)?(game.market_history||[]).filter(r=>
      r.game_id===game.game_id&&Number.isFinite(r.home_margin)&&Number.isFinite(r.forecast_home_margin)&&
      Math.abs(r.forecast_home_margin-model)<1e-9&&Date.parse(r.forecast_generated_at)===forecast&&
      Date.parse(r.observed_at)<=Date.parse(r.recorded_at)&&forecast<=Date.parse(r.recorded_at)&&Date.parse(r.recorded_at)<kickoff
    ).sort((a,b)=>Date.parse(a.recorded_at)-Date.parse(b.recorded_at)||Date.parse(a.observed_at)-Date.parse(b.observed_at)):[];
    let selected=history[0];
    if(mode==='best')for(const row of history){
      if(Math.abs(model-row.home_margin)>Math.abs(model-selected.home_margin)+1e-9)selected=row;
    }
    return {model,market:selected?.home_margin??null,label:mode==='first'?'First recorded':'Best recorded',
      observedAt:selected?.observed_at??null,recordedAt:selected?.recorded_at??null,count:history.length};
  }
  function grade(game,mode='closing'){
    const empty=(key,label)=>({key,label,team:null,line:null});
    if(game.status!=='Final')return empty('pending','Pending');
    const {model,market}=comparison(game,mode),actual=game.actual_home_margin;
    if(![model,market,actual].every(Number.isFinite))return empty('unavailable','Unavailable');
    const edge=model-market;
    if(Math.abs(edge)<=1e-9)return empty('no-edge','No edge');
    const home=edge>0,cover=(home?1:-1)*(actual-market);
    return {key:Math.abs(cover)<1e-9?'push':cover>0?'win':'loss',
      label:Math.abs(cover)<1e-9?'Push':cover>0?'Winner':'Loser',
      team:home?game.home:game.away,line:home?-market:market};
  }
  function weeklyRecords(games,mode='closing'){
    const weeks=new Map();
    for(const game of games){
      if(game.status!=='Final'||!Number.isInteger(game.week)||game.week<1)continue;
      if(!weeks.has(game.week))weeks.set(game.week,{week:game.week,wins:0,losses:0,pushes:0,excluded:0});
      const record=weeks.get(game.week),key=grade(game,mode).key;
      if(key==='win')record.wins++;else if(key==='loss')record.losses++;else if(key==='push')record.pushes++;else record.excluded++;
    }
    return [...weeks.values()].sort((a,b)=>b.week-a.week);
  }
  return {comparison,grade,weeklyRecords};
});
