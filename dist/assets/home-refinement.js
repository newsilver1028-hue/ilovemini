(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const home = $('#home'), ledger = $('#ledger'), member = $('#membershipCard'), banner = $('.affiliate-banner-section'), album = $('.mini-album-section'), search = $('.cafe-ai-card'), notices = $('#cafe-notice-section');
  const cafeView = document.createElement('section');
  cafeView.id = 'cafe'; cafeView.className = 'view cafe-view';
  cafeView.innerHTML = '<div class="pagehead"><div class="overline">ILOVEMINI CAFE</div><h1>카페</h1><p>아이러브미니 공개 게시글을 검색하고 카페 소식을 확인하세요.</p></div>';
  home.after(cafeView);
  // Keep the home focused on the garage and place community content in its own tab.
  if (banner) home.append(banner);
  if (search) cafeView.append(search);
  [notices,album].filter(Boolean).forEach(el => el.remove());
  const cafePosts = document.createElement('section');
  cafePosts.id = 'cafePostsSection'; cafePosts.className = 'section cafe-posts-section';
  cafePosts.innerHTML = '<div class="secthead"><h2>아이러브미니 카페 게시글</h2><small>공개글 검색</small></div><p class="smallnote">카페 글 검색을 누르면 공개 게시글을 불러옵니다. 글을 누르면 네이버 카페에서 열립니다.</p><div id="cafePostsStatus" class="cafe-posts-status" role="status" aria-live="polite">카페 게시글을 불러오는 중…</div><div id="cafePostsList" class="cafe-posts-list"></div><a class="btn outline wide cafe-open-link" href="https://m.cafe.naver.com/minilover/" target="_blank" rel="noopener noreferrer">네이버 카페 열기</a>' ;
  cafeView.append(cafePosts);
  const profile = $('#profile');
  if (member && profile) {
    const profileHead = $('.profilehead', profile);
    if (profileHead) profileHead.after(member); else profile.prepend(member);
    $('#profileMemberGrade', profile)?.remove();
    const gradeLink = $('.attendance-head .textbtn', member);
    if (gradeLink) {
      gradeLink.textContent = '등급 안내';
      gradeLink.onclick = () => { const guide=$('.member-grade-guide',member); if(guide){guide.open=true;guide.scrollIntoView({behavior:'smooth',block:'center'});} };
    }
  }
  const quick = document.createElement('div'); quick.className = 'home-quick-actions';
  quick.innerHTML = `<button type="button" onclick="openEntry()"><span>기록 추가</span><small>주유·정비·소모품 기록</small></button><button type="button" onclick="openPartnerFinder()"><span>업체 찾기</span><small>분야·지역별 예약 요청</small></button>`;
  $('.home-car-card',home)?.after(quick);
  if (ledger) {
    const vehicleCard = $('#ledgerVehicleCard', ledger);
    const reminderSection = $('.reminder', ledger)?.closest('.section');
    const monthCard = $('.ledger-month-card', ledger);
    const passportCard = $('#vehiclePassportCard', ledger);
    const recordSection = $('.month-total', ledger)?.closest('.section');
    if (vehicleCard && reminderSection) vehicleCard.after(reminderSection);
    if (reminderSection && monthCard) reminderSection.after(monthCard);
    if (monthCard && passportCard) monthCard.after(passportCard);
    if (passportCard && recordSection) {
      $('.passport-section-title', passportCard)?.remove();
      $('#passportTimeline', passportCard)?.remove();
      const heading = $('.secthead h2', recordSection);
      if (heading) heading.textContent = '기록 내역';
      const listHeading = $('.month-total .row b', recordSection);
      if (listHeading) listHeading.textContent = '전체 기록';
      passportCard.append(recordSection);
    }
  }
  if (search) search.id = 'miniDoctorQa';
  const grid = $('.mini-album-grid');
  if(grid) {
    const controls = document.createElement('div'); controls.className='album-controls';
    controls.innerHTML='<button type="button" aria-label="이전 사진">‹</button><span aria-live="polite"></span><button type="button" aria-label="다음 사진">›</button>';
    album.append(controls);
    const [prev,next] = controls.querySelectorAll('button'), counter=controls.querySelector('span');
    const step=()=>grid.firstElementChild.getBoundingClientRect().width+12;
    const update=()=>{prev.disabled=grid.scrollLeft<2;next.disabled=grid.scrollLeft>=grid.scrollWidth-grid.clientWidth-2;counter.textContent=`${Math.min(grid.children.length,Math.round(grid.scrollLeft/step())+1)} / ${grid.children.length}`;};
    prev.onclick=()=>grid.scrollBy({left:-step(),behavior:'smooth'});next.onclick=()=>grid.scrollBy({left:step(),behavior:'smooth'});
    grid.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);
    grid.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();grid.scrollBy({left:step()*(e.key==='ArrowRight'?1:-1),behavior:'smooth'});}});
    let down=false,start=0,left=0,dragged=false;
    grid.addEventListener('pointerdown',e=>{if(e.pointerType!=='mouse'||e.button!==0)return;down=true;dragged=false;start=e.clientX;left=grid.scrollLeft;});
    window.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-start;if(Math.abs(dx)>5){dragged=true;grid.style.scrollSnapType='none';grid.scrollLeft=left-dx;}});
    window.addEventListener('pointerup',()=>{down=false;grid.style.scrollSnapType='';});
    grid.addEventListener('dragstart',e=>e.preventDefault());grid.addEventListener('click',e=>{if(dragged){e.preventDefault();e.stopPropagation();dragged=false;}},true);
    requestAnimationFrame(update);
  }
  const section=document.createElement('section');section.id='partnerFinder';section.className='partner-finder';
  section.innerHTML=`<div class="secthead"><h2>업체 찾기 · 예약</h2><small>PARTNER BOOKING</small></div><div class="finder-filters"><input id="finderQuery" type="search" placeholder="업체명·정비 항목 검색" aria-label="예약 업체 검색"><select id="finderRegion" aria-label="업체 지역"><option value="">전체 지역</option><option value="서울/경기 협력업체">서울·경기·인천</option><option value="전라/경상/충청 협력업체">부산·충청 등 지방</option></select></div><div class="finder-result-meta"><span>검색 결과</span><b id="finderCount" aria-live="polite"></b></div><div id="finderResults" class="finder-results"></div>`;
  const partnersView=$('#partners'), pageHead=$('.pagehead',partnersView);
  // Replace the duplicated legacy category/search/list and the separate map finder with one workspace.
  pageHead.querySelector('h1').textContent='협력업체 찾기';
  pageHead.querySelector('p').textContent='분야와 지역으로 찾고, 지도 확인과 예약 요청을 한곳에서 진행하세요.';
  partnersView.querySelector('label:has(#search)')?.remove();partnersView.querySelector('#filters')?.remove();partnersView.querySelector('.row')?.remove();partnersView.querySelector('#shoplist')?.remove();
  partnersView.querySelectorAll('.smallnote').forEach(el=>{if(el.textContent.includes('업체 정보·영업시간'))el.remove();});
  pageHead.after(section);
  const categoryChoices=['전체','정비','사고수리','오디오·전장','차량유리','휠·타이어','부품·튜닝','신차패키지','수도권','지방'];
  section.querySelector('.finder-filters').insertAdjacentHTML('afterend',`<div class="finder-categories" role="group" aria-label="업체 분야">${categoryChoices.map((name,i)=>`<button type="button" data-category="${esc(name)}" aria-pressed="${i===0}">${esc(name)}</button>`).join('')}</div><div class="finder-map-heading"><b id="finderMapTitle">Google 업체 지도</b><span id="finderMapHint">업체별 지도·상담 버튼으로 위치를 확인하거나 문의할 수 있어요.</span></div><div class="finder-map" id="finderMapPanel"><iframe id="finderMapFrame" title="협력업체 지도" src="https://www.google.com/maps?q=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>`);
  let selectedCategory='전체', selectedMapId='';
  const normalize=value=>String(value??'').toLocaleLowerCase('ko-KR').replace(/[\s·,.-]+/g,'');
  const searchText=p=>[p.name,p.region,p.address,p.regionGroup,p.group,p.category,p.offer,p.detail,p.cafeLink,p.menu,...(Array.isArray(p.tags)?p.tags:[]),...(Array.isArray(p.packages)?p.packages.flat():[])].map(normalize).join(' ');
  function categoryMatches(p,category) {
    if(category==='전체')return true;
    if(category==='수도권')return p.regionGroup==='서울/경기 협력업체';
    if(category==='지방')return p.regionGroup==='전라/경상/충청 협력업체';
    const hay=normalize([p.category,...(Array.isArray(p.tags)?p.tags:[]),...(Array.isArray(p.packages)?p.packages.flat():[])].join(' '));
    const terms={정비:['정비','점검'],사고수리:['사고수리','판금','도색'], '오디오·전장':['오디오','전장','튜닝'],차량유리:['유리'], '휠·타이어':['휠','타이어'], '부품·튜닝':['부품','튜닝'],신차패키지:['신차패키지']}[category]||[];
    return terms.some(term=>hay.includes(normalize(term)));
  }
  function renderFinder() {
    const q=normalize($('#finderQuery').value),region=$('#finderRegion').value;
    const rows=Object.values(partners).filter(p=>(!region||p.regionGroup===region)&&categoryMatches(p,selectedCategory)&&searchText(p).includes(q));
    $('#finderCount').textContent=`${rows.length}곳`;
    const shopMarkup=p=>{
      return `<article class="finder-shop"><div class="finder-shop-main"><div class="finder-shop-info"><b>${esc(p.name)}</b><small>${esc(p.displayAddress||p.address||p.region||'위치 확인 중')} · ${esc(p.category)}</small></div><div class="finder-shop-actions"><button type="button" class="finder-map-toggle ${selectedMapId===p.id?'active':''}" data-map="${esc(p.id)}">${esc(p.mapActionLabel||'지도보기')}</button><button type="button" class="finder-booking-btn" data-reserve="${esc(p.id)}">${esc(p.bookingLabel||'예약 요청')}</button></div></div></article>`;
    };
    if(!rows.length){$('#finderResults').innerHTML='<p class="empty">검색 결과가 없습니다. 검색어 또는 분야를 바꿔보세요.</p>';return;}
    const regions=[['서울/경기 협력업체','수도권 협력업체'],['전라/경상/충청 협력업체','지방 협력업체'],['신차패키지','신차패키지 업체']];
    const groupOrder=['사고수리 전문','차량유리 전문','전장류 전문','휠·타이어 전문','부품·튜닝 전문','정비 전문','신차패키지'];
    $('#finderResults').innerHTML=regions.map(([key,label])=>{
      const regionRows=rows.filter(p=>p.regionGroup===key);
      if(!regionRows.length)return '';
      const groups=key==='전라/경상/충청 협력업체'?[['사고수리·정비 전문',regionRows]]:groupOrder.map(group=>[group,regionRows.filter(p=>partnerCategoryGroups(p).includes(group))]).filter(([,shops])=>shops.length);
      if(!groups.length)return '';
      const openGroup=selectedCategory!=='전체'||Boolean(q);
      return `<section class="finder-region-group"><div class="partner-region-title">${label}<span>${regionRows.length}곳</span></div>${groups.map(([group,shops])=>`<details class="partner-category-disclosure finder-category-group" ${openGroup?'open':''}><summary><b>${esc(group)}</b><span>${shops.length}곳</span></summary><div class="finder-category-shops">${shops.map(shopMarkup).join('')}</div></details>`).join('')}</section>`;
    }).join('')||'<p class="empty">검색 결과가 없습니다. 분야를 바꿔보세요.</p>';
  }
  section.addEventListener('click',e=>{
    const category=e.target.closest('[data-category]');
    if(category){selectedCategory=category.dataset.category;section.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b===category)));renderFinder();return;}
    const map=e.target.closest('[data-map]');
    if(map){const p=partners[map.dataset.map];if(!p)return;if(p.mapActionUrl){window.open(p.mapActionUrl,'_blank','noopener,noreferrer');return;}selectedMapId=p.id;const place=`${p.name} ${p.address||p.region||''}`.trim(),query=encodeURIComponent(place),frame=$('#finderMapFrame');frame.src=`https://www.google.com/maps?q=${query}&output=embed`;frame.title=`${p.name} 위치 Google 지도`;$('#finderMapTitle').textContent=p.name;$('#finderMapHint').textContent=`${p.address||p.region||'지역 확인 필요'} · Google 지도에서 업체 위치를 확인하세요.`;section.querySelectorAll('[data-map]').forEach(button=>button.classList.toggle('active',button===map));$('#finderMapPanel').scrollIntoView({behavior:'smooth',block:'center'});return;}
    const button=e.target.closest('[data-reserve]');
    if(!button)return;
    const id=button.dataset.reserve;
    const partner=partners[id];if(partner?.bookingUrl){window.open(partner.bookingUrl,'_blank','noopener,noreferrer');return;}
    if(typeof window.openBooking==='function')window.openBooking(id);
    else window.toast?.('예약 입력창을 불러오지 못했어요. 페이지를 새로고침해주세요.');
  });
  $('#finderQuery').addEventListener('input',renderFinder);$('#finderRegion').addEventListener('change',renderFinder);
  window.openPartnerFinder=()=>{go('partners');section.scrollIntoView({behavior:'smooth',block:'start'});};

  const originalLoadEntries=window.loadEntries;
  const normalizeHistory=value=>String(value??'').toLocaleLowerCase('ko-KR').replace(/[\s·,.-]+/g,'');
  const numberFrom=value=>Number(String(value??'').replace(/[^0-9]/g,''))||0;
  function historyKind(row){
    if(row.kind)return row.kind;
    const text=normalizeHistory(`${row.work||row.name||''} ${row.part||''}`);
    return row.part||/타이어|배터리|패드|필터|와이퍼|브레이크액|냉각수|에어컨필터/.test(text)?'소모품':'정비';
  }
  function enrichVehicleHistory(){
    const list=$('#entries'),car=window.selectedVehicle?.();
    if(!list||!car)return;
    const records=window.allPassportRecords?.(car.id)||[];
    const unique=[];
    for(const row of records){
      const key=`${numberFrom(row.odo)}|${normalizeHistory(row.work)}`;
      const old=unique.find(item=>item.key===key);
      const priority={partner:3,owner:2}[row.source]||1;
      if(!old)unique.push({key,row,priority});else if(priority>old.priority){old.row=row;old.priority=priority;}
    }
    const remaining=new Set(unique);
    const entries=[...list.querySelectorAll('.entry')];
    for(const entry of entries){
      const label=$('.entrytext b',entry)?.textContent||'',small=$('.entrytext small',entry)?.textContent||'';
      const odo=numberFrom(small.match(/[0-9,]+\s*km/i)?.[0]);
      const nameKey=normalizeHistory(label);
      const match=unique.find(item=>remaining.has(item)&&numberFrom(item.row.odo)===odo&&nameKey.includes(normalizeHistory(item.row.work)));
      const icon=$('.entryico',entry)?.textContent||'';
      entry.dataset.kind=icon.includes('⛽')?'주유':icon.includes('🔧')?'정비':'소모품';
      if(match){remaining.delete(match);const text=$('.entrytext',entry);const badge=document.createElement('small');badge.className=`history-badge ${match.row.source==='owner'?'owner':''}`;badge.textContent=match.row.source==='partner'?'업체 인증':'차주 기록';text.append(badge);}
    }
    for(const item of remaining){
      const row=item.row,kind=historyKind(row);
      const entry=document.createElement('div');entry.className='entry';entry.dataset.kind=kind;
      const icon=document.createElement('span');icon.className='entryico';icon.textContent=kind==='소모품'?'🧰':'🔧';
      const info=document.createElement('span');info.className='entrytext';
      const title=document.createElement('b');title.textContent=row.work||'정비 기록';
      const meta=document.createElement('small');meta.textContent=`${row.date||''} · ${row.odo||''}`;
      const shop=document.createElement('small');shop.textContent=row.shop||'차주 직접 기록';
      info.append(title,meta,shop);
      const badge=document.createElement('small');badge.className=`history-badge ${row.source==='owner'?'owner':''}`;badge.textContent=row.source==='partner'?'업체 인증':'차주 기록';info.append(badge);
      const amount=document.createElement('span');amount.className='entryamount';amount.textContent=row.cost||'';
      entry.append(icon,info,amount);list.append(entry);
    }
    const selectedKind=$('.record-filters .chip.active')?.dataset.kind||'전체';
    let visibleCount=0;
    for(const entry of list.querySelectorAll('.entry')){entry.hidden=selectedKind!=='전체'&&entry.dataset.kind!==selectedKind;if(!entry.hidden)visibleCount++;}
    $('#entrycount').textContent=`${visibleCount}건`;
    const monthKey=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul'}).format(new Date()).slice(0,7);
    let extraSpend=0,extraService=0,extraParts=0;
    for(const item of remaining){
      const row=item.row;if(String(row.date||'').replaceAll('.','-').slice(0,7)!==monthKey)continue;
      const amount=numberFrom(row.cost);extraSpend+=amount;
      if(historyKind(row)==='소모품')extraParts+=amount;else extraService+=amount;
    }
    if(extraSpend){$('#monthSpend').textContent=`₩${(numberFrom($('#monthSpend').textContent)+extraSpend).toLocaleString()}`;$('#serviceSpend').textContent=`₩${(numberFrom($('#serviceSpend').textContent)+extraService).toLocaleString()}`;$('#partsSpend').textContent=`₩${(numberFrom($('#partsSpend').textContent)+extraParts).toLocaleString()}`;}
  }
  if(typeof originalLoadEntries==='function'){
    window.loadEntries=function(...args){
      const selected=typeof activeEntryKind!=='undefined'?activeEntryKind:($('.record-filters .chip.active')?.dataset.kind||'전체');
      if(typeof activeEntryKind!=='undefined')activeEntryKind='전체';
      let result;
      try{result=originalLoadEntries.apply(this,args);}finally{if(typeof activeEntryKind!=='undefined')activeEntryKind=selected;}
      enrichVehicleHistory();
      return result;
    };
    window.setTimeout(()=>window.loadEntries(),0);
  }
  renderFinder();
})();
