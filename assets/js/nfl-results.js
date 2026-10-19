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
  return {grade};
});
