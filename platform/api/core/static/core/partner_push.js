(() => {
  const config = window.PARTNER_WEB_PUSH_CONFIG;
  const button = document.getElementById("partner-push-toggle");
  const status = document.getElementById("partner-push-status");
  if (!config || !button || !status) return;

  const setMessage = (message, isError = false) => {
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  };
  const decodeKey = (value) => {
    const padded = value + "=".repeat((4 - value.length % 4) % 4);
    const raw = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
    return Uint8Array.from(raw, (character) => character.charCodeAt(0));
  };
  const csrfToken = () => document.cookie.split(";").map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken="))?.slice("csrftoken=".length) || "";
  const post = async (url, data) => {
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || "요청을 처리하지 못했습니다.");
    }
    return response.json();
  };

  const updateButton = async () => {
    if (!("Notification" in window) || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      button.disabled = true;
      setMessage("이 브라우저는 PC 알림을 지원하지 않습니다.", true);
      return;
    }
    try {
      const registration = await navigator.serviceWorker.register(config.serviceWorkerUrl, { scope: "/partner-admin/" });
      const subscription = await registration.pushManager.getSubscription();
      button.textContent = subscription ? "PC 예약 알림 끄기" : "PC 예약 알림 켜기";
      if (Notification.permission === "denied") setMessage("브라우저 사이트 설정에서 알림을 허용해 주세요.", true);
      else if (subscription) setMessage("이 PC에서 예약 알림을 받을 수 있습니다.");
      else setMessage("이 PC에서 예약 알림을 받으려면 켜 주세요.");
    } catch (_) {
      button.disabled = true;
      setMessage("알림을 준비하지 못했습니다. HTTPS 접속 여부를 확인해 주세요.", true);
    }
  };

  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await post(config.unsubscribeUrl, { endpoint: subscription.endpoint });
        await subscription.unsubscribe();
        setMessage("이 PC의 예약 알림을 껐습니다.");
      } else {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") throw new Error("브라우저 알림 권한을 허용해 주세요.");
        const created = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: decodeKey(config.publicKey),
        });
        await post(config.subscribeUrl, created.toJSON());
        setMessage("이 PC의 예약 알림을 켰습니다.");
      }
    } catch (error) {
      setMessage(error.message || "알림 설정에 실패했습니다.", true);
    } finally {
      button.disabled = false;
      await updateButton();
    }
  });

  updateButton();
})();
