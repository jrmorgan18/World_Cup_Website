const {test}=require('node:test');
const assert=require('node:assert/strict');
const {comparison,grade,weeklyRecords}=require('../assets/js/nfl-results.js');
const game=(model,market,actual,extra={})=>({status:'Final',home:'HOME',away:'AWAY',forecast_home_margin:model,market_home_margin:market,actual_home_margin:actual,...extra});

test('a stronger favorite recommendation wins, loses or pushes at the closing line',()=>{
  assert.deepEqual(grade(game(9,7,9)),{key:'win',label:'Winner',team:'HOME',line:-7});
  assert.equal(grade(game(9,7,6)).key,'loss');assert.equal(grade(game(9,7,7)).key,'push');
});
test('a weaker favorite implies taking the underdog even when the favorite wins',()=>{
  assert.deepEqual(grade(game(5,7,6)),{key:'win',label:'Winner',team:'AWAY',line:7});
  assert.equal(grade(game(5,7,8)).key,'loss');
});
test('away favorites and home underdogs preserve the home-margin sign convention',()=>{
  assert.deepEqual(grade(game(-9,-7,-9)),{key:'win',label:'Winner',team:'AWAY',line:-7});
  assert.deepEqual(grade(game(-5,-7,-6)),{key:'win',label:'Winner',team:'HOME',line:7});
});
test('half-point lines cannot push and tied games are graded against the spread',()=>{
  assert.equal(grade(game(9,7.5,7)).key,'loss');assert.equal(grade(game(5,7.5,7)).key,'win');
  assert.equal(grade(game(2,0,0)).key,'push');assert.equal(grade(game(0,3,0)).key,'win');
});
test('recommendations use full precision and exact model/market ties have no edge',()=>{
  assert.equal(grade(game(7,7,9)).key,'no-edge');assert.equal(grade(game(7.004,7,9)).key,'win');
  assert.equal(grade(game(-.04,0,1)).key,'loss');
});
test('displayed actual-starter corrections determine the displayed comparison; zero is retained',()=>{
  assert.equal(grade(game(9,7,6)).key,'loss');
  assert.deepEqual(grade(game(9,7,6,{display_home_margin:5})),{key:'win',label:'Winner',team:'AWAY',line:7});
  assert.equal(grade(game(9,7,6,{display_home_margin:0})).team,'AWAY');
});
test('missing inputs and games without a final score never manufacture a result',()=>{
  for(const field of ['forecast_home_margin','market_home_margin','actual_home_margin']){
    for(const value of [null,undefined,NaN,Infinity])assert.equal(grade({...game(9,7,9),[field]:value}).key,'unavailable');
  }
  assert.equal(grade(game(9,7,9,{status:'Upcoming'})).key,'pending');
});

test('weekly records count every matching game before pagination and keep pushes separate',()=>{
  const games=Array.from({length:25},(_,i)=>game(9,7,i<21?9:i<24?6:7,{week:6}));
  games.push(game(5,7,6,{week:5}));
  assert.deepEqual(weeklyRecords(games),[
    {week:6,wins:21,losses:3,pushes:1,excluded:0},
    {week:5,wins:1,losses:0,pushes:0,excluded:0}
  ]);
});
test('weekly records exclude missing lines and no-edge games, omit pending weeks, and honor filtered input',()=>{
  const games=[game(9,7,9,{week:6,forecast_kind:'saved'}),game(5,7,8,{week:6,forecast_kind:'retrospective'}),
    game(7,7,9,{week:6}),game(9,null,9,{week:6}),game(9,7,9,{week:7,status:'Upcoming'})];
  assert.deepEqual(weeklyRecords(games),[{week:6,wins:1,losses:1,pushes:0,excluded:2}]);
  assert.deepEqual(weeklyRecords(games.filter(g=>g.forecast_kind==='saved')),[{week:6,wins:1,losses:0,pushes:0,excluded:0}]);
  assert.deepEqual(weeklyRecords([]),[]);
});
test('weekly records use the same actual-starter correction as individual ATS results',()=>{
  assert.deepEqual(weeklyRecords([game(9,7,6,{week:6,display_home_margin:5})]),[{week:6,wins:1,losses:0,pushes:0,excluded:0}]);
});

const timedGame=(model,quotes,extra={})=>{
  const g=game(model,7,7,{game_id:'2026_07_A_B',week:7,forecast_kind:'saved',
    forecast_generated_at:'2026-10-20T12:00:00Z',kickoff_utc:'2026-10-25T17:00:00Z',...extra});
  g.market_history=quotes.map((home_margin,i)=>({game_id:g.game_id,home_margin,forecast_home_margin:model,
    forecast_generated_at:g.forecast_generated_at,observed_at:`2026-10-${20+i}T12:00:00Z`,recorded_at:`2026-10-${20+i}T12:01:00Z`}));
  return g;
};

test('first/best recorded and closing can fairly produce different ATS results',()=>{
  const g=timedGame(9,[7.5,6.5,7]);
  assert.equal(comparison(g,'first').market,7.5);
  assert.equal(comparison(g,'best').market,6.5);
  assert.equal(grade(g,'first').key,'loss');
  assert.equal(grade(g,'best').key,'win');
  assert.equal(grade(g,'closing').key,'push');
  assert.deepEqual(weeklyRecords([g],'best'),[{week:7,wins:1,losses:0,pushes:0,excluded:0}]);
});

test('best quote is selected by gap to the saved model, without looking at the result',()=>{
  const g=timedGame(5,[3,8,7]);
  assert.equal(comparison(g,'best').market,8);
  assert.equal(grade(g,'best').team,'AWAY');
  assert.equal(comparison({...g,actual_home_margin:100},'best').market,8);
  assert.equal(comparison({...g,actual_home_margin:-100},'best').market,8);
  const tied=timedGame(5,[3,7]);
  assert.equal(comparison(tied,'best').market,3);
});

test('early-price evaluation cannot use retrospective QB knowledge or borrow another forecast revision',()=>{
  const g=timedGame(9,[7],{display_home_margin:5,lineup_changed:true});
  assert.equal(grade(g,'closing').team,'AWAY');
  assert.equal(grade(g,'first').team,'HOME');
  assert.equal(comparison({...g,forecast_generated_at:'2026-10-21T12:00:00Z'},'best').market,null);
  assert.equal(comparison({...g,forecast_home_margin:10},'best').market,null);
});

test('missing or late history stays unavailable rather than silently substituting closing',()=>{
  const g=timedGame(9,[]);
  assert.equal(grade(g,'best').key,'unavailable');
  assert.equal(grade({...g,forecast_kind:'retrospective'},'first').key,'unavailable');
  const late=timedGame(9,[1]);late.market_history[0].recorded_at=late.kickoff_utc;
  assert.equal(grade(late,'best').key,'unavailable');
  assert.deepEqual(weeklyRecords([g],'first'),[{week:7,wins:0,losses:0,pushes:0,excluded:1}]);
  assert.equal(grade({...g,status:'Upcoming'},'best').key,'pending');
});
