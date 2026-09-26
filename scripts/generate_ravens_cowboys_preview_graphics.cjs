#!/usr/bin/env node
// Companion graphics use the article's Friday reporting context and two-game sample.
const fs = require("node:fs");
const path = require("node:path");
const out = path.join(__dirname, "../assets/images/ravens/cowboys-week-three-2026");
fs.mkdirSync(out, { recursive: true });
const esc = s => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const text = (x, y, s, size=24, fill="#f4f4f7", weight=500, anchor="start") =>
  `<text x="${x}" y="${y}" fill="${fill}" font-family="Arial, Helvetica, sans-serif" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}">${esc(s)}</text>`;
const rect = (x,y,w,h) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="24" fill="#191b23" stroke="#6843a4" stroke-width="1.5"/>`;
const frame = (title, subtitle, desc, body, footer) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-labelledby="title desc">
<title id="title">${esc(title)}</title><desc id="desc">${esc(desc)}</desc>
<rect width="1200" height="675" fill="#101114"/><rect width="1200" height="112" fill="#302065"/>
${text(55,58,title,36,"#ffffff",800)}${text(55,92,subtitle,21,"#c4b8df")}
${body}
${text(55,652,footer,16,"#b5b6c0")}
</svg>\n`;
const topCards = [
  [55,305,"RAVENS · 1–1","155","Rush yards per game","+0.17 EPA per rush"],
  [420,305,"COWBOYS · 1–1","173.5","Rush yards allowed per game","+0.32 EPA per pass allowed"],
  [785,360,"FRIDAY MARKET","BAL −3.5","Total: 53.5","September 25 snapshot"]
].map(([x,w,label,big,line1,line2])=>rect(x,150,w,156)+text(x+22,186,label,21,"#dfb936",800)+text(x+22,233,big,38,"#f4f4f7",800)+text(x+22,268,line1,20,"#b5b6c0")+text(x+22,294,line2,20,"#b5b6c0")).join("\n");
const numbers = [
  ["126","QB rushing yards","allowed by Dallas"],
  ["43.8%","Ravens pressure rate","No. 5 in the NFL"],
  ["68.2%","Dallas third downs","converted · 15 of 22"],
  ["68.0%","Dallas third downs","allowed · 17 of 25"]
].map(([big,l1,l2],i)=>text(80+i*265,469,big,38,"#dfb936",800)+text(80+i*265,510,l1,22,"#f4f4f7",700)+text(80+i*265,545,l2,20,"#b5b6c0")).join("\n");
fs.writeFileSync(path.join(out,"ravens-cowboys-at-a-glance-2026.svg"),frame(
  "RAVENS vs. COWBOYS","Week 3 · Sunday, 4:25 ET · Maracanã Stadium, Rio",
  "Both teams are 1–1. Baltimore averages 155 rushing yards; Dallas allows 173.5. Dallas converts 68.2 percent of third downs and allows 68 percent.",
  topCards+rect(55,346,1090,264)+text(80,393,"THE FOUR NUMBERS TO KNOW",28,"#f4f4f7",800)+numbers,
  "DUAL EIGHTS · Article statistics through Week 2 · Market as of Friday · Two-game sample"));
const matchups = [
  ["Henry + Lamar vs. Dallas run fits","Dallas has allowed 347 rushing yards, including an NFL-high 126 to quarterbacks.","Baltimore's opportunity: force the edge and second level to choose."],
  ["Ravens pressure vs. Dak Prescott","Baltimore's 43.8% pressure rate only matters if coverage delays the quick throw.","The key: create immediate interior pressure and make Prescott hesitate."],
  ["Lamb + Ferguson vs. Ravens coverage","Lamb: 153 yards last week. Ferguson: two touchdowns against Washington.","Hamilton's role: disguise, coverage and pressure cannot all be his job at once."]
].map(([title,a,b],i)=>{
const y=137+i*162;return rect(55,y,1090,145)+`<circle cx="105" cy="${y+72}" r="31" fill="#4c338c"/>`+text(105,y+83,i+1,30,"#ffffff",800,"middle")+text(160,y+41,title,28,"#f4f4f7",800)+text(160,y+80,a,21,"#b5b6c0")+text(160,y+119,b,21,"#dfb936",600);
}).join("\n");
fs.writeFileSync(path.join(out,"ravens-cowboys-key-matchups-2026.svg"),frame(
  "THREE MATCHUPS THAT DECIDE IT","Ravens–Cowboys · Week 3",
  "Henry and Lamar against Dallas run defense; Ravens pressure against Dak Prescott; CeeDee Lamb and Jake Ferguson against Ravens coverage.",
  matchups,"DUAL EIGHTS · Baltimore wants to dictate on offense and finish possessions on defense"));
const injuryBody = rect(55,148,530,449)+rect(615,148,530,449)+
  text(80,194,"BALTIMORE · WATCH",28,"#dfb936",800)+
  text(80,248,"Zay Flowers · hamstring",27,"#f4f4f7",800)+
  text(80,281,"Returned to the field Friday.",22,"#b5b6c0")+
  text(80,312,"Availability and workload uncertain.",22,"#b5b6c0")+
  text(80,364,"Ronnie Stanley · toe",27,"#f4f4f7",800)+
  text(80,397,"Protection plan hinges on left tackle.",22,"#b5b6c0")+
  text(80,449,"Madubuike + Buchanan",27,"#f4f4f7",800)+
  text(80,482,"Full practices Wednesday and Thursday.",22,"#b5b6c0")+
  text(80,513,"Buchanan expected back; Madubuike trending.",21,"#b5b6c0")+
  text(80,563,"Hendrickson · managing a broken finger",21,"#b5b6c0")+
  text(640,194,"DALLAS · RULED OUT",28,"#dfb936",800)+
  text(640,256,"DeMarvion Overshown",28,"#f4f4f7",800)+text(640,289,"Linebacker",22,"#b5b6c0")+
  text(640,347,"Cobie Durant",28,"#f4f4f7",800)+text(640,380,"Cornerback",22,"#b5b6c0")+
  text(640,438,"Malik Hooker + P.J. Locke",28,"#f4f4f7",800)+text(640,471,"Safeties",22,"#b5b6c0")+
  text(640,539,"A depleted secondary and more responsibility",21,"#b5b6c0")+text(640,570,"for Dallas' rookie defenders.",21,"#b5b6c0");
fs.writeFileSync(path.join(out,"ravens-cowboys-injury-watch-2026.svg"),frame(
  "AVAILABILITY COULD CHANGE THE PLAN","Week 3 injury watch · As of Friday, September 25",
  "Baltimore is watching Flowers, Stanley, Madubuike and Buchanan. Dallas has ruled out Overshown, Durant, Hooker and Locke.",
  injuryBody,"DUAL EIGHTS · Reporting through Friday, September 25 · Check game-day inactives"));
const stats = JSON.parse(fs.readFileSync(path.join(__dirname, "../_data/ravens_dashboard_stats.json"), "utf8"));
if (stats.header.next_game.opponent_abbr !== "DAL" || stats.current_snapshot !== "2026-week-02") {
  throw new Error("This preview requires the Cowboys matchup through Week 2.");
}
const items = stats.header.next_game.matchup.items;
const label = (value, pct=false) => pct ? value.toFixed(1)+"%" : (value>=0?"+":"")+value.toFixed(2);
const cell = (x,y,value,rank) => text(x,y,value,34,"#f4f4f7",800)+
  `<rect x="${x}" y="${y+17}" width="72" height="34" rx="17" fill="${rank<=8?"#dfb936":rank<=16?"#6843a4":"#4a223f"}"/>`+
  text(x+36,y+42,"#"+rank,22,rank<=8?"#15121a":"#f4f4f7",800,"middle");
const panel = (y,kicker,left,right,rows) => rect(55,y,1090,284)+
  text(80,y+40,kicker.toUpperCase(),21,"#bda4e5",800)+
  text(80,y+82,left,28,"#ffffff",800)+text(1120,y+82,right,28,"#ffffff",800,"end")+
  rows.map((r,i)=> {
    const rowY=y+137+i*87;
    return text(600,rowY+15,r.name,24,"#cfc8d5",600,"middle")+
      cell(85,rowY,label(r.a.value,r.pct),r.a.rank)+
      cell(1010,rowY,label(r.b.value,r.pct),r.b.rank);
  }).join("");
const dnaBody = panel(176,"When the Ravens have the ball","RAVENS OFFENSE","COWBOYS DEFENSE",[
  {name:"EPA / play",a:items[0].ravens,b:items[0].opponent},
  {name:"Explosive-play rate",a:items[1].ravens,b:items[1].opponent,pct:true}
])+panel(485,"When the Cowboys have the ball","COWBOYS OFFENSE","RAVENS DEFENSE",[
  {name:"EPA / play",a:items[2].opponent,b:items[2].ravens},
  {name:"Red-zone TD rate",a:items[3].opponent,b:items[3].ravens,pct:true}
]);
fs.writeFileSync(path.join(out,"ravens-cowboys-matchup-dna.svg"),
  `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="840" viewBox="0 0 1200 840" role="img" aria-labelledby="title desc">
<title id="title">Ravens Cowboys Week 3 matchup profile</title>
<desc id="desc">Ravens offensive EPA per play is plus 0.22, fourth in the NFL, against Dallas defense plus 0.23, 30th. Dallas offensive EPA is plus 0.22, third, against Baltimore defense minus 0.02, 13th. Also compares explosive-play rate and red-zone touchdown rate.</desc>
<rect width="1200" height="840" fill="#101114"/><rect width="1200" height="140" fill="#302065"/>
${text(55,57,"RAVENS × COWBOYS",38,"#ffffff",800)}
${text(55,105,"MATCHUP DNA · THROUGH WEEK 2",25,"#dfb936",800)}
${text(1145,58,"WEEK 3 · 2026",22,"#c4b8df",700,"end")}
${text(1145,100,"League ranks: #1 best",21,"#c4b8df",500,"end")}
${dnaBody}
${text(55,812,"DUAL EIGHTS · Ravens Season Dashboard / nflverse · Two-game sample",18,"#b5b6c0")}
</svg>\n`);

console.log("Generated four Ravens–Cowboys companion graphics.");
