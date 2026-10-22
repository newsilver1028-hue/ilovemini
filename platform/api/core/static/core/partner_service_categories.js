(function () {
  "use strict";

  function csrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    const cookie = document.cookie.split("; ").find((item) => item.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
  }

  function addChoice(list, value, label) {
    const existing = Array.from(list.querySelectorAll('input[type="checkbox"]'))
      .find((input) => input.value === value);
    if (existing) {
      existing.checked = true;
      return;
    }

    const id = "id_service_categories_" + list.querySelectorAll('input[type="checkbox"]').length;
    const wrapper = document.createElement("div");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "service_categories";
    input.value = value;
    input.id = id;
    input.checked = true;
    const text = document.createElement("label");
    text.htmlFor = id;
    text.textContent = label;
    wrapper.append(input, text);
    list.appendChild(wrapper);
  }

  function init() {
    const list = document.getElementById("id_service_categories");
    if (!list || list.dataset.addFieldReady === "true") return;
    list.dataset.addFieldReady = "true";

    const addUrl = list.dataset.addUrl;
    if (!addUrl) return;
    const row = document.createElement("div");
    row.className = "partner-service-category-add";
    const input = document.createElement("input");
    input.type = "text";
    input.maxLength = 80;
    input.placeholder = "새 서비스 분야";
    input.setAttribute("aria-label", "새 서비스 분야");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "button";
    button.textContent = "+ 분야 추가";
    const message = document.createElement("span");
    message.setAttribute("role", "status");
    row.append(input, button, message);
    list.insertAdjacentElement("afterend", row);

    async function submit() {
      const name = input.value.trim().replace(/\s+/g, " ");
      if (!name) {
        message.textContent = "분야 이름을 입력해 주세요.";
        input.focus();
        return;
      }
      button.disabled = true;
      message.textContent = "추가 중…";
      try {
        const response = await fetch(addUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-CSRFToken": csrfToken(),
          },
          body: new URLSearchParams({ name }).toString(),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "분야를 추가하지 못했습니다.");
        addChoice(list, result.value, result.label);
        input.value = "";
        message.textContent = "분야를 추가하고 선택했습니다.";
      } catch (error) {
        message.textContent = error.message || "분야를 추가하지 못했습니다.";
      } finally {
        button.disabled = false;
      }
    }

    button.addEventListener("click", submit);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
