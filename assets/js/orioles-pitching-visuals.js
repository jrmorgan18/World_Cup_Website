/* Native SVG charts. The accompanying HTML tables remain available without JS. */
(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs = {}, text) => {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k,v));
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const num = (v,unit) => unit === '%' ? v.toFixed(1)+'%' : unit === 'wins' ? (v>0?'+':'')+v.toFixed(1) : unit === 'ERA' || unit === 'ERA / FIP' ? v.toFixed(2) : v.toFixed(1);
  document.querySelectorAll('[data-pitching-chart]').forEach(canvas => {
    const figure=canvas.closest('figure');
    const c=JSON.parse(figure.querySelector('.pitching-config').textContent);
    const tooltip=document.createElement('div');
    tooltip.className='pitching-tooltip'; tooltip.hidden=true; tooltip.role='tooltip';
    tooltip.id='pitching-tooltip-'+canvas.dataset.pitchingChart; figure.append(tooltip);
    let active=null;
    function hide() { tooltip.hidden=true; if(active) active.removeAttribute('aria-describedby'); active=null; }
    function show(mark) {
      active=mark; tooltip.textContent=mark.dataset.tooltip; tooltip.hidden=false;
      mark.setAttribute('aria-describedby',tooltip.id);
      const b=mark.getBoundingClientRect(),t=tooltip.getBoundingClientRect();
      tooltip.style.left=Math.max(12,Math.min(window.innerWidth-t.width-12,b.x+b.width/2-t.width/2))+'px';
      tooltip.style.top=Math.max(8,Math.min(window.innerHeight-t.height-8,b.y-t.height-10))+'px';
    }
    canvas.addEventListener('pointerover',e=>{ const m=e.target.closest('[data-tooltip]'); if(m)show(m); });
    canvas.addEventListener('pointerout',e=>{if(!e.relatedTarget || !canvas.contains(e.relatedTarget))hide();});
    canvas.addEventListener('focusin',e=>{if(e.target.dataset.tooltip)show(e.target);});
    canvas.addEventListener('focusout',hide);
    canvas.addEventListener('click',e=>{const m=e.target.closest('[data-tooltip]');if(m)show(m);else hide();});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')hide();});
    document.addEventListener('pointerdown',e=>{if(!figure.contains(e.target))hide();});
    window.addEventListener('scroll',hide,{passive:true});
    function render() {
      hide(); canvas.replaceChildren();
      const w=Math.floor(canvas.getBoundingClientRect().width); if(w<100)return;
      const color=getComputedStyle(figure);
      const colors=['--pv-orange','--pv-neutral'].map(x=>color.getPropertyValue(x).trim());
      const paint=name=>color.getPropertyValue('--pv-'+name).trim();
      let h=c.kind==='horizontal'?c.labels.length*68+44:c.kind==='scatter'?320:280;
      const svg=el('svg',{viewBox:`0 0 ${w} ${h}`,width:w,height:h,role:'group','aria-label':c.title});
      svg.append(el('title',{},c.title));
      const text=(x,y,s,cls='pv-axis',anchor='start',size=12)=>svg.appendChild(el('text',{x,y,class:cls,'text-anchor':anchor,'font-size':size},s));
      const line=(x1,y1,x2,y2,cls='pv-grid')=>svg.appendChild(el('line',{x1,y1,x2,y2,class:cls}));
      function mark(tag,attrs,label) {
        const n=el(tag,{...attrs,tabindex:0,role:'img','aria-label':label,'data-tooltip':label,class:'pv-mark'});
        n.append(el('title',{},label)); svg.append(n); return n;
      }
      if(c.series) {
        const legend=document.createElement('div');legend.className='pitching-legend';
        c.series.forEach((s,j)=>{const item=document.createElement('span'),swatch=document.createElement('i');swatch.style.background=colors[j];item.append(swatch,document.createTextNode(s.name));legend.append(item);});
        canvas.append(legend);
        const m={l:37,r:12,t:16,b:c.annotations?65:36},pw=w-m.l-m.r,ph=h-m.t-m.b;
        for(let i=0;i<=4;i++){const v=c.max*i/4,y=m.t+ph*(1-i/4);line(m.l,y,w-m.r,y);text(m.l-7,y+4,c.unit==='%'?v.toFixed(0)+'%':String(v),'pv-axis','end');}
        const n=c.labels.length;
        const x=i=>c.kind==='line'?m.l+pw*i/(n-1):m.l+pw*(i+.5)/n;
        const y=v=>m.t+ph*(1-v/c.max);
        c.labels.forEach((label,i)=>{
          const parts=label.includes(' 2026')?[label.replace(' 2026',''),'2026']:[label];
          parts.forEach((s,j)=>text(x(i),h-m.b+20+j*14,s,'pv-axis','middle',n>4?11:12));
          if(c.annotations)text(x(i),h-8,c.annotations[i],'pv-label','middle',w<400?10:12);
        });
        c.series.forEach((s,j)=>{
          if(c.kind==='line')svg.append(el('polyline',{points:s.values.map((v,i)=>`${x(i)},${y(v)}`).join(' '),fill:'none',stroke:colors[j],'stroke-width':2.5,'stroke-dasharray':j?'6 4':''}));
          s.values.forEach((v,i)=>{
            const value=s.display?s.display[i]:num(v,c.unit),label=`${s.name} · ${c.labels[i]}: ${value}${c.unit==='%'?'':' '+c.unit}${c.annotations?' · '+c.annotations[i]:''}`;
            if(c.kind==='line') {
              const g=mark('g',{},label);
              g.append(el('circle',{cx:x(i),cy:y(v),r:15,fill:'transparent'}),el('circle',{cx:x(i),cy:y(v),r:j?4:4.5,fill:colors[j],stroke:paint('bg'),'stroke-width':1.5}));
            } else {
              const bw=Math.min(24,pw/n*.32),xx=x(i)+(j===0?-bw-2:2);
              mark('rect',{x:xx,y:y(v),width:bw,height:ph*v/c.max,fill:colors[j]},label);
            }
          });
        });
      } else if(c.kind==='horizontal') {
        const m={l:6,r:43,t:0,b:27},pw=w-m.l-m.r;
        const min=c.min||0,max=c.max,x=v=>m.l+pw*(v-min)/(max-min),zero=x(0);
        // Labels sit above each bar, preserving room for long names on phones.
        for(let i=0;i<c.labels.length;i++) {
          const y=i*68+19,v=c.values[i];
          text(m.l,y,c.labels[i],'pv-label','start',w<350?12:14);
          if(c.secondary)text(m.l,y+16,c.secondary[i],'pv-axis','start',11);
          const by=y+(c.secondary?23:12),col=c.colors?paint(c.colors[i]):v<0?paint('negative'):c.highlight?(c.highlight.includes(c.labels[i])?colors[0]:colors[1]):colors[0];
          mark('rect',{x:Math.min(zero,x(v)),y:by,width:Math.max(2,Math.abs(x(v)-zero)),height:14,fill:col},`${c.labels[i]}: ${num(v,c.unit)} ${c.unit}${c.secondary?' · '+c.secondary[i]:''}`);
          text((v<0?zero:x(v))+5,by+12,num(v,c.unit),'pv-label','start',12);
        }
        if(min<0)line(zero,34,zero,h-30,'pv-zero');
        [min,(min+max)/2,max].forEach(v=>text(x(v),h-2,(c.unit==='wins'?(v>0?'+':''):'')+v+(c.unit==='wins'?' wins':''),'pv-axis',v===min?'start':v===max?'end':'middle',11));
      } else if(c.kind==='scatter') {
        const m={l:36,r:18,t:28,b:46},pw=w-m.l-m.r,ph=h-m.t-m.b;
        const x=v=>m.l+(v-9)/20*pw,y=v=>m.t+(2.9-v)/1.5*ph;
        [1.5,2,2.5].forEach(v=>{line(m.l,y(v),w-m.r,y(v));text(m.l-6,y(v)+4,v.toFixed(1),'pv-axis','end');});
        [10,15,20,25].forEach(v=>text(x(v),h-27,'$'+v+'M','pv-axis','middle'));
        text(w/2,h-5,'Estimated annual salary','pv-axis','middle');text(m.l,13,'Projected WAR','pv-axis');
        const offsets={'Griffin':[0,-12],'Imanaga':[8,4],'King':[0,-13],'Holmes':[0,-12],'Mahle':[0,-13],'Peterson':[5,19],'Itoh':[-6,-13]};
        c.points.forEach(p=>{
          const surname=p.name.split(' ').at(-1),[dx,dy]=offsets[surname];
          const g=mark('g',{},`${p.name}: $${p.x}M estimated annual salary · ${p.y.toFixed(1)} projected WAR`);
          g.append(el('circle',{cx:x(p.x),cy:y(p.y),r:17,fill:'transparent'}),el('circle',{cx:x(p.x),cy:y(p.y),r:6,fill:surname==='Imanaga'?colors[0]:colors[1],stroke:paint('bg'),'stroke-width':1.5}));
          text(x(p.x)+dx,y(p.y)+dy,surname,'pv-label',surname==='Imanaga'?'start':'middle',12);
        });
      }
      canvas.append(svg);
      figure.querySelector('.pitching-chart-help').hidden=false;
    }
    const resize=new ResizeObserver(render);resize.observe(canvas);
    render();
  });
})();
