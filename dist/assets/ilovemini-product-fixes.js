/* ILOVEMINI prototype: vehicle-scoped Passport, duplicate checks, bookings, membership summary. */
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const read = (key, fallback) => { try { return JSON.parse(window.ilmGet(key) || JSON.stringify(fallback)); } catch { return fallback; } };
  const write = (key, value) => window.ilmSet(key, JSON.stringify(value));
  const vehicle = () => window.selectedVehicle?.() || null;
  const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul' }).format(new Date());
  const normalized = (value) => String(value ?? '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const dateKey = (value) => String(value ?? '').replaceAll('.', '-');
  const kmValue = (value) => Number(String(value ?? '').replace(/\D/g, '')) || 0;

  function passportCode(car = vehicle()) {
    if (!car) return '';
    const ids = read('ilmPassportCodes', {});
    if (!ids[car.id]) {
      const random = globalThis.crypto?.randomUUID?.().replaceAll('-', '').slice(0, 12).toUpperCase()
        || Math.random().toString(36).slice(2, 14).toUpperCase();
      ids[car.id] = `ILM-${random}`;
      write('ilmPassportCodes', ids);
    }
    return ids[car.id];
  }
  const qrPayload = (car = vehicle()) => car ? `ILOVEMINI-PASSPORT:${passportCode(car)}` : '';

  function recordsFor(vehicleId = vehicle()?.id) {
    if (!vehicleId) return [];
    const partner = (window.getPartnerRecords?.() || []).filter((row) => (row.vehicleId || 'mini') === vehicleId);
    const owner = read('ilmEntries', []).filter((entry) => String(entry.vehicle || 'mini') === vehicleId && ['정비', '소모품'].includes(entry.kind))
      .map((entry) => ({ id: entry.id, vehicleId, date: entry.date, odo: `${Number(entry.odo || 0).toLocaleString()} km`, work: entry.name, shop: '차주 직접 기록', cost: `₩${Number(entry.amount || 0).toLocaleString()}`, source: 'owner' }));
    const samples = (samplePassportRecords || []).filter((row) => (row.vehicleId || 'mini') === vehicleId);
    return [...partner, ...owner, ...samples].sort((a, b) => dateKey(b.date).localeCompare(dateKey(a.date)));
  }
  function isDuplicate({ vehicleId, date, odo, work, shop, source }) {
    const targetWork = normalized(work), targetKm = kmValue(odo);
    return recordsFor(vehicleId).some((row) => dateKey(row.date) === dateKey(date)
      && kmValue(row.odo) === targetKm && normalized(row.work) === targetWork
      && (source === 'owner' || row.source === 'owner' || normalized(row.shop) === normalized(shop)));
  }

  function addLedgerPassport() {
    const ledger = $('#ledger');
    const carCard = $('#ledgerVehicleCard', ledger);
    if (ledger && carCard && !$('#vehiclePassportCard')) {
      carCard.insertAdjacentHTML('afterend', `<section class="passport-card" id="vehiclePassportCard">
        <div class="passport-head"><div><span class="eyebrow">VEHICLE PASSPORT</span><h2 id="passportVehicleName">차량 이력</h2><p id="passportSummary">차량별 정비·주유·소모품 내역</p></div><button type="button" class="qr-small" onclick="openPassportQr(event)">▦ 통합 QR</button></div>
        <div class="passport-metrics"><div><b id="verifiedCount">0</b><span>업체 인증</span></div><div><b id="ownerCount">0</b><span>차주 기록</span></div><div><b id="handoverCount">0</b><span>정비 이력</span></div></div>
      </section>`);
    }
  }
  function addMembershipCard() {
    const attendance = $('.attendance-card');
    if (!attendance || $('#membershipCard')) return;
    attendance.id = 'membershipCard'; attendance.classList.add('membership-card');
    $('.attendance-head', attendance).innerHTML = `<div><span class="attendance-kicker">ILOVEMINI MEMBERSHIP</span><h2>아이러브미니 멤버십</h2></div><button type="button" class="textbtn" onclick="go('profile')">나의 차고 ›</button>`;
    $('.attendance-copy', attendance).outerHTML = `<div class="membership-stats"><div><small>보유 포인트</small><b id="attendanceBalance">0 P</b></div><div><small>보유 쿠폰</small><b id="membershipCouponCount">0장</b></div><div><small>회원 등급</small><b>정회원</b></div></div>`;
    $('.attendance-footnote', attendance).textContent = '출석 1,000P · 7일 연속 보너스 +3,000P · 시제품 데이터는 이 기기에 저장됩니다.';
    attendance.insertAdjacentHTML('beforeend', `<details class="member-grade-guide"><summary>회원 등급 안내</summary><ol><li><b>신입회원</b><span>가입 후 활동을 시작하는 회원</span></li><li><b>정회원</b><span>동호회의 일반 정회원</span></li><li><b>미니회원</b><span>미니장터·벙개모임 게시판 이용 가능</span></li><li><b>협력업체</b><span>아이러브미니 공식 협력업체</span></li></ol></details>`);
    const profile = $('#profile');
    if(profile && !$('#profileMemberGrade')) {
      const badge=document.createElement('section');badge.id='profileMemberGrade';badge.className='membership-card';
      badge.innerHTML='<small>회원 등급</small><h2>정회원</h2><p class="smallnote">현재 시제품 표시 등급입니다. 실제 등급은 로그인 계정의 승인 정보로 적용됩니다.</p>';
      const profileHead=$('.profilehead', profile);
      if(profileHead) profileHead.after(badge); else profile.prepend(badge);
    }
    window.renderAttendance?.();
  }
  function addBookingList() {
    const list = $('#myVehicleList');
    if (list && !$('#bookingList')) list.insertAdjacentHTML('afterend', `<section class="section"><div class="secthead"><h2>업체 예약 요청</h2><small id="bookingCount">0건</small></div><div id="bookingList"></div><p class="smallnote">시제품 예약 요청은 현재 이용 중인 기기에만 저장됩니다. 업체로 전송되거나 예약이 확정되지는 않아요.</p></section>`);
  }
  function renderPassport() {
    addLedgerPassport();
    const card = $('#vehiclePassportCard');
    if (!card) return;
    const car = vehicle(), records = recordsFor(car?.id);
    $('#passportVehicleName').textContent = car ? `${car.model} 차량 이력` : '차량 이력';
    $('#passportSummary').textContent = car ? `정비·소모품 ${records.length}건 · 주유 기록 포함` : '차량을 추가하면 이력이 표시됩니다.';
    $('#verifiedCount').textContent = records.filter((row) => row.source === 'partner').length;
    $('#ownerCount').textContent = records.filter((row) => row.source === 'owner').length;
    $('#handoverCount').textContent = records.length;
  }
  function renderMembership() {
    addMembershipCard();
    const points = (window.attendanceSummary?.().balance) || 0;
    const coupons = read('ilmCoupons', []).filter((coupon) => !coupon.used).length;
    if ($('#membershipPoints')) $('#membershipPoints').textContent = `${points.toLocaleString()} P`;
    if ($('#membershipCouponCount')) $('#membershipCouponCount').textContent = `${coupons}장`;
  }

  window.allPassportRecords = recordsFor;
  window.renderPassport = renderPassport;
  window.renderMembership = renderMembership;
  window.openPassportQr = function (event) {
    event?.stopPropagation?.();
    const car = vehicle();
    if (!car) return window.toast?.('먼저 차량을 등록해주세요.');
    $('#passportqrback')?.classList.add('show');
    $('#passportqrback h3').textContent = `${car.model} QR`;
    $('.qr-id b', $('#passportqrback'))?.replaceChildren(document.createTextNode(passportCode(car)));
    $('.privacy-line', $('#passportqrback')).textContent = '🔒 차량 코드만 포함 · 이름·전화번호·차량번호는 QR에 저장하지 않습니다.';
    $('.prototype-note', $('#passportqrback')).textContent = '시제품은 이 브라우저의 차량 기록으로 동작합니다. 서버 공유는 아직 연결 전입니다.';
    const node = $('#passportqr'); node.replaceChildren();
    if (window.QRCode) new window.QRCode(node, { text: qrPayload(car), width: 220, height: 220, colorDark: '#111111', colorLight: '#ffffff', correctLevel: window.QRCode.CorrectLevel.M });
    else node.innerHTML = '<div class="empty">QR 생성 기능을 불러오지 못했어요. 인터넷 연결을 확인하고 다시 열어주세요.</div>';
  };

  window.openPartnerScanner = function (event) {
    event?.stopPropagation?.();
    const car = vehicle();
    if (!car) return window.toast?.('차량을 먼저 선택해주세요.');
    $('#scannerback')?.classList.add('show');
    const scanner = $('#scannerback');
    const scanQr = $('#scannerVehicleQr', scanner);
    scanQr.replaceChildren();
    new window.QRCode(scanQr, { text: qrPayload(car), width: 220, height: 220, correctLevel: window.QRCode.CorrectLevel.M });
    $('.center', scanner).textContent = '시제품에서는 아래 차량 코드로 스캔 흐름을 확인합니다.';
    const vehicleCard = $('.scan-vehicle', scanner);
    $('b', vehicleCard).textContent = car.model;
    $('small', vehicleCard).textContent = `${car.generation || ''} · ${car.year || ''}년형 · ${Number(car.km || 0).toLocaleString()} km`;
    const details = $('.center', scanner);
    if (!$('#scanPassportInput', scanner)) details.insertAdjacentHTML('afterend', `<label for="scanPassportInput">스캔한 차량 코드</label><input id="scanPassportInput" autocomplete="off"><p class="smallnote" id="scanHistorySummary" aria-live="polite"></p>`);
    $('#scanPassportInput', scanner).value = passportCode(car);
    const history = recordsFor(car.id);
    $('#scanHistorySummary', scanner).innerHTML = history.length ? `<b>기존 이력 ${history.length}건</b>${history.slice(0, 8).map((row) => `<small class=\"scan-history-row\">${escapeHtml(row.date)} · ${escapeHtml(row.odo)} · ${escapeHtml(row.work)} · ${row.source === 'partner' ? '업체 인증' : '차주 기록'}</small>`).join('')}` : '아직 저장된 정비·소모품 이력이 없습니다.';
    const button = $('button.btn.wide', scanner);
    button.textContent = '차량 이력 확인';
    button.onclick = window.verifyPassportScan;
  };
  window.verifyPassportScan = function () {
    const car = vehicle(), code = $('#scanPassportInput')?.value.trim();
    const status = $('#scanHistorySummary');
    if (!car || code !== passportCode(car)) { if (status) status.textContent = '선택한 차량의 QR 코드와 일치하지 않습니다.'; return; }
    const rows = recordsFor(car.id);
    if (status) status.textContent = rows.length ? `차량 확인 완료 · 기존 이력 ${rows.length}건 · 최근 기록 ${rows[0].date} ${rows[0].work}` : '차량 확인 완료 · 등록된 이력이 없습니다.';
    window.closeModal?.('scannerback');
    window.openPartnerRecord?.();
  };
  const oldPartnerRecord = window.openPartnerRecord;
  window.openPartnerRecord = function () {
    const car = vehicle();
    oldPartnerRecord?.();
    if (!car) return;
    const card = $('.scan-vehicle', $('#partnerrecordback'));
    if (card) { $('b', card).textContent = car.model; $('small', card).textContent = `${car.generation || ''} · ${car.year || ''}년형 · ${Number(car.km || 0).toLocaleString()} km`; }
    const auth = $('.auth-notice', $('#partnerrecordback')); if (auth) auth.textContent = '시제품 협력업체 등록 체험 · 실제 계정 인증은 연결 전입니다.';
    const latest = recordsFor(car.id).map((row) => kmValue(row.odo)).reduce((max, n) => Math.max(max, n), Number(car.km || 0));
    if ($('#shopOdo')) $('#shopOdo').value = latest || '';
    if ($('#shopName') && selectedPartner && partners?.[selectedPartner]) $('#shopName').value = partners[selectedPartner].name;
  };
  window.savePartnerRecord = function () {
    const car = vehicle(), work = $('#shopWork')?.value.trim(), odo = Number($('#shopOdo')?.value), cost = Number($('#shopCost')?.value || 0), shop = $('#shopName')?.value || '', date = today();
    if (!car || !work || !Number.isFinite(odo) || odo <= 0) return window.toast?.('작업내용과 올바른 주행거리를 입력해주세요.');
    if (isDuplicate({ vehicleId: car.id, date, odo, work, shop, source: 'partner' })) return window.toast?.('같은 차량·날짜·주행거리·작업 이력이 이미 등록되어 있어요.');
    const entries = window.getPartnerRecords?.() || [];
    entries.unshift({ id: globalThis.crypto?.randomUUID?.() || `record-${Date.now()}`, vehicleId: car.id, passportCode: passportCode(car), date, odo: `${odo.toLocaleString()} km`, work, shop, cost: `₩${cost.toLocaleString()}`, part: $('#shopPart')?.value || '', source: 'partner' });
    write('ilmPartnerRecords', entries);
    window.closeModal?.('partnerrecordback'); renderPassport(); window.loadEntries?.();
    window.toast?.('업체 인증 이력을 이 기기에 저장했어요. 서버 전송은 아직 연결 전입니다.');
  };
  window.saveEntry = function () {
    const car = vehicle(), kind = $('#kind')?.value || '정비', work = $('#item')?.value.trim() || kind;
    const amount = Number($('#amount')?.value || 0), odo = Number($('#odo')?.value || car?.km || 0), date = today();
    if (!car || !odo) return window.toast?.('차량과 주행거리를 확인해주세요.');
    if (['정비', '소모품'].includes(kind) && isDuplicate({ vehicleId: car.id, date, odo, work, shop: '차주 직접 기록', source: 'owner' })) return window.toast?.('같은 차량의 정비 이력이 이미 등록되어 있어요.');
    const entries = read('ilmEntries', []);
    entries.unshift({ id: globalThis.crypto?.randomUUID?.() || `entry-${Date.now()}`, vehicle: car.id, kind, name: work, amount, odo, date });
    write('ilmEntries', entries); window.loadEntries?.(); renderPassport(); window.closeModal?.('entryback');
    ['item', 'amount', 'odo'].forEach((id) => { if ($('#' + id)) $('#' + id).value = ''; });
    window.toast?.('차계부와 차량 이력에 저장했어요.');
  };

  // Reservations are requests, not confirmed appointments; the prototype stores them on this device only.
  function bookings() { return read('ilmPartnerBookings', []); }
  function renderBookings() {
    addBookingList();
    const rows = bookings().filter((row) => row.status !== '취소'), list = $('#bookingList');
    if (!list) return;
    if ($('#bookingCount')) $('#bookingCount').textContent = `${rows.length}건`;
    list.innerHTML = rows.length ? rows.map((row) => `<article class="booking-row"><div><b>${escapeHtml(row.partnerName)}</b><small>${escapeHtml(row.date)} · ${escapeHtml(row.time)} · ${escapeHtml(row.service)}</small><small>${escapeHtml(row.vehicle)} · ${escapeHtml(row.status)}</small>${row.memo ? `<p>${escapeHtml(row.memo)}</p>` : ''}</div>${row.status === '취소' ? '' : `<button type="button" class="textbtn" onclick="cancelILoveMiniBooking('${escapeHtml(row.id)}')">취소</button>`}</article>`).join('') : '<div class="empty">예약 요청이 없어요.</div>';
  }
  window.openBooking = function (id) {
    const partner = partners?.[id], car = vehicle();
    if (!partner || !car) return window.toast?.('협력업체와 차량을 선택해주세요.');
    const modal = $('#bookingback');
    if (!modal) return window.toast?.('예약 입력창을 불러오지 못했어요. 페이지를 새로고침해주세요.');
    selectedPartner = id;
    $('#bookingPartnerName').textContent = `${partner.name}에 희망 일정을 요청합니다.`;
    $('#bookingVehicle').value = `${car.model} · ${car.generation || ''} · ${Number(car.km || 0).toLocaleString()} km`;
    $('#bookingDate').min = today(); $('#bookingDate').value = today(); $('#bookingMemo').value = '';
    window.closeModal?.('partnerback'); modal.classList.add('show');
  };
  window.saveILoveMiniBooking = function () {
    const car = vehicle(), partner = partners?.[selectedPartner];
    const date = $('#bookingDate').value, time = $('#bookingTime').value, service = $('#bookingService').value, memo = $('#bookingMemo').value.trim();
    if (!car || !partner || !date || date < today()) return window.toast?.('업체·차량·예약 희망 날짜를 확인해주세요.');
    const rows = bookings();
    if (rows.some((row) => row.partnerId === partner.id && row.vehicleId === car.id && row.date === date && row.time === time && row.status !== '취소')) return window.toast?.('같은 업체·차량·시간의 예약 요청이 이미 있어요.');
    rows.unshift({ id: globalThis.crypto?.randomUUID?.() || `booking-${Date.now()}`, partnerId: partner.id, partnerName: partner.name, vehicleId: car.id, vehicle: car.model, date, time, service, memo, status: '임시 저장' });
    write('ilmPartnerBookings', rows); window.closeModal?.('bookingback'); renderBookings();
    window.toast?.('예약 요청을 이 기기에 저장했어요. 업체에는 전달되지 않았으니 실제 예약은 업체에 직접 문의해주세요.');
  };
  window.cancelILoveMiniBooking = function (id) { write('ilmPartnerBookings', bookings().filter((row) => row.id !== id)); renderBookings(); };

  function addBookingModal() {
    if ($('#bookingback')) return;
    document.body.insertAdjacentHTML('beforeend', `<div class="modalback" id="bookingback" onclick="if(event.target===this)closeModal('bookingback')"><div class="modal"><div class="grabber"></div><div class="modal-title-row"><div><span class="eyebrow">PARTNER BOOKING</span><h3>정비 예약 요청</h3></div><button class="closebtn" aria-label="닫기" onclick="closeModal('bookingback')">×</button></div><p id="bookingPartnerName">협력업체에 희망 일정을 요청해요.</p><label>차량</label><input id="bookingVehicle" readonly><label for="bookingService">예약 서비스</label><select id="bookingService"><option>정비·점검</option><option>사고 수리</option><option>오디오·전장</option><option>휠·타이어</option><option>차량 유리</option><option>기타</option></select><div class="input-grid"><div><label for="bookingDate">희망 날짜</label><input id="bookingDate" type="date"></div><div><label for="bookingTime">희망 시간</label><select id="bookingTime"><option>09:00</option><option>10:00</option><option>11:00</option><option>13:00</option><option>14:00</option><option>15:00</option><option>16:00</option><option>17:00</option></select></div></div><label for="bookingMemo">증상·요청사항</label><textarea id="bookingMemo" rows="3" maxlength="300" placeholder="차량 증상이나 원하는 작업을 적어주세요"></textarea><button type="button" class="btn wide" onclick="saveILoveMiniBooking()">요청 내용 저장</button><p class="smallnote">시제품은 요청 내용을 현재 기기에만 저장합니다. 업체로 전달되지 않으며, 실제 예약은 업체에 직접 문의해주세요.</p></div></div>`);
  }
  function addStyles() {
    if ($('#ilovemini-fix-style')) return;
    const style = document.createElement('style'); style.id = 'ilovemini-fix-style';
    style.textContent = `.membership-card{margin:12px 0;padding:16px;background:var(--white);color:var(--ink);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}.membership-top,.membership-stats{display:flex;justify-content:space-between;gap:10px;align-items:center}.membership-top strong{display:block;font-size:16px}.membership-stats{margin-top:12px;padding-top:12px;border-top:1px solid var(--line);align-items:flex-start}.membership-stats div{display:flex;flex-direction:column;gap:3px}.membership-stats small,.membership-note,.booking-row small{color:var(--muted);font-size:12px}.membership-stats b{font-size:15px}.membership-note{margin:10px 0 0;line-height:1.45}.booking-row{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;padding:12px 0;border-bottom:1px solid var(--line)}.booking-row small{display:block;margin-top:3px}.booking-row p{margin:7px 0 0;font-size:13px}.scan-history-row{display:block;margin-top:5px;color:var(--muted);font-size:12px;line-height:1.4}.passport-card{background:var(--white);color:var(--ink)}.history-item{border-bottom:1px solid var(--line)}@media(max-width:360px){.membership-stats{gap:5px}.membership-stats b{font-size:13px}.membership-stats small{font-size:11px}}`;
    document.head.append(style);
  }
  function addPartnerBookingButtons() {
    const original = window.openPartner;
    if (!original || original.__bookingWrapped) return;
    const wrapped = function (id) {
      original(id);
      const detail = $('#partnerdetail');
      if (!detail || $('.book-partner-btn', detail)) return;
      const button = document.createElement('button'); button.type = 'button'; button.className = 'btn wide book-partner-btn'; button.textContent = '예약 요청하기'; button.onclick = () => window.openBooking(id);
      const inquiry = $('button.btn.wide', detail); if (inquiry) detail.insertBefore(button, inquiry); else detail.append(button);
    };
    wrapped.__bookingWrapped = true; window.openPartner = wrapped;
  }
  function hookVehicleRefresh() {
    const originalSelect = window.selectVehicle;
    if (originalSelect && !originalSelect.__passportWrapped) {
      const wrapped = function (id) { originalSelect(id); renderPassport(); renderMembership(); };
      wrapped.__passportWrapped = true; window.selectVehicle = wrapped;
    }
    const originalCheckin = window.checkInAttendance;
    if (originalCheckin && !originalCheckin.__membershipWrapped) {
      const wrapped = function () { originalCheckin(); renderMembership(); };
      wrapped.__membershipWrapped = true; window.checkInAttendance = wrapped;
    }
  }

  addBookingModal(); addStyles(); addLedgerPassport(); addMembershipCard(); addBookingList(); addPartnerBookingButtons(); hookVehicleRefresh();
  renderPassport(); renderMembership(); renderBookings();
})();
