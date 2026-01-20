const apiBase = "";
const tokenKey = "novelai_token";

const state = {
  token: localStorage.getItem(tokenKey),
  user: null,
  config: null,
  keys: [],
  clientKeys: [],
};

const el = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

const navButtons = document.querySelectorAll(".nav-item");
const sections = document.querySelectorAll(".section");

const sectionTitle = el("sectionTitle");
const authStatus = el("authStatus");
const openAuthBtn = el("openAuthBtn");
const closeAuthBtn = el("closeAuthBtn");
const authModal = el("authModal");
const logoutBtn = el("logoutBtn");
const refreshBtn = el("refreshBtn");
const appRoot = el("appRoot");
const loginScreen = el("loginScreen");
const loginGateBtn = el("loginGateBtn");
const refreshMyLogsBtn = el("refreshMyLogsBtn");
const refreshAdminLogsBtn = el("refreshAdminLogsBtn");

const logFrom = el("logFrom");
const logTo = el("logTo");
const logQuery = el("logQuery");
const applyLogFilterBtn = el("applyLogFilterBtn");
const resetLogFilterBtn = el("resetLogFilterBtn");
const logTabs = el("logTabs");
const adminLogTabBtn = el("adminLogTabBtn");
const logHead = el("logHead");
const logBody = el("logBody");
const logCountHint = el("logCountHint");
const logPrevBtn = el("logPrevBtn");
const logNextBtn = el("logNextBtn");
const logPageInfo = el("logPageInfo");
const logPageSize = el("logPageSize");

const refreshProxyPoolBtn = el("refreshProxyPoolBtn");
const upstreamProxyMode = el("upstreamProxyMode");
const upstreamProxies = el("upstreamProxies");
const upstreamProxiesHint = el("upstreamProxiesHint");
const upstreamProxyCooldown = el("upstreamProxyCooldown");
const upstreamProxyMaxCooldown = el("upstreamProxyMaxCooldown");
const upstreamProxyFailureThreshold = el("upstreamProxyFailureThreshold");
const upstreamProxyFailStreakCap = el("upstreamProxyFailStreakCap");
const upstreamProxyHandle429 = el("upstreamProxyHandle429");
const upstreamProxyHandle5xx = el("upstreamProxyHandle5xx");
const upstreamProxyHandleNetworkErrors = el("upstreamProxyHandleNetworkErrors");
const upstreamProxyCooldown429 = el("upstreamProxyCooldown429");
const upstreamProxyCooldown5xx = el("upstreamProxyCooldown5xx");
const upstreamProxyCooldownError = el("upstreamProxyCooldownError");
const upstreamProxyStickySalt = el("upstreamProxyStickySalt");
const upstreamProxyKeepaliveEnabled = el("upstreamProxyKeepaliveEnabled");
const upstreamProxyKeepaliveInterval = el("upstreamProxyKeepaliveInterval");
const upstreamProxyKeepaliveUrl = el("upstreamProxyKeepaliveUrl");
const saveProxyPoolBtn = el("saveProxyPoolBtn");
const proxyPoolHead = el("proxyPoolHead");
const proxyPoolBody = el("proxyPoolBody");

const loginForm = el("loginForm");
const registerForm = el("registerForm");

// 生图网页端已移除：本站仅提供 API 中转

const keyForm = el("keyForm");
const keysTable = el("keysTable");
const keyListPreview = el("keyListPreview");
const keySummary = el("keySummary");
const adminKeyUploadForm = el("adminKeyUploadForm");

const configForm = el("configForm");
const healthCheckBtn = el("healthCheckBtn");
const adminUsers = el("adminUsers");
const adminKeys = el("adminKeys");
// 生图相关历史展示已移除
const adminNav = el("adminNav");
const poolCard = el("poolCard");
const poolTitle = el("poolTitle");
const quotaMode = el("quotaMode");
const autoHint = el("autoHint");
const modelList = el("modelList");
const refreshModelsBtn = el("refreshModelsBtn");
const allowRegistrationToggle = el("allowRegistrationToggle");
const baseRpmContributorOnlyToggle = el("baseRpmContributorOnlyToggle");
const baseRpmInput = el("baseRpmInput");
const perKeyRpmInput = el("perKeyRpmInput");
const maxRpmInput = el("maxRpmInput");
const keyCooldownInput = el("keyCooldownInput");
const saveCommonConfigBtn = el("saveCommonConfigBtn");
const manualGlobalRpmInput = el("manualGlobalRpmInput");
const adminNodeId = el("adminNodeId");
const multiNodeEnabledBadge = el("multiNodeEnabledBadge");
const healthCheckLeaderOnlyToggle = el("healthCheckLeaderOnlyToggle");
const healthCheckLeaderNodeIdInput = el("healthCheckLeaderNodeIdInput");
const proxyKeepaliveLeaderOnlyToggle = el("proxyKeepaliveLeaderOnlyToggle");
const proxyKeepaliveLeaderNodeIdInput = el("proxyKeepaliveLeaderNodeIdInput");

const clientKeyName = el("clientKeyName");
const clientKeyRotate = el("clientKeyRotate");
const createClientKeyBtn = el("createClientKeyBtn");
const newClientKey = el("newClientKey");
const clientKeysTable = el("clientKeysTable");

function setAuth(token) {
  state.token = token;
  if (token) {
    localStorage.setItem(tokenKey, token);
  } else {
    localStorage.removeItem(tokenKey);
  }
}

function showLoginGate() {
  if (loginScreen) loginScreen.classList.remove("hidden");
  if (appRoot) appRoot.classList.add("hidden");
  authModal.classList.add("show");
}

function hideLoginGate() {
  if (loginScreen) loginScreen.classList.add("hidden");
  if (appRoot) appRoot.classList.remove("hidden");
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    let detail = "Request failed";
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch (err) {
      detail = await response.text();
    }
    throw new Error(detail);
  }
  return response;
}

const sectionLabels = {
  dashboard: "概览",
  generate: "生图",
  keys: "中转 Key",
  logs: "日志",
  admin: "管理",
};

function setSection(sectionId) {
  if (sectionId === "admin" && state.user?.role !== "admin") {
    sectionId = "dashboard";
  }
  sections.forEach((section) => {
    section.classList.toggle("active", section.id === `section-${sectionId}`);
  });
  navButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.section === sectionId);
  });
  sectionTitle.textContent = sectionLabels[sectionId] || sectionId;
}

function updateAuthUI() {
  if (state.user) {
    authStatus.textContent = `已登录：${state.user.username}`;
    openAuthBtn.textContent = "账户 👤";
  } else {
    authStatus.textContent = "未登录";
    openAuthBtn.textContent = "登录 🔐";
  }
  const isAdmin = state.user?.role === "admin";
  if (adminNav) {
    adminNav.classList.toggle("hidden", !isAdmin);
  }
  if (poolCard) {
    poolCard.classList.toggle("hidden", !isAdmin);
  }
  if (adminLogTabBtn) {
    adminLogTabBtn.classList.toggle("hidden", !isAdmin);
  }
  if (refreshAdminLogsBtn) {
    refreshAdminLogsBtn.classList.toggle("hidden", !isAdmin);
  }
  if (poolTitle) {
    poolTitle.textContent = "共享池概况 🧺";
  }
}

function clearSensitiveUiState() {
  state.user = null;
  state.config = null;
  state.keys = [];
  state.clientKeys = [];
  logState.tab = "mine";
  logState.myLogs = [];
  logState.allLogs = [];
  logState.page = 1;
  logState.from = null;
  logState.to = null;
  logState.query = "";
  updateAuthUI();
  updateStatsUI();
  renderKeysTable();
  renderKeyPreview();
  if (adminUsers) {
    adminUsers.innerHTML = "<div class='empty-state'>仅管理员可见。</div>";
  }
  if (adminKeys) {
    adminKeys.innerHTML = "<div class='empty-state'>仅管理员可见。</div>";
  }
  if (modelList) {
    modelList.innerHTML = "<div class='key-chip'>登录后查看模型</div>";
  }
  if (logHead) logHead.innerHTML = "";
  if (logBody) logBody.innerHTML = "<div class='empty-state'>登录后查看使用日志。</div>";
  if (logCountHint) logCountHint.textContent = "-";
  if (logPageInfo) logPageInfo.textContent = "-";
  if (proxyPoolHead) proxyPoolHead.innerHTML = "";
  if (proxyPoolBody) proxyPoolBody.innerHTML = "<div class='empty-state'>仅管理员可见。</div>";
  if (upstreamProxiesHint) upstreamProxiesHint.textContent = "-";
  if (clientKeysTable) {
    clientKeysTable.innerHTML = "<div class='empty-state'>登录后查看中转 Key。</div>";
  }
  if (newClientKey) {
    newClientKey.textContent = "-";
  }
  if (clientKeyName) {
    clientKeyName.value = "";
  }
}

function updateStatsUI() {
  el("statUser").textContent = state.user?.username || "-";
  el("statRole").textContent = state.user?.role || "-";
  el("statManualRpm").textContent =
    state.user?.manual_rpm === null || state.user?.manual_rpm === undefined
      ? "auto"
      : state.user.manual_rpm;

  if (state.config) {
    el("statAutoQuota").textContent = String(state.config.auto_quota_enabled);
    el("statBaseRpm").textContent = state.config.base_rpm;
    el("statPerKeyRpm").textContent = state.config.per_key_rpm;
  } else {
    el("statAutoQuota").textContent = "-";
    el("statBaseRpm").textContent = "-";
    el("statPerKeyRpm").textContent = "-";
  }
}

function renderKeyPreview() {
  keyListPreview.innerHTML = "";
  if (!state.keys.length) {
    keySummary.textContent = "暂无密钥";
    keyListPreview.innerHTML = "<div class='key-chip'>暂无可用密钥</div>";
    return;
  }
  keySummary.textContent = `密钥数 ${state.keys.length}`;
  state.keys.slice(0, 4).forEach((key) => {
    const chip = document.createElement("div");
    chip.className = "key-chip";
    chip.textContent = `#${key.id} 状态:${key.status} 等级:${key.tier ?? "-"}`;
    keyListPreview.appendChild(chip);
  });
}

function renderKeysTable() {
  if (!keysTable) return;
  if (!state.keys.length) {
    keysTable.innerHTML = "<div class='empty-state'>暂无密钥。</div>";
    return;
  }
  keysTable.innerHTML = state.keys
    .map(
      (key) => `
    <div class="table-row">
      <strong>#${key.id}</strong>
      <span>${escapeHtml(key.status)}</span>
      <span>等级 ${escapeHtml(key.tier ?? "-")}</span>
    </div>
  `
    )
    .join("");
}

function renderAdminTables(users, keys) {
  adminUsers.innerHTML = users?.length
    ? users
        .map((user) => {
          const quotaLabel = user.manual_rpm === null || user.manual_rpm === undefined ? "auto" : user.manual_rpm;
          const username = escapeHtml(user.username);
          const role = escapeHtml(user.role);
          const manualRpmValue = escapeHtml(user.manual_rpm ?? "");
          const activeText = user.is_active ? "启用" : "禁用";
          const toggleText = user.is_active ? "禁用" : "启用";
          const quotaLabelSafe = escapeHtml(quotaLabel);
          return `
        <div class="table-row admin-user-row">
          <strong>${username}</strong>
          <span>${role}</span>
          <div class="admin-quota">
            <span class="muted">配额</span>
            <input type="number" min="0" placeholder="auto" value="${manualRpmValue}" data-rpm="${user.id}" />
            <span class="muted">当前：${quotaLabelSafe}</span>
          </div>
          <span>${activeText}</span>
          <div class="row-actions">
            <button class="btn ghost" data-save="${user.id}">保存</button>
            <button class="btn ghost" data-toggle-user="${user.id}" data-active="${user.is_active ? "1" : "0"}">
              ${toggleText}
            </button>
          </div>
        </div>
      `;
        })
        .join("")
    : "<div class='empty-state'>暂无用户数据。</div>";

  adminKeys.innerHTML =
    keys?.length
      ? keys
          .map(
            (key) => `
        <div class="table-row admin-key-row">
          <strong>#${key.id}</strong>
          <span>${escapeHtml(key.username ?? `UID:${key.user_id}`)}</span>
          <span>${escapeHtml(key.status)}</span>
          <span>等级 ${escapeHtml(key.tier ?? "-")}</span>
          <button class="btn ghost" data-toggle="${key.id}">
            ${key.is_enabled ? "禁用" : "启用"}
          </button>
        </div>
      `
          )
          .join("")
      : "<div class='empty-state'>暂无密钥数据。</div>";

  adminKeys.querySelectorAll("button[data-toggle]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/admin/keys/${btn.dataset.toggle}/toggle`, { method: "POST" });
        await refreshAdmin();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  adminUsers.querySelectorAll("button[data-save]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const userId = btn.dataset.save;
      const input = adminUsers.querySelector(`input[data-rpm="${userId}"]`);
      const value = input?.value;
      const payload = value === "" ? { manual_rpm: null } : { manual_rpm: Number(value) };
      try {
        await apiFetch(`/admin/users/${userId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        await refreshAdmin();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  adminUsers.querySelectorAll("button[data-toggle-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const userId = btn.dataset.toggleUser;
      const isActive = btn.dataset.active === "1";
      try {
        await apiFetch(`/admin/users/${userId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !isActive }),
        });
        await refreshAdmin();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

async function refreshMe() {
  if (!state.token) {
    clearSensitiveUiState();
    showLoginGate();
    return;
  }
  try {
    const response = await apiFetch("/auth/me");
    state.user = await response.json();
    updateAuthUI();
    hideLoginGate();
  } catch (err) {
    setAuth(null);
    clearSensitiveUiState();
    showLoginGate();
    return;
  }
  updateStatsUI();
}

async function refreshConfig() {
  if (!state.token) {
    state.config = null;
    updateStatsUI();
    return;
  }
  try {
    const response = await apiFetch("/admin/config");
    state.config = await response.json();
    if (quotaMode) {
      quotaMode.value = state.config.auto_quota_enabled ? "auto" : "manual";
    }
    if (autoHint) {
      autoHint.classList.toggle("hidden", !state.config.auto_quota_enabled);
    }
    if (allowRegistrationToggle) {
      allowRegistrationToggle.checked = Boolean(state.config.allow_registration);
    }
    if (adminNodeId) {
      adminNodeId.textContent = state.config.node_id || "-";
    }
    const multiNodeEnabled = Boolean(state.config.multi_node_enabled);
    if (multiNodeEnabledBadge) {
      multiNodeEnabledBadge.textContent = multiNodeEnabled ? "开启" : "关闭";
      multiNodeEnabledBadge.classList.toggle("ok", multiNodeEnabled);
      multiNodeEnabledBadge.classList.toggle("muted", !multiNodeEnabled);
    }
    if (baseRpmContributorOnlyToggle) {
      baseRpmContributorOnlyToggle.checked = Boolean(state.config.base_rpm_contributor_only);
    }
    if (baseRpmInput) {
      baseRpmInput.value = String(state.config.base_rpm ?? 0);
    }
    if (perKeyRpmInput) {
      perKeyRpmInput.value = String(state.config.per_key_rpm ?? 0);
    }
    if (maxRpmInput) {
      maxRpmInput.value = String(state.config.max_rpm ?? 0);
    }
    if (keyCooldownInput) {
      keyCooldownInput.value = String(state.config.key_cooldown_seconds ?? 0);
    }
    if (manualGlobalRpmInput) {
      manualGlobalRpmInput.value = String(state.config.manual_global_rpm ?? 0);
    }
    if (healthCheckLeaderOnlyToggle) {
      healthCheckLeaderOnlyToggle.checked = Boolean(state.config.health_check_leader_only);
      healthCheckLeaderOnlyToggle.disabled = !multiNodeEnabled;
    }
    if (healthCheckLeaderNodeIdInput) {
      healthCheckLeaderNodeIdInput.value = String(state.config.health_check_leader_node_id ?? "node-1");
      healthCheckLeaderNodeIdInput.disabled = !multiNodeEnabled;
    }
    if (proxyKeepaliveLeaderOnlyToggle) {
      proxyKeepaliveLeaderOnlyToggle.checked = Boolean(state.config.upstream_proxy_keepalive_leader_only);
      proxyKeepaliveLeaderOnlyToggle.disabled = !multiNodeEnabled;
    }
    if (proxyKeepaliveLeaderNodeIdInput) {
      proxyKeepaliveLeaderNodeIdInput.value = String(
        state.config.upstream_proxy_keepalive_leader_node_id ?? "node-1"
      );
      proxyKeepaliveLeaderNodeIdInput.disabled = !multiNodeEnabled;
    }
    if (upstreamProxyMode) {
      upstreamProxyMode.value = state.config.upstream_proxy_mode || "direct";
    }
    if (upstreamProxyCooldown) {
      upstreamProxyCooldown.value = String(state.config.upstream_proxy_cooldown_seconds ?? 10);
    }
    if (upstreamProxyMaxCooldown) {
      upstreamProxyMaxCooldown.value = String(state.config.upstream_proxy_max_cooldown_seconds ?? 120);
    }
    if (upstreamProxyStickySalt) {
      upstreamProxyStickySalt.value = state.config.upstream_proxy_sticky_salt || "";
    }
    if (upstreamProxyFailureThreshold) {
      upstreamProxyFailureThreshold.value = String(state.config.upstream_proxy_failure_threshold ?? 1);
    }
    if (upstreamProxyFailStreakCap) {
      upstreamProxyFailStreakCap.value = String(state.config.upstream_proxy_fail_streak_cap ?? 6);
    }
    if (upstreamProxyHandle429) {
      upstreamProxyHandle429.checked = Boolean(state.config.upstream_proxy_handle_429);
    }
    if (upstreamProxyHandle5xx) {
      upstreamProxyHandle5xx.checked = Boolean(state.config.upstream_proxy_handle_5xx);
    }
    if (upstreamProxyHandleNetworkErrors) {
      upstreamProxyHandleNetworkErrors.checked = Boolean(state.config.upstream_proxy_handle_network_errors);
    }
    if (upstreamProxyCooldown429) {
      upstreamProxyCooldown429.value = String(state.config.upstream_proxy_cooldown_429_seconds ?? 10);
    }
    if (upstreamProxyCooldown5xx) {
      upstreamProxyCooldown5xx.value = String(state.config.upstream_proxy_cooldown_5xx_seconds ?? 15);
    }
    if (upstreamProxyCooldownError) {
      upstreamProxyCooldownError.value = String(state.config.upstream_proxy_cooldown_error_seconds ?? 10);
    }
    if (upstreamProxyKeepaliveEnabled) {
      upstreamProxyKeepaliveEnabled.checked = Boolean(state.config.upstream_proxy_keepalive_enabled);
    }
    if (upstreamProxyKeepaliveInterval) {
      upstreamProxyKeepaliveInterval.value = String(
        state.config.upstream_proxy_keepalive_interval_seconds ?? 300
      );
    }
    if (upstreamProxyKeepaliveUrl) {
      upstreamProxyKeepaliveUrl.value = state.config.upstream_proxy_keepalive_url || "https://api.novelai.net/";
    }
    if (upstreamProxiesHint) {
      upstreamProxiesHint.textContent = state.config.upstream_proxies_configured
        ? "已配置（为安全起见不回显明文；如需修改请重新粘贴后保存）"
        : "未配置";
    }
  } catch (err) {
    state.config = null;
  }
  updateStatsUI();
}

async function refreshKeys() {
  if (!state.token || state.user?.role !== "admin") {
    state.keys = [];
    renderKeysTable();
    renderKeyPreview();
    return;
  }
  try {
    const response = await apiFetch("/admin/keys");
    state.keys = await response.json();
  } catch (err) {
    state.keys = [];
  }
  renderKeysTable();
  renderKeyPreview();
}

async function refreshAdmin() {
  if (!state.user?.role || state.user.role !== "admin") {
    adminUsers.innerHTML = "<div class='empty-state'>仅管理员可见。</div>";
    adminKeys.innerHTML = "<div class='empty-state'>仅管理员可见。</div>";
    return;
  }
  try {
    const users = await (await apiFetch("/admin/users")).json();
    const keys = await (await apiFetch("/admin/keys")).json();
    renderAdminTables(users, keys);
  } catch (err) {
    const msg = escapeHtml(err.message);
    adminUsers.innerHTML = `<div class='empty-state'>${msg}</div>`;
    adminKeys.innerHTML = `<div class='empty-state'>${msg}</div>`;
  }
}

async function refreshModels() {
  if (!state.token) {
    if (modelList) {
      modelList.innerHTML = "<div class='key-chip'>登录后查看模型</div>";
    }
    return;
  }
  try {
    const response = await apiFetch("/v1/novelai/models");
    const data = await response.json();
    const models = data.models || [];
    if (!models.length) {
      modelList.innerHTML = "<div class='key-chip'>暂无可用模型</div>";
      return;
    }
    modelList.innerHTML = models
      .map((model) => `<div class="key-chip">${escapeHtml(model)}</div>`)
      .join("");
  } catch (err) {
    if (modelList) {
      modelList.innerHTML = `<div class='key-chip'>${escapeHtml(err.message)}</div>`;
    }
  }
}

function _formatDate(value) {
  if (!value) return "-";
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString();
  } catch (err) {
    return String(value);
  }
}

function renderClientKeysTable(keys) {
  if (!clientKeysTable) return;
  if (!keys?.length) {
    clientKeysTable.innerHTML = "<div class='empty-state'>暂无中转 Key。</div>";
    return;
  }

  clientKeysTable.innerHTML = keys
    .map(
      (key) => `
      <div class="table-row">
        <strong>${escapeHtml(key.prefix)}</strong>
        <span>${escapeHtml(key.name || "-")}</span>
        <span>${key.is_active ? "启用" : "禁用"}</span>
        <div class="row-actions">
          <button class="btn ghost" data-toggle-client-key="${key.id}" data-active="${key.is_active ? "1" : "0"}">
            ${key.is_active ? "禁用" : "启用"}
          </button>
          <button class="btn ghost danger" data-delete-client-key="${key.id}">删除</button>
        </div>
      </div>
      <div class="table-row action">
        <span>创建</span>
        <span>${escapeHtml(_formatDate(key.created_at))}</span>
        <span>最近使用</span>
        <span>${escapeHtml(_formatDate(key.last_used_at))}</span>
      </div>
    `
    )
    .join("");

  clientKeysTable.querySelectorAll("button[data-toggle-client-key]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const keyId = btn.dataset.toggleClientKey;
      const isActive = btn.dataset.active === "1";
      if (isActive) {
        const ok = confirm("确定要禁用这个中转 Key 吗？禁用后该 Key 将无法再调用 API。");
        if (!ok) return;
      }
      try {
        await apiFetch(`/client-keys/${keyId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !isActive }),
        });
        await refreshClientKeys();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  clientKeysTable.querySelectorAll("button[data-delete-client-key]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const keyId = btn.dataset.deleteClientKey;
      const ok = confirm("确定要永久删除这个中转 Key 吗？删除后无法恢复。");
      if (!ok) return;
      try {
        await apiFetch(`/client-keys/${keyId}`, { method: "DELETE" });
        await refreshClientKeys();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

async function refreshClientKeys() {
  if (!state.token) {
    state.clientKeys = [];
    if (clientKeysTable) {
      clientKeysTable.innerHTML = "<div class='empty-state'>登录后查看中转 Key。</div>";
    }
    if (newClientKey) {
      newClientKey.textContent = "-";
    }
    return;
  }
  try {
    const response = await apiFetch("/client-keys");
    state.clientKeys = await response.json();
    renderClientKeysTable(state.clientKeys);
  } catch (err) {
    state.clientKeys = [];
    if (clientKeysTable) {
      clientKeysTable.innerHTML = `<div class='empty-state'>${escapeHtml(err.message)}</div>`;
    }
  }
}

const logState = {
  tab: "mine",
  myLogs: [],
  allLogs: [],
  page: 1,
  pageSize: 50,
  from: null,
  to: null,
  query: "",
};

function _parseLocalDateTimeInput(inputEl) {
  const value = inputEl?.value;
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function _matchesLogFilter(log) {
  const createdAt = log?.created_at ? new Date(log.created_at) : null;
  if (logState.from && createdAt && createdAt < logState.from) return false;
  if (logState.to && createdAt && createdAt > logState.to) return false;

  const q = (logState.query || "").trim().toLowerCase();
  if (!q) return true;

  const hay = [
    log.username,
    log.action,
    log.status,
    String(log.status_code ?? ""),
    log.reject_reason,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return hay.includes(q);
}

function _logBadge(text, tone) {
  const t = escapeHtml(text ?? "-");
  const cls = tone ? `badge ${tone}` : "badge";
  return `<span class="${cls}">${t}</span>`;
}

function renderLogsError(message, tab) {
  if (logHead) logHead.innerHTML = "";
  if (logBody) logBody.innerHTML = `<div class='empty-state'>${escapeHtml(message)}</div>`;
  if (logCountHint) {
    logCountHint.textContent = tab === "all" ? "全站日志加载失败" : "我的日志加载失败";
  }
  if (logPageInfo) logPageInfo.textContent = "-";
}

function renderLogsView(tab) {
  const activeLogs = tab === "all" ? logState.allLogs : logState.myLogs;
  const filtered = activeLogs.filter(_matchesLogFilter);
  const total = filtered.length;
  const pageSize = logState.pageSize;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  logState.page = Math.min(logState.page, totalPages);
  const start = (logState.page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  const columns =
    tab === "all"
      ? ["时间", "用户", "状态", "动作", "耗时", "原因"]
      : ["时间", "状态", "动作", "耗时", "原因"];

  if (logHead) {
    logHead.innerHTML = columns.map((c) => `<div class="log-cell head">${c}</div>`).join("");
    logHead.style.setProperty("--log-cols", String(columns.length));
    logHead.style.setProperty(
      "--log-template",
      tab === "all"
        ? "1.3fr 0.9fr 1.2fr 1.2fr 0.7fr 2.6fr"
        : "1.3fr 1.2fr 1.2fr 0.7fr 2.6fr"
    );
  }
  if (logBody) {
    logBody.style.setProperty("--log-cols", String(columns.length));
    logBody.style.setProperty(
      "--log-template",
      tab === "all"
        ? "1.3fr 0.9fr 1.2fr 1.2fr 0.7fr 2.6fr"
        : "1.3fr 1.2fr 1.2fr 0.7fr 2.6fr"
    );
    if (!items.length) {
      logBody.innerHTML = "<div class='empty-state'>暂无匹配记录。</div>";
    } else {
      logBody.innerHTML = items
        .map((log) => {
          const latency = log.latency_ms ? `${Math.round(log.latency_ms)}ms` : "-";
          const code = Number(log.status_code || 0);
          const codeTone = code >= 500 ? "bad" : code >= 400 ? "warn" : "ok";
          const statusTone =
            log.status === "success" ? "ok" : log.status === "failed" ? "warn" : "muted";
          const statusCell = `${_logBadge(log.status_code ?? "-", codeTone)} ${_logBadge(
            log.status || "-",
            statusTone
          )}`;
          const cells =
            tab === "all"
              ? [
                  escapeHtml(_formatDate(log.created_at)),
                  escapeHtml(log.username || "-"),
                  statusCell,
                  escapeHtml(log.action || "-"),
                  escapeHtml(latency),
                  escapeHtml(log.reject_reason || "-"),
                ]
              : [
                  escapeHtml(_formatDate(log.created_at)),
                  statusCell,
                  escapeHtml(log.action || "-"),
                  escapeHtml(latency),
                  escapeHtml(log.reject_reason || "-"),
                ];
          return `<div class="log-row">${cells
            .map((c) => `<div class="log-cell">${c}</div>`)
            .join("")}</div>`;
        })
        .join("");
    }
  }

  if (logCountHint) {
    logCountHint.textContent =
      tab === "all"
        ? `全站：${total} 条（已加载 ${activeLogs.length} 条）`
        : `我的：${total} 条（已加载 ${activeLogs.length} 条）`;
  }
  if (logPageInfo) {
    logPageInfo.textContent = `${logState.page}/${totalPages}`;
  }
  if (logPrevBtn) logPrevBtn.disabled = logState.page <= 1;
  if (logNextBtn) logNextBtn.disabled = logState.page >= totalPages;
}

function setLogTab(tab) {
  if (tab === "all" && state.user?.role !== "admin") tab = "mine";
  logState.tab = tab;
  logState.page = 1;

  if (logTabs) {
    logTabs.querySelectorAll("button[data-log-tab]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.logTab === tab);
    });
  }
  renderLogsView(tab);
  if (tab === "mine" && !logState.myLogs.length) {
    refreshMyLogs();
  }
  if (tab === "all" && !logState.allLogs.length) {
    refreshAdminLogs();
  }
}

async function refreshMyLogs() {
  if (!state.token) return;
  try {
    const logs = await (await apiFetch("/logs")).json();
    logState.myLogs = Array.isArray(logs) ? logs : [];
    if (logState.tab === "mine") renderLogsView("mine");
  } catch (err) {
    renderLogsError(err.message, "mine");
  }
}

async function refreshAdminLogs() {
  if (!state.user || state.user.role !== "admin") return;
  try {
    const logs = await (await apiFetch("/admin/logs")).json();
    logState.allLogs = Array.isArray(logs) ? logs : [];
    if (logState.tab === "all") renderLogsView("all");
  } catch (err) {
    renderLogsError(err.message, "all");
  }
}

// 生图网页端已移除：无需历史/表单同步

navButtons.forEach((button) => {
  button.addEventListener("click", () => setSection(button.dataset.section));
});

openAuthBtn.addEventListener("click", () => {
  authModal.classList.add("show");
});
closeAuthBtn.addEventListener("click", () => authModal.classList.remove("show"));

logoutBtn.addEventListener("click", () => {
  setAuth(null);
  clearSensitiveUiState();
  setSection("dashboard");
  showLoginGate();
});

refreshBtn.addEventListener("click", async () => {
  await refreshMe();
  await refreshConfig();
  await refreshKeys();
  await refreshAdmin();
  await refreshModels();
  await refreshClientKeys();
  await refreshMyLogs();
  await refreshAdminLogs();
  await refreshProxyPoolStatus();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(loginForm));
  try {
    const response = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    setAuth(data.access_token);
    authModal.classList.remove("show");
    hideLoginGate();
    await refreshMe();
    await refreshConfig();
    await refreshKeys();
    await refreshAdmin();
    await refreshModels();
    await refreshClientKeys();
    await refreshMyLogs();
    await refreshAdminLogs();
    await refreshProxyPoolStatus();
  } catch (err) {
    alert(err.message);
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(registerForm));
  if (payload.password !== payload.confirm_password) {
    alert("两次密码不一致");
    return;
  }
  delete payload.confirm_password;
  try {
    await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    alert("注册成功，请登录。");
  } catch (err) {
    alert(err.message);
  }
});

if (adminKeyUploadForm) {
  adminKeyUploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(adminKeyUploadForm));
    payload.verify_now = Boolean(adminKeyUploadForm.verify_now?.checked);
    try {
      await apiFetch("/admin/keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      adminKeyUploadForm.reset();
      await refreshAdmin();
      await refreshKeys();
    } catch (err) {
      alert(err.message);
    }
  });
}

if (createClientKeyBtn) {
  createClientKeyBtn.addEventListener("click", async () => {
    if (!state.token) {
      showLoginGate();
      return;
    }
    createClientKeyBtn.disabled = true;
    if (newClientKey) newClientKey.textContent = "生成中...";
    try {
      const payload = {
        name: clientKeyName?.value?.trim() || null,
        rotate: Boolean(clientKeyRotate?.checked),
      };
      const response = await apiFetch("/client-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (newClientKey) {
        newClientKey.textContent = data.api_key || "-";
      }
      await refreshClientKeys();
    } catch (err) {
      if (newClientKey) newClientKey.textContent = "-";
      alert(err.message);
    } finally {
      createClientKeyBtn.disabled = false;
    }
  });
}

// 生图网页端已移除：不再绑定生成表单事件

configForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(configForm));
  try {
    await apiFetch("/admin/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshConfig();
    alert("配置已更新");
  } catch (err) {
    alert(err.message);
  }
});

if (quotaMode) {
  quotaMode.addEventListener("change", async () => {
    const isAuto = quotaMode.value === "auto";
    if (autoHint) {
      autoHint.classList.toggle("hidden", !isAuto);
    }
    try {
      await apiFetch("/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: "auto_quota_enabled", value: String(isAuto) }),
      });
      await refreshConfig();
    } catch (err) {
      alert(err.message);
    }
  });
}

if (allowRegistrationToggle) {
  allowRegistrationToggle.addEventListener("change", async () => {
    try {
      await apiFetch("/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key: "allow_registration",
          value: String(allowRegistrationToggle.checked),
        }),
      });
      await refreshConfig();
    } catch (err) {
      alert(err.message);
    }
  });
}

async function _setConfigKey(key, value) {
  await apiFetch("/admin/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value: String(value) }),
  });
}

function renderProxyPoolStatus(data) {
  if (!proxyPoolHead || !proxyPoolBody) return;
  const columns = ["代理", "可用", "冷却", "失败", "最后错误"];
  proxyPoolHead.innerHTML = columns.map((c) => `<div class="log-cell head">${c}</div>`).join("");
  proxyPoolHead.style.setProperty("--log-template", "1.6fr 0.5fr 0.7fr 0.5fr 2.2fr");
  proxyPoolBody.style.setProperty("--log-template", "1.6fr 0.5fr 0.7fr 0.5fr 2.2fr");
  proxyPoolBody.style.setProperty("--log-cols", String(columns.length));

  const items = data?.items || [];
  if (!items.length) {
    proxyPoolBody.innerHTML = "<div class='empty-state'>暂无代理数据。</div>";
    return;
  }
  proxyPoolBody.innerHTML = items
    .map((item) => {
      const ok = item.is_available ? _logBadge("可用", "ok") : _logBadge("冷却", "warn");
      const cd = escapeHtml(item.cooldown_seconds ? `${item.cooldown_seconds}s` : "-");
      const err = escapeHtml(item.last_error || "-");
      const proxy = escapeHtml(item.proxy || "-");
      const streak = escapeHtml(item.fail_streak ?? 0);
      return `<div class="log-row">
        <div class="log-cell"><strong>${proxy}</strong></div>
        <div class="log-cell">${ok}</div>
        <div class="log-cell">${cd}</div>
        <div class="log-cell">${streak}</div>
        <div class="log-cell">${err}</div>
      </div>`;
    })
    .join("");
}

async function refreshProxyPoolStatus() {
  if (!state.user || state.user.role !== "admin") return;
  if (proxyPoolBody) proxyPoolBody.innerHTML = "<div class='empty-state'>加载中...</div>";
  try {
    const data = await (await apiFetch("/admin/proxy-pool")).json();
    renderProxyPoolStatus(data);
  } catch (err) {
    if (proxyPoolBody) proxyPoolBody.innerHTML = `<div class='empty-state'>${escapeHtml(err.message)}</div>`;
  }
}

if (saveCommonConfigBtn) {
  saveCommonConfigBtn.addEventListener("click", async () => {
    try {
      saveCommonConfigBtn.disabled = true;
      await _setConfigKey("base_rpm", Number(baseRpmInput?.value || 0));
      await _setConfigKey("per_key_rpm", Number(perKeyRpmInput?.value || 0));
      await _setConfigKey("max_rpm", Number(maxRpmInput?.value || 0));
      await _setConfigKey("key_cooldown_seconds", Number(keyCooldownInput?.value || 0));
      await _setConfigKey("manual_global_rpm", Number(manualGlobalRpmInput?.value || 0));
      await _setConfigKey(
        "base_rpm_contributor_only",
        Boolean(baseRpmContributorOnlyToggle?.checked)
      );
      await refreshConfig();
      alert("常用配置已保存");
    } catch (err) {
      alert(err.message);
    } finally {
      saveCommonConfigBtn.disabled = false;
    }
  });
}

if (healthCheckLeaderOnlyToggle) {
  healthCheckLeaderOnlyToggle.addEventListener("change", async () => {
    try {
      await _setConfigKey("health_check_leader_only", Boolean(healthCheckLeaderOnlyToggle.checked));
      await refreshConfig();
      alert("已更新（必要时重启节点生效）");
    } catch (err) {
      alert(err.message);
    }
  });
}

if (healthCheckLeaderNodeIdInput) {
  healthCheckLeaderNodeIdInput.addEventListener("change", async () => {
    try {
      await _setConfigKey("health_check_leader_node_id", String(healthCheckLeaderNodeIdInput.value || "node-1"));
      await refreshConfig();
      alert("已更新（必要时重启节点生效）");
    } catch (err) {
      alert(err.message);
    }
  });
}

if (proxyKeepaliveLeaderOnlyToggle) {
  proxyKeepaliveLeaderOnlyToggle.addEventListener("change", async () => {
    try {
      await _setConfigKey(
        "upstream_proxy_keepalive_leader_only",
        Boolean(proxyKeepaliveLeaderOnlyToggle.checked)
      );
      await refreshConfig();
      alert("已更新（必要时重启节点生效）");
    } catch (err) {
      alert(err.message);
    }
  });
}

if (proxyKeepaliveLeaderNodeIdInput) {
  proxyKeepaliveLeaderNodeIdInput.addEventListener("change", async () => {
    try {
      await _setConfigKey(
        "upstream_proxy_keepalive_leader_node_id",
        String(proxyKeepaliveLeaderNodeIdInput.value || "node-1")
      );
      await refreshConfig();
      alert("已更新（必要时重启节点生效）");
    } catch (err) {
      alert(err.message);
    }
  });
}

healthCheckBtn.addEventListener("click", async () => {
  try {
    const response = await apiFetch("/admin/health-check", { method: "POST" });
    const data = await response.json();
    alert(`已检测 ${data.checked} 个密钥`);
  } catch (err) {
    alert(err.message);
  }
});

if (refreshModelsBtn) {
  refreshModelsBtn.addEventListener("click", refreshModels);
}

if (refreshMyLogsBtn) {
  refreshMyLogsBtn.addEventListener("click", async () => {
    await refreshMyLogs();
    setLogTab("mine");
  });
}

if (refreshAdminLogsBtn) {
  refreshAdminLogsBtn.addEventListener("click", async () => {
    await refreshAdminLogs();
    setLogTab("all");
  });
}

if (logTabs) {
  logTabs.querySelectorAll("button[data-log-tab]").forEach((btn) => {
    btn.addEventListener("click", () => setLogTab(btn.dataset.logTab));
  });
}

if (applyLogFilterBtn) {
  applyLogFilterBtn.addEventListener("click", () => {
    logState.from = _parseLocalDateTimeInput(logFrom);
    logState.to = _parseLocalDateTimeInput(logTo);
    logState.query = logQuery?.value || "";
    logState.page = 1;
    renderLogsView(logState.tab);
  });
}

if (resetLogFilterBtn) {
  resetLogFilterBtn.addEventListener("click", () => {
    if (logFrom) logFrom.value = "";
    if (logTo) logTo.value = "";
    if (logQuery) logQuery.value = "";
    logState.from = null;
    logState.to = null;
    logState.query = "";
    logState.page = 1;
    renderLogsView(logState.tab);
  });
}

if (logPrevBtn) {
  logPrevBtn.addEventListener("click", () => {
    logState.page = Math.max(1, logState.page - 1);
    renderLogsView(logState.tab);
  });
}

if (logNextBtn) {
  logNextBtn.addEventListener("click", () => {
    logState.page = logState.page + 1;
    renderLogsView(logState.tab);
  });
}

if (logPageSize) {
  logPageSize.addEventListener("change", () => {
    const size = Number(logPageSize.value || 50);
    logState.pageSize = Number.isFinite(size) && size > 0 ? size : 50;
    logState.page = 1;
    renderLogsView(logState.tab);
  });
}

if (refreshProxyPoolBtn) {
  refreshProxyPoolBtn.addEventListener("click", refreshProxyPoolStatus);
}

if (saveProxyPoolBtn) {
  saveProxyPoolBtn.addEventListener("click", async () => {
    try {
      saveProxyPoolBtn.disabled = true;
      await _setConfigKey("upstream_proxy_mode", upstreamProxyMode?.value || "direct");
      await _setConfigKey("upstream_proxy_cooldown_seconds", Number(upstreamProxyCooldown?.value || 10));
      await _setConfigKey(
        "upstream_proxy_max_cooldown_seconds",
        Number(upstreamProxyMaxCooldown?.value || 120)
      );
      await _setConfigKey("upstream_proxy_sticky_salt", upstreamProxyStickySalt?.value || "");
      await _setConfigKey(
        "upstream_proxy_failure_threshold",
        Number(upstreamProxyFailureThreshold?.value || 1)
      );
      await _setConfigKey(
        "upstream_proxy_fail_streak_cap",
        Number(upstreamProxyFailStreakCap?.value || 6)
      );
      await _setConfigKey("upstream_proxy_handle_429", Boolean(upstreamProxyHandle429?.checked));
      await _setConfigKey("upstream_proxy_handle_5xx", Boolean(upstreamProxyHandle5xx?.checked));
      await _setConfigKey(
        "upstream_proxy_handle_network_errors",
        Boolean(upstreamProxyHandleNetworkErrors?.checked)
      );
      await _setConfigKey(
        "upstream_proxy_cooldown_429_seconds",
        Number(upstreamProxyCooldown429?.value || 10)
      );
      await _setConfigKey(
        "upstream_proxy_cooldown_5xx_seconds",
        Number(upstreamProxyCooldown5xx?.value || 15)
      );
      await _setConfigKey(
        "upstream_proxy_cooldown_error_seconds",
        Number(upstreamProxyCooldownError?.value || 10)
      );
      await _setConfigKey(
        "upstream_proxy_keepalive_enabled",
        Boolean(upstreamProxyKeepaliveEnabled?.checked)
      );
      await _setConfigKey(
        "upstream_proxy_keepalive_interval_seconds",
        Number(upstreamProxyKeepaliveInterval?.value || 300)
      );
      await _setConfigKey(
        "upstream_proxy_keepalive_url",
        upstreamProxyKeepaliveUrl?.value || "https://api.novelai.net/"
      );

      const rawProxies = upstreamProxies?.value || "";
      const normalized = rawProxies
        .split(/[\n,]+/)
        .map((s) => s.trim())
        .filter(Boolean)
        .join(",");
      if (normalized) {
        await _setConfigKey("upstream_proxies", normalized);
      }

      await refreshConfig();
      await refreshProxyPoolStatus();
      alert("代理配置已保存（探活定时任务开关需要重启后才会开始/停止）");
    } catch (err) {
      alert(err.message);
    } finally {
      saveProxyPoolBtn.disabled = false;
    }
  });
}

if (loginGateBtn) {
  loginGateBtn.addEventListener("click", () => authModal.classList.add("show"));
}

(async () => {
  await refreshMe();
  if (!state.token || !state.user) return;
  await refreshConfig();
  await refreshKeys();
  await refreshAdmin();
  await refreshModels();
  await refreshClientKeys();
  await refreshMyLogs();
  await refreshAdminLogs();
  await refreshProxyPoolStatus();
})();
