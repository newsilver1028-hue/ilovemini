(() => {
  const input = document.getElementById('cafeAiQuery');
  const status = document.getElementById('cafePostsStatus');
  const list = document.getElementById('cafePostsList');
  const cafeTab = document.querySelector('.bottom [data-view="cafe"]');
  if (!input || !status || !list) return;

  const defaultApi = 'https://ilovemini.onrender.com';
  let loading = false;
  let firstLoadStarted = false;

  function apiBase() {
    let value = defaultApi;
    try { value = localStorage.getItem('ilmApiBaseUrl') || defaultApi; } catch {}
    return String(value).trim().replace(/\/+$/, '').replace(/\/api$/i, '');
  }
  function setStatus(text, kind = '') {
    status.textContent = text;
    status.className = `cafe-posts-status${kind ? ` is-${kind}` : ''}`;
    status.hidden = !text;
  }
  function makeExternalUrl(value) {
    try {
      const url = new URL(value);
      if (url.protocol !== 'https:' || !/(^|\.)cafe\.naver\.com$/i.test(url.hostname)) return null;
      return url.href;
    } catch { return null; }
  }
  function fallbackSearchUrl(query) {
    const url = new URL('https://m.cafe.naver.com/ca-fe/web/cafes/13071593/search');
    url.searchParams.set('q', query);
    url.searchParams.set('mi', '0');
    url.searchParams.set('ta', 'SUBJECT');
    url.searchParams.set('pc', 'ALL');
    url.searchParams.set('od', 'NEW');
    return url.href;
  }
  function render(items) {
    list.replaceChildren();
    for (const item of items) {
      const href = makeExternalUrl(item.link);
      if (!href) continue;
      const card = document.createElement('a');
      card.className = 'cafe-post-card';
      card.href = href;
      card.target = '_blank';
      card.rel = 'noopener noreferrer';
      const title = document.createElement('strong');
      title.textContent = item.title || '아이러브미니 카페 게시글';
      card.append(title);
      if (item.description) {
        const description = document.createElement('p');
        description.textContent = item.description;
        card.append(description);
      }
      const meta = document.createElement('small');
      meta.textContent = item.cafe_name || '아이러브미니 네이버 카페 · 게시글 열기';
      card.append(meta);
      list.append(card);
    }
  }
  window.searchCafePosts = async (presetQuery) => {
    const query = String(presetQuery ?? input.value).trim();
    if (query.length < 2 || query.length > 80) {
      setStatus('카페 글 검색어는 2~80자로 입력해 주세요.', 'error');
      input.focus();
      return;
    }
    input.value = query;
    if (loading) return;
    loading = true;
    const button = document.querySelector('.cafe-post-search');
    if (button) { button.disabled = true; button.textContent = '검색 중…'; }
    setStatus(`“${query}” 카페 게시글을 불러오는 중…`);
    list.replaceChildren();
    try {
      const response = await fetch(`${apiBase()}/api/cafe/search/?q=${encodeURIComponent(query)}`, {
        headers: {Accept: 'application/json'},
        credentials: 'omit',
      });
      let payload = {};
      try { payload = await response.json(); } catch {}
      if (!response.ok) throw new Error(payload.detail || `서버 응답 오류 (${response.status})`);
      render(Array.isArray(payload.items) ? payload.items : []);
      if (list.children.length) setStatus(`“${query}” 검색 결과 ${list.children.length}건 · 공개 게시글`);
      else setStatus('검색 결과가 없어요. 다른 검색어를 입력해 보세요.');
    } catch (error) {
      setStatus(`${error.message || '연결 오류'} · 네이버 카페에서 직접 검색할 수 있어요.`, 'error');
      const link = document.createElement('a');
      link.className = 'cafe-post-card';
      link.href = fallbackSearchUrl(query);
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = `네이버 카페에서 “${query}” 검색`;
      list.replaceChildren(link);
    } finally {
      loading = false;
      if (button) { button.disabled = false; button.textContent = '카페 글 검색'; }
    }
  };
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      window.searchCafePosts();
    }
  });
  cafeTab?.addEventListener('click', () => {
    if (firstLoadStarted) return;
    firstLoadStarted = true;
    window.searchCafePosts('MINI');
  });
})();
