/* Pure injury-scenario arithmetic, shared with regression checks. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.NFLInjuries=api;})(typeof globalThis==='object'?globalThis:this,()=>{
  'use strict';
  const groups=['OL','REC','DB','FRONT','LB','RB'];
  function valid(entry){return !!entry&&typeof entry.points==='number'&&Number.isFinite(entry.points)&&Math.abs(entry.points)<=6&&Math.abs(entry.points*4-Math.round(entry.points*4))<1e-8;}
  function sanitize(value,teams){
    const out={};if(!value||typeof value!=='object')return out;
    for(const team of teams){const input=value[team];if(!input||typeof input!=='object')continue;const clean={};
      for(const group of groups){const e=input[group];if(!valid(e)||e.points===0)continue;
        clean[group]={points:e.points,applyRanks:e.applyRanks===true,note:String(e.note||'').slice(0,1000),source:safeUrl(e.source),direction:e.direction==='return'?'return':'loss'};
      }if(Object.keys(clean).length)out[team]=clean;
    }return out;
  }
  function total(clusters,team,ranksOnly=false){return Object.values(clusters?.[team]||{}).filter(e=>valid(e)&&(!ranksOnly||e.applyRanks)).reduce((n,e)=>n+e.points,0);}
  function centered(clusters,teams){const raw=teams.map(t=>total(clusters,t,true)),mean=raw.reduce((a,b)=>a+b,0)/teams.length;return Object.fromEntries(teams.map((t,i)=>[t,raw[i]-mean]));}
  function margin(base,home,away,clusters,eligible=true){return base==null?null:base+(eligible?total(clusters,home)-total(clusters,away):0);}
  function net(current,embedded){return Number(current)-Number(embedded);}
  function eligible(game,now=Date.now()){return game.status!=='Final'&&new Date(game.kickoff_utc).getTime()>now;}
  function safeUrl(value){try{const u=new URL(String(value||''));return ['https:','http:'].includes(u.protocol)?u.href:'';}catch{return '';}}
  return {groups,valid,sanitize,total,centered,margin,net,eligible,safeUrl};
});
