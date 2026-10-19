/* Closing-line grading for the displayed historical DEPI recommendation. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.NFLResults=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function grade(game){
    const empty=(key,label)=>({key,label,team:null,line:null});
    if(game.status!=='Final')return empty('pending','Pending');
    const model=game.display_home_margin??game.forecast_home_margin,market=game.market_home_margin,actual=game.actual_home_margin;
    if(![model,market,actual].every(Number.isFinite))return empty('unavailable','Unavailable');
    const edge=model-market;
    if(Math.abs(edge)<=1e-9)return empty('no-edge','No edge');
    const home=edge>0,cover=(home?1:-1)*(actual-market);
    return {key:Math.abs(cover)<1e-9?'push':cover>0?'win':'loss',
      label:Math.abs(cover)<1e-9?'Push':cover>0?'Winner':'Loser',
      team:home?game.home:game.away,line:home?-market:market};
  }
  function weeklyRecords(games){
    const weeks=new Map();
    for(const game of games){
      if(game.status!=='Final'||!Number.isInteger(game.week)||game.week<1)continue;
      if(!weeks.has(game.week))weeks.set(game.week,{week:game.week,wins:0,losses:0,pushes:0,excluded:0});
      const record=weeks.get(game.week),key=grade(game).key;
      if(key==='win')record.wins++;else if(key==='loss')record.losses++;else if(key==='push')record.pushes++;else record.excluded++;
    }
    return [...weeks.values()].sort((a,b)=>b.week-a.week);
  }
  return {grade,weeklyRecords};
});
