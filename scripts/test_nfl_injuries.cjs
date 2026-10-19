const {test}=require('node:test');
const assert=require('node:assert/strict');
const i=require('../assets/js/nfl-injuries.js');
const e=(points,applyRanks=false)=>({points,applyRanks});
test('net effect reverses an impairment already embedded in the rating',()=>{
  assert.equal(i.net(-2,-1.25),-.75);assert.equal(i.net(0,-1.25),1.25);assert.equal(i.net(-1,-1),0);
});
test('home and away scenarios change the margin once with opposite signs',()=>{
  assert.equal(i.margin(3,'H','A',{H:{OL:e(-1)},A:{DB:e(.75)}}),1.25);
  assert.equal(i.margin(3,'H','A',{A:{DB:e(-1.5)}}),4.5);
  assert.equal(i.margin(null,'H','A',{}),null);
});
test('weekly-only scenarios do not change ranks; rank effects stay centered',()=>{
  const c={H:{OL:e(-1,true),REC:e(-.5,false)},A:{DB:e(.75,true)}};
  assert.equal(i.total(c,'H'),-1.5);assert.equal(i.total(c,'H',true),-1);
  const rank=i.centered(c,['H','A','C']);
  assert.ok(Math.abs(Object.values(rank).reduce((a,b)=>a+b,0))<1e-12);
  assert.equal(rank.H-rank.A,-1.75);
});
test('completed and already-started games cannot receive scenario changes',()=>{
  const now=Date.parse('2026-10-16T12:00:00Z');
  assert.equal(i.eligible({status:'Final',kickoff_utc:'2026-10-18T17:00:00Z'},now),false);
  assert.equal(i.eligible({status:'Upcoming',kickoff_utc:'2026-10-15T20:00:00Z'},now),false);
  assert.equal(i.eligible({status:'Upcoming',kickoff_utc:'2026-10-18T17:00:00Z'},now),true);
  assert.equal(i.margin(3,'H','A',{H:{OL:e(-1)}},false),3);
});
test('untrusted stored scenarios cannot inject unknown teams, groups or values',()=>{
  const c=i.sanitize({H:{OL:{...e(-1,true),source:'javascript:alert(1)'},DB:e(NaN),FRONT:e(20),REC:e(.3)},FAKE:{OL:e(-1)}},['H']);
  assert.deepEqual(Object.keys(c),['H']);assert.deepEqual(Object.keys(c.H),['OL']);assert.equal(c.H.OL.source,'');
  assert.equal(i.valid({points:'-1'}),false);assert.equal(i.safeUrl('https://example.org/report'),'https://example.org/report');
});
