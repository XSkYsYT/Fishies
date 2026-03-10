const state = { data: null };

function setStatus(msg, error = false) {
  const el = document.getElementById("setup-status");
  if (!el) return;
  el.textContent = msg;
  el.style.color = error ? "#ff6f80" : "";
}

function setActiveTab(target) {
  document.querySelectorAll(".setup-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.target === target);
  });
  document.querySelectorAll(".setup-view").forEach((view) => {
    view.classList.toggle("active", view.id === `setup-${target}`);
  });
}

function createOption(value, text = value) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = text;
  return option;
}

function fillSelect(id, values, selected, includeNone = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";
  if (includeNone) el.appendChild(createOption("None"));
  values.forEach((v) => el.appendChild(createOption(v)));
  el.value = selected || "";
  if (!el.value && el.options.length > 0) el.selectedIndex = 0;
}

function render(data) {
  state.data = data;
  const cfg = data.config || {};

  const homeGrid = document.getElementById("home-keybind-grid");
  if (homeGrid) {
    homeGrid.innerHTML = "";
    const fixed = ["F1 Start", "F2 Pause", "F3 Exit", "F4 Feedback", "F5 Reload", "F7 Redo", "F12 Safe Pause"];
    fixed.forEach((item) => {
      const card = document.createElement("article");
      card.className = "setup-key-card";
      card.innerHTML = `<h3>Fixed Hotkey</h3><p>${item}</p>`;
      homeGrid.appendChild(card);
    });
  }

  const colorInput = document.getElementById("cfg-ColorPreset");
  if (colorInput) colorInput.value = cfg.ColorPreset || "default.ini";

  fillSelect("cfg-SelectedRod", data.rods || [], cfg.SelectedRod || "");
  fillSelect("cfg-SelectedEnchant", data.enchants || [], cfg.SelectedEnchant || "None", true);
  fillSelect(
    "cfg-SelectedSecondaryEnchant",
    data.enchants || [],
    cfg.SelectedSecondaryEnchant || "None",
    true,
  );
  fillSelect("cfg-SelectedBait", data.baits || [], cfg.SelectedBait || "Worm");

  const logs = document.getElementById("setup-logs-box");
  logs.textContent = (data.recentLogs || []).join("\n") || "No logs found.";
}

async function loadSetup() {
  setStatus("Loading setup data...");
  const response = await fetch("/api/setup/config");
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "Failed to load setup config");
  render(payload.data);
  setStatus("Setup loaded.");
}

function collectConfig() {
  const config = {};
  ["ColorPreset", "SelectedRod", "SelectedEnchant", "SelectedSecondaryEnchant", "SelectedBait"].forEach(
    (key) => {
      const input = document.getElementById(`cfg-${key}`);
      config[key] = (input?.value || "").trim();
    },
  );

  return config;
}

async function saveSetup() {
  setStatus("Saving setup...");
  const response = await fetch("/api/setup/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config: collectConfig() }),
  });
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "Failed to save setup");
  render(payload.data);
  setStatus("Setup saved.");
}

function bindEvents() {
  document.querySelectorAll(".setup-tab").forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.target));
  });
  document.getElementById("setup-save")?.addEventListener("click", async () => {
    try {
      await saveSetup();
    } catch (error) {
      setStatus(error.message || "Unable to save setup.", true);
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await loadSetup();
  } catch (error) {
    setStatus(error.message || "Unable to load setup.", true);
  }
});
