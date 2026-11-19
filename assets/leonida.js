(()=>{"use strict";
const root=document.querySelector("[data-leonida]");if(!root)return;
const W=820,H=780,R=W/H,
map=root.querySelector(".lm-map"),svg=root.querySelector(".lm-svg"),
pins=[...root.querySelectorAll(".lm-pin")],cards=[...root.querySelectorAll(".lm-card")],
route=root.querySelector(".lm-route"),routeBg=root.querySelector(".lm-route-bg"),
car=root.querySelector(".lm-car"),plane=root.querySelector(".lm-plane"),
coords=root.querySelector(".lm-coords"),label=root.querySelector(".lm-route-label"),
reset=root.querySelector(".lm-reset"),
still=matchMedia("(prefers-reduced-motion:reduce)").matches,
pts=pins.map(p=>[+p.dataset.x,+p.dataset.y]),
names=pins.map(p=>p.textContent.trim().toUpperCase());
let vb={x:0,y:0,w:W},cur=0,run=0,started=false;

const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
lerp=(a,b,t)=>a+(b-a)*t,
wait=ms=>new Promise(r=>setTimeout(r,ms)),
tween=(ms,fn,id)=>new Promise(res=>{if(still||ms<=0){fn(1);return res()}const t0=performance.now();const f=now=>{if(id!==run)return res();const t=Math.min(1,(now-t0)/ms);fn(ease(t));t<1?requestAnimationFrame(f):res()};requestAnimationFrame(f)});

function draw(){
  const h=vb.w/R;
  svg.setAttribute("viewBox",`${vb.x.toFixed(1)} ${vb.y.toFixed(1)} ${vb.w.toFixed(1)} ${h.toFixed(1)}`);
  pins.forEach((p,i)=>{p.style.left=(pts[i][0]-vb.x)/vb.w*100+"%";p.style.top=(pts[i][1]-vb.y)/h*100+"%"});
  const cx=vb.x+vb.w/2,cy=vb.y+h/2;
  coords.textContent=`${(31.3-(cy-30)/104).toFixed(2)}°N ${(88-(cx-40)/90).toFixed(2)}°W`;
  reset.hidden=vb.w>W*.95;
  svg.style.setProperty("--k",W/vb.w);
  if(car.dataset.x)car.setAttribute("transform",`translate(${car.dataset.x} ${car.dataset.y}) scale(${vb.w/W})`);
}
// výrez okolo bodov, v pomere strán mapy a v jej hraniciach
function fit(list,pad,minW){
  const xs=list.map(p=>p[0]),ys=list.map(p=>p[1]);
  let x0=Math.min(...xs)-pad,x1=Math.max(...xs)+pad,y0=Math.min(...ys)-pad,y1=Math.max(...ys)+pad;
  let w=Math.max(x1-x0,(y1-y0)*R,minW);w=Math.min(w,W);
  const h=w/R,cx=(x0+x1)/2,cy=(y0+y1)/2;
  return{x:Math.max(0,Math.min(W-w,cx-w/2)),y:Math.max(0,Math.min(H-h,cy-h/2)),w};
}
const camera=(to,ms,id)=>{const from={...vb};return tween(ms,t=>{vb={x:lerp(from.x,to.x,t),y:lerp(from.y,to.y,t),w:lerp(from.w,to.w,t)};draw()},id)};
const curve=(a,b,bend)=>{const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2,dx=b[0]-a[0],dy=b[1]-a[1];return`M${a[0]} ${a[1]}Q${mx-dy*bend} ${my+dx*bend} ${b[0]} ${b[1]}`};

// vozidlo (bod alebo lietadlo) ide po trase a trasa sa za ním kreslí
function travel(d,obj,ms,id,turn){
  route.setAttribute("d",d);routeBg.setAttribute("d",d);
  const len=route.getTotalLength();
  routeBg.style.strokeDasharray=len;routeBg.style.strokeDashoffset=len;
  route.style.opacity=0;obj.style.opacity=1;
  return tween(ms,t=>{
    const at=len*t,p=route.getPointAtLength(at),q=route.getPointAtLength(Math.min(len,at+1)),r=route.getPointAtLength(Math.max(0,at-1));
    const ang=Math.atan2(q.y-r.y,q.x-r.x)*180/Math.PI,s=vb.w/W;
    obj.setAttribute("transform",`translate(${p.x} ${p.y}) rotate(${turn?ang+90:0}) scale(${s})`);
    if(obj===car){car.dataset.x=p.x;car.dataset.y=p.y}
    routeBg.style.strokeDashoffset=len*(1-t);
  },id).then(()=>{if(id===run){route.style.opacity=1;routeBg.style.strokeDasharray="none"}});
}

function show(i){
  cards.forEach((c,k)=>c.hidden=k!==i);
  pins.forEach((p,k)=>p.setAttribute("aria-pressed",k===i));
}
const zoomIn=i=>fit([pts[i]],10,W*.62);

async function go(i){
  i=(i+pins.length)%pins.length;if(i===cur&&started)return;
  const id=++run,from=cur;cur=i;show(i);
  label.textContent=`${root.dataset.route}: ${names[from]} → ${names[i]}`;
  plane.style.opacity=0;
  await camera(fit([pts[from],pts[i]],90,W*.4),650,id);if(id!==run)return;
  await travel(curve(pts[from],pts[i],.18),car,Math.min(1500,500+Math.hypot(pts[i][0]-pts[from][0],pts[i][1]-pts[from][1])*2.2),id);if(id!==run)return;
  await camera(zoomIn(i),800,id);
}

async function intro(){
  const id=++run;started=true;draw();
  if(still){root.classList.add("is-drawn","is-ready");show(0);travel(curve([W+60,-60],pts[0],-.12),plane,0,id,true);plane.style.opacity=0;vb=zoomIn(0);draw();return}
  await wait(1900);if(id!==run)return;
  root.classList.add("is-drawn");
  await travel(curve([W+80,-80],pts[0],-.14),plane,2300,id,true);if(id!==run)return;
  plane.style.opacity=0;car.style.opacity=1;car.dataset.x=pts[0][0];car.dataset.y=pts[0][1];draw();
  root.classList.add("is-ready");
  await camera(zoomIn(0),1100,id);
}

pins.forEach((p,i)=>p.addEventListener("click",()=>{root.classList.add("is-drawn","is-ready");go(i)}));
root.querySelector(".lm-prev").addEventListener("click",()=>go(cur-1));
root.querySelector(".lm-next").addEventListener("click",()=>go(cur+1));
reset.addEventListener("click",()=>{const id=++run;camera({x:0,y:0,w:W},700,id)});
map.addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key==="ArrowDown"){e.preventDefault();go(cur+1);pins[cur].focus()}else if(e.key==="ArrowLeft"||e.key==="ArrowUp"){e.preventDefault();go(cur-1);pins[cur].focus()}});

if(!still&&matchMedia("(hover:hover) and (min-width:701px)").matches){
  map.addEventListener("pointermove",e=>{const b=map.getBoundingClientRect(),x=(e.clientX-b.left)/b.width-.5,y=(e.clientY-b.top)/b.height-.5;map.style.setProperty("--ry",x*7+"deg");map.style.setProperty("--rx",-y*7+"deg")});
  map.addEventListener("pointerleave",()=>{map.style.setProperty("--ry","0deg");map.style.setProperty("--rx","0deg")});
}

draw();
const io=new IntersectionObserver(es=>es.forEach(e=>{
  root.classList.toggle("is-live",e.isIntersecting);
  if(e.isIntersecting&&!started){root.classList.add("is-on");intro()}
}),{threshold:.3});
io.observe(map);
})();
