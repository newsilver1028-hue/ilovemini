(() => {
  const key = 'ilmApiBaseUrl';
  const defaultApiBase = 'https://ilovemini.onrender.com';
  const cleanBase = (value) => {
    const raw = String(value || '').trim().replace(/\/+$/, '');
    if (!raw) return '';
    const parsed = new URL(raw);
    if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('API 주소는 https://로 시작해야 합니다.');
    if (parsed.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(parsed.hostname)) throw new Error('실서비스 API 주소는 보안을 위해 https://가 필요합니다.');
    return raw.replace(/\/api$/i, '');
  };
  const base = () => {
    try { return `${cleanBase(localStorage.getItem(key) || defaultApiBase)}/api`; } catch { return ''; }
  };
  const apiUrl = (path) => `${base()}/${String(path).replace(/^\/+/, '').replace(/\/+$/, '')}/`;
  const json = async (url, options = {}) => {
    const controller = typeof AbortController === 'undefined' ? null : new AbortController();
    let timer;
    try {
      const timeout = new Promise((_, reject) => { timer = setTimeout(() => { controller?.abort(); reject(new Error('서버 응답이 지연되고 있어요.')); }, 8000); });
      const request = fetch(url, {...options, headers: {'Accept':'application/json', ...(options.headers || {})}, ...(controller ? {signal: controller.signal} : {})});
      const response = await Promise.race([request, timeout]);
      let payload = {};
      try { payload = await response.json(); } catch {}
      if (!response.ok) throw new Error(payload.detail || `서버 응답 오류 (${response.status})`);
      return payload;
    } finally { clearTimeout(timer); }
  };
  const statusMarkup = `<div class="api-connection-row"><span>서버 연결</span><b class="api-connection-status" id="apiConnectionStatus" data-state="off">미설정</b></div>`;
  const modalMarkup = `<div class="modalback" id="apiConnectionBack" onclick="if(event.target===this)closeModal('apiConnectionBack')"><div class="modal"><div class="grabber"></div><div class="modal-title-row"><div><span class="eyebrow">SERVICE CONNECTION</span><h3>API 서버 연결</h3></div><button class="closebtn" type="button" onclick="closeModal('apiConnectionBack')" aria-label="닫기">×</button></div><p>배포한 API 서버 주소를 입력하면 공개 카페 게시글 검색과 서버 상태를 확인합니다.</p><label class="api-modal-label" for="apiBaseInput">API 서버 주소</label><input class="api-modal-input" id="apiBaseInput" inputmode="url" placeholder="https://ilovemini-api.onrender.com" autocomplete="url"><p class="api-modal-help">서버 주소만 입력하세요. 비밀번호나 API 비밀키는 입력하지 마세요. 이 주소는 이 브라우저에 저장됩니다. 정비 기록·예약 변경은 로그인 권한이 연결된 앱에서 처리됩니다.</p><div class="api-connection-row"><span>연결 확인</span><b class="api-connection-status" id="apiModalStatus" data-state="off">아직 확인하지 않음</b></div><div class="api-modal-actions"><button class="btn light" type="button" onclick="clearApiConnection()">연결 해제</button><button class="btn" type="button" onclick="saveApiConnection()">저장하고 확인</button></div></div></div>`;
  const cafeSearchModalMarkup = `<div class="modalback" id="cafeDirectSearchBack" role="presentation" onclick="if(event.target===this)closeModal('cafeDirectSearchBack')"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="cafeDirectSearchTitle"><div class="grabber"></div><div class="modal-title-row"><div><span class="eyebrow">ILOVEMINI CAFE</span><h3 id="cafeDirectSearchTitle">카페에 직접 질문</h3></div><button class="closebtn" type="button" onclick="closeModal('cafeDirectSearchBack')" aria-label="닫기">×</button></div><p>질문을 확인하고 원하는 검색으로 이어가세요.</p><label class="api-modal-label" for="cafeDirectSearchQuery">질문 또는 검색어</label><input class="api-modal-input cafe-direct-query" id="cafeDirectSearchQuery" type="search" enterkeyhint="search" maxlength="120" placeholder="예: 미션 수리 방법" autocomplete="off" onkeydown="if(event.key==='Enter'){event.preventDefault();submitCafeDirectSearch('cafe')}"><p class="api-modal-help">네이버 AI탭에서 답변을 확인하거나 카페 글을 검색할 수 있어요.</p><button class="btn wide" type="button" onclick="submitCafeDirectSearch('naver')">네이버 AI탭에서 검색</button><button class="btn light wide" type="button" onclick="submitCafeDirectSearch('cafe')">아이러브미니 카페에서 검색</button></div></div>`;

  function install() {
    const menu = document.querySelector('#profile .menu');
    if (menu && !document.getElementById('apiConnectionMenu')) {
      const button = document.createElement('button');
      button.id = 'apiConnectionMenu';
      button.type = 'button';
      button.innerHTML = 'API 서버 연결 <span>›</span>';
      button.onclick = openApiConnectionSettings;
      menu.append(button);
      menu.insertAdjacentHTML('afterend', statusMarkup);
    }
    if (!document.getElementById('apiConnectionBack')) document.body.insertAdjacentHTML('beforeend', modalMarkup);
    if (!document.getElementById('cafeDirectSearchBack')) document.body.insertAdjacentHTML('beforeend', cafeSearchModalMarkup);
    const cafeSearchForm = document.getElementById('cafeAiForm');
    const stylesheet = document.querySelector('link[href^="assets/api-connection.css"]');
    if (stylesheet && !stylesheet.href.includes('v=4')) stylesheet.href = 'assets/api-connection.css?v=4';
    const description = document.querySelector('#cafeAiTitle')?.parentElement?.querySelector('p');
    if (description) description.textContent = '네이버 AI 답변과 아이러브미니 카페 게시글 중 골라 검색하세요.';
    const submit = cafeSearchForm?.querySelector('button[type="submit"]');
    if (submit) { submit.textContent = 'AI 검색'; submit.setAttribute('aria-label', '네이버 AI탭에서 검색'); }
    const input = document.getElementById('cafeAiQuery');
    if (input) { input.type = 'search'; input.setAttribute('enterkeyhint', 'search'); }
    const result = document.getElementById('cafeAiResult');
    if (result && !document.getElementById('cafeAiDirectLink')) {
      result.insertAdjacentHTML('afterend', '<button class="cafe-ai-direct-link" id="cafeAiDirectLink" type="button">네이버에서 질문 이어가기</button>');
      document.getElementById('cafeAiDirectLink').addEventListener('click', openCafeDirectSearch);
    }
    updateStatus();
  }
  function updateStatus(text, state) {
    let configured = false;
    try { configured = !!base(); } catch {}
    const label = text || (configured ? '주소 저장됨' : '미설정');
    for (const node of document.querySelectorAll('#apiConnectionStatus,#apiModalStatus')) {
      node.textContent = label;
      node.dataset.state = state || 'off';
    }
  }
  window.openApiConnectionSettings = () => {
    const input = document.getElementById('apiBaseInput');
    input.value = localStorage.getItem(key) || '';
    updateStatus('연결 확인 전', 'off');
    document.getElementById('apiConnectionBack').classList.add('show');
    input.focus();
  };
  window.saveApiConnection = async () => {
    const input = document.getElementById('apiBaseInput');
    let origin;
    try { origin = cleanBase(input.value); if (!origin) throw new Error('API 서버 주소를 입력해 주세요.'); }
    catch (error) { updateStatus(error.message, 'error'); toast(error.message); return; }
    localStorage.setItem(key, origin);
    updateStatus('연결 확인 중…', 'off');
    try {
      const result = await json(`${origin}/api/health/`);
      if (result.status !== 'ok') throw new Error('API 서버가 정상 상태를 반환하지 않았습니다.');
      updateStatus('연결됨', 'ok');
      toast('API 서버에 연결됐어요.');
    } catch (error) {
      updateStatus('연결 실패', 'error');
      toast(`${error.message} · 서버 주소와 CORS 설정을 확인해 주세요.`);
    }
  };
  window.clearApiConnection = () => {
    localStorage.removeItem(key);
    document.getElementById('apiBaseInput').value = defaultApiBase;
    updateStatus('기본 서버 사용', 'off');
    toast('기본 API 서버 주소로 돌아왔어요.');
  };
  const mobileCafeSearchUrl = (query) => {
    const url = new URL('https://m.cafe.naver.com/ca-fe/web/cafes/13071593/search');
    url.searchParams.set('q', query);
    url.searchParams.set('mi', '0');
    url.searchParams.set('ta', 'SUBJECT');
    url.searchParams.set('pc', 'ALL');
    url.searchParams.set('od', 'NEW');
    return url.href;
  };
  const naverAiTabSearchUrl = (query) => {
    const url = new URL('https://search.naver.com/search.naver');
    url.searchParams.set('query', query);
    url.searchParams.set('ssc', 'tab.ait.all');
    url.searchParams.set('sm', 'top_clk.aitab');
    url.searchParams.set('dtm_source', 'main');
    url.searchParams.set('dtm_medium', 'searchbox');
    url.searchParams.set('dtm_detail', 'empty');
    url.searchParams.set('ait_pv', 'home');
    return url.href;
  };
  const escapeHtml = (value) => String(value || '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const showCafeState = (message, state = 'loading') => {
    const result = document.getElementById('cafeAiResult');
    if (!result) return;
    result.className = `cafe-ai-result is-${state}`;
    result.setAttribute('aria-busy', state === 'loading' ? 'true' : 'false');
    result.textContent = message;
  };
  window.askCafeKnowledge = (query) => {
    const input = document.getElementById('cafeAiQuery');
    if (input) input.value = query;
    window.searchCafeKnowledge();
  };
  function openCafeDirectSearch() {
    const input = document.getElementById('cafeAiQuery');
    const queryField = document.getElementById('cafeDirectSearchQuery');
    queryField.value = input?.value?.trim() || '';
    document.getElementById('cafeDirectSearchBack').classList.add('show');
    requestAnimationFrame(() => queryField.focus());
  }
  window.submitCafeDirectSearch = (destination) => {
    const queryField = document.getElementById('cafeDirectSearchQuery');
    const query = queryField.value.trim();
    if (!query) { queryField.focus(); return; }
    if (query.length < 2 || query.length > 120) {
      toast('질문을 2~120자로 입력해 주세요.');
      queryField.focus();
      return;
    }
    const url = destination === 'naver'
      ? naverAiTabSearchUrl(query)
      : mobileCafeSearchUrl(query);
    window.location.assign(url);
  };
  window.searchCafeKnowledge = async () => {
    const input = document.getElementById('cafeAiQuery');
    const query = input.value.trim();
    if (!query) { input.focus(); return; }
    if (query.length < 2 || query.length > 120) {
      toast('질문을 2~120자로 입력해 주세요.');
      input.focus();
      return;
    }
    window.open(naverAiTabSearchUrl(query), '_blank', 'noopener,noreferrer');
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once:true}); else install();
})();
