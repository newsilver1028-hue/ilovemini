(() => {
  const cafe = document.getElementById('cafe');
  if (!cafe) return;
  const products = [
    { title: '차량용 거치대', detail: '차량용 스마트폰 거치 아이템 · 호환 정보 확인 중', image: 'assets/cafe-item-phone-holder.png' },
    { title: '실내 고정 브래킷', detail: '실내 고정용 부품 · 적용 차종 확인 중', image: 'assets/cafe-item-interior-brackets.png' },
    { title: '프런트 그릴 파츠', detail: '외장 그릴 부품 · 적용 차종 확인 중', image: 'assets/cafe-item-grille-parts.png' },
    { title: '기어 노브·부츠', detail: '수동 기어 노브와 부츠 · 적용 차종 확인 중', image: 'assets/cafe-item-shift-knob.png' },
  ];
  const section = document.createElement('section');
  section.className = 'section cafe-products-section';
  section.setAttribute('aria-labelledby', 'cafeProductsTitle');
  section.innerHTML = `
    <div class="secthead"><h2 id="cafeProductsTitle">MINI 추천 아이템</h2><small>회원 추천 아이템</small></div>
    <p class="cafe-products-intro">제품 정보와 MINI 호환 여부를 확인하고 있어요.</p>
    <div class="cafe-product-carousel" role="region" aria-roledescription="캐러셀" aria-label="MINI 추천 아이템">
      <div class="cafe-product-track" id="cafeProductTrack" tabindex="0" aria-label="좌우로 넘겨 추천 아이템 보기"></div>
      <div class="cafe-product-controls"><button type="button" id="cafeProductPrev" aria-label="이전 아이템">‹</button><span id="cafeProductCount" aria-live="polite">1 / 4</span><button type="button" id="cafeProductNext" aria-label="다음 아이템">›</button><button type="button" id="cafeProductPause" aria-label="자동 넘김 일시정지">Ⅱ</button></div>
    </div>
    <p class="cafe-product-note">구매 링크는 준비 중입니다. 실제 등록 전 상품명과 적용 차종을 확인할 예정입니다.</p>`;
  cafe.append(section);

  const track = section.querySelector('#cafeProductTrack');
  const count = section.querySelector('#cafeProductCount');
  const pause = section.querySelector('#cafeProductPause');
  const slides = products.map(product => {
    const article = document.createElement('article');
    article.className = 'cafe-product-slide';
    const picture = document.createElement('div'); picture.className = 'cafe-product-picture';
    const image = document.createElement('img'); image.src = product.image; image.alt = product.title; image.loading = 'lazy'; image.decoding = 'async';
    picture.append(image);
    const meta = document.createElement('div'); meta.className = 'cafe-product-meta';
    const title = document.createElement('h3'); title.textContent = product.title;
    const detail = document.createElement('p'); detail.textContent = product.detail;
    const status = document.createElement('span'); status.className = 'cafe-product-status'; status.textContent = '구매 링크 준비 중';
    meta.append(title, detail, status); article.append(picture, meta); return article;
  });
  const first = slides[0].cloneNode(true), last = slides[slides.length - 1].cloneNode(true);
  [first, last].forEach(slide => { slide.setAttribute('aria-hidden', 'true'); slide.inert = true; });
  track.append(last, ...slides, first);
  const allSlides = [...track.children], n = slides.length;
  let index = 1, timer, settle, paused = false;
  function logical(i) { return ((i - 1 + n) % n) + 1; }
  function updateCount(i = index) { count.textContent = `${logical(i)} / ${n}`; }
  function jump(i, smooth = true) {
    index = Math.max(0, Math.min(n + 1, i));
    const card = allSlides[index], rect = track.getBoundingClientRect();
    const left = track.scrollLeft + card.getBoundingClientRect().left - rect.left;
    track.scrollTo({ left, behavior: smooth ? 'smooth' : 'auto' }); updateCount(index);
  }
  function stop() { clearInterval(timer); }
  function start() {
    stop();
    if (!paused && !document.hidden && cafe.classList.contains('active')) timer = setInterval(() => jump(index + 1), 5000);
  }
  function move(delta) {
    let next = index + delta;
    if (next < 0) next = n;
    if (next > n + 1) next = 1;
    jump(next); start();
  }
  track.addEventListener('scroll', () => {
    clearTimeout(settle);
    settle = setTimeout(() => {
      const left = track.getBoundingClientRect().left;
      index = allSlides.reduce((best, slide, i) => Math.abs(slide.getBoundingClientRect().left - left) < Math.abs(allSlides[best].getBoundingClientRect().left - left) ? i : best, 0);
      if (index === 0) jump(n, false); else if (index === n + 1) jump(1, false); else updateCount();
    }, 160);
  }, { passive: true });
  section.querySelector('#cafeProductPrev').onclick = () => move(-1);
  section.querySelector('#cafeProductNext').onclick = () => move(1);
  pause.onclick = () => { paused = !paused; pause.textContent = paused ? '▶' : 'Ⅱ'; pause.setAttribute('aria-label', paused ? '자동 넘김 재생' : '자동 넘김 일시정지'); start(); };
  track.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); move(e.key === 'ArrowRight' ? 1 : -1); } });
  track.addEventListener('pointerdown', stop); window.addEventListener('pointerup', start); window.addEventListener('pointercancel', start);
  track.addEventListener('mouseenter', stop); track.addEventListener('mouseleave', start); track.addEventListener('focusin', stop); track.addEventListener('focusout', start);
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());
  document.querySelectorAll('.bottom [data-view="cafe"]').forEach(button => button.addEventListener('click', () => setTimeout(start, 0)));
  new ResizeObserver(() => { if (track.clientWidth) jump(index, false); }).observe(track);
  requestAnimationFrame(() => { jump(1, false); start(); });
})();
