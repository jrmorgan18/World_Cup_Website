const {test}=require('node:test');
const assert=require('node:assert/strict');
const {grade}=require('../assets/js/nfl-results.js');
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
