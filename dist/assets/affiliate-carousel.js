(()=>{
const track=document.getElementById('affiliateTrack');if(!track)return;
const originals=[...track.children],n=originals.length,count=document.getElementById('affiliateCount'),pause=document.getElementById('affiliatePause');
if(!n)return;
let index=1,timer,settle,paused=false;
const first=originals[0].cloneNode(true),last=originals[n-1].cloneNode(true);
[first,last].forEach(el=>{el.setAttribute('aria-hidden','true');el.tabIndex=-1});
track.prepend(last);track.append(first);
const cards=[...track.children];
originals.forEach((el,i)=>{const title=el.querySelector('h3')?.textContent||`제휴 배너 ${i+1}`;el.setAttribute('aria-label',`${i+1} / ${n} · ${title}`)});
function logical(i){return ((i-1+n)%n)+1}
function updateCount(i=index){count.textContent=`${logical(i)} / ${n}`}
function jump(i,smooth=true){
  index=Math.max(0,Math.min(n+1,i));
  const card=cards[index],trackRect=track.getBoundingClientRect();
  const left=track.scrollLeft+card.getBoundingClientRect().left-trackRect.left-(track.clientWidth-card.offsetWidth)/2;
  track.scrollTo({left,behavior:smooth?'smooth':'auto'});
  updateCount(index);
}
function stop(){clearInterval(timer)}
function start(){stop();if(!paused&&!document.hidden)timer=setInterval(()=>jump(index+1),5000)}
function state(){pause.textContent=paused?'▶':'Ⅱ';pause.setAttribute('aria-label',paused?'자동 넘김 재생':'자동 넘김 일시정지');start()}
track.addEventListener('scroll',()=>{
  clearTimeout(settle);
  settle=setTimeout(()=>{
    const center=track.getBoundingClientRect().left+track.clientWidth/2;
    index=cards.reduce((best,el,i)=>Math.abs(el.getBoundingClientRect().left+el.offsetWidth/2-center)<Math.abs(cards[best].getBoundingClientRect().left+cards[best].offsetWidth/2-center)?i:best,0);
    if(index===0)jump(n,false);else if(index===n+1)jump(1,false);else updateCount(index);
  },180);
},{passive:true});
function move(delta){let next=index+delta;if(next<0)next=n;if(next>n+1)next=1;jump(next);start()}
document.getElementById('affiliatePrev').onclick=()=>move(-1);
document.getElementById('affiliateNext').onclick=()=>move(1);
pause.onclick=()=>{paused=!paused;state()};
track.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(e.key==='ArrowRight'?1:-1)}});
track.addEventListener('pointerdown',stop);window.addEventListener('pointerup',start);window.addEventListener('pointercancel',start);
track.addEventListener('mouseenter',stop);track.addEventListener('mouseleave',start);track.addEventListener('focusin',stop);track.addEventListener('focusout',start);
document.addEventListener('visibilitychange',()=>document.hidden?stop():start());
function detail(el){const image=el.querySelector('img');const d=document.createElement('dialog');d.style.cssText='width:min(92vw,680px);border:1px solid var(--line);border-radius:16px;background:var(--bg);color:var(--ink);padding:20px';const title=document.createElement('h3');title.textContent=el.querySelector('h3').textContent;const img=image.cloneNode();img.style.cssText='width:100%;height:auto;display:block;margin:20px 0';const close=document.createElement('button');close.textContent='닫기';close.className='btn wide';close.onclick=()=>d.close();d.append(title,img,close);document.body.append(d);d.addEventListener('close',()=>d.remove());d.showModal()}
track.addEventListener('click',e=>{const el=e.target.closest('[data-banner-detail]');if(el)detail(el)});
track.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-banner-detail]')){e.preventDefault();detail(e.target)}});
new ResizeObserver(()=>{if(track.offsetWidth)jump(index,false)}).observe(track);
requestAnimationFrame(()=>jump(1,false));state();
})();
