// Job Copilot Web Dashboard Client Logic
let socket = null;
let currentProfile = {};

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  connectWebSocket();
  fetchStats();
  fetchProfile();
  fetchApplications();
  fetchInvisibleDotsStatus();
  bindCopilotControls();
  bindWellfoundQueueControls();
  bindInvisibleDotsControls();
  bindCoverLetterStudio();
  bindProfileForm();
  bindTrackerModal();
});

// TABS NAVIGATION
function initTabs() {
  const tabs = document.querySelectorAll(".nav-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const targetPane = tab.getAttribute("data-tab");
      document.querySelectorAll(".tab-pane").forEach(pane => {
        pane.classList.remove("active");
      });
      const activePane = document.getElementById(`pane-${targetPane}`);
      if (activePane) activePane.classList.add("active");
    });
  });
}

// WEBSOCKET LOG STREAM
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

  const wsStatusPill = document.getElementById("wsStatusPill");
  const wsStatusText = document.getElementById("wsStatusText");

  try {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      wsStatusPill.classList.add("online");
      wsStatusText.innerText = "Live Connected";
      addLogEntry("00:00:00", "SUCCESS", "Real-time diagnostic stream connected.");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "log") {
          addLogEntry(data.timestamp, data.level, data.message);
        } else if (data.type === "status") {
          updateBrowserStatus(data.is_running, data.current_url);
        } else if (data.type === "stats") {
          updateKpis(data);
        } else if (data.type === "wellfound_review") {
          showWellfoundReview(data);
        } else if (data.type === "wellfound_finished" || data.type === "wellfound_stopped") {
          hideWellfoundReview();
          fetchStats();
          fetchApplications();
        }
      } catch (err) {
        console.error("WS Parse error:", err);
      }
    };

    socket.onclose = () => {
      wsStatusPill.classList.remove("online");
      wsStatusText.innerText = "Reconnecting...";
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = () => {
      wsStatusPill.classList.remove("online");
      wsStatusText.innerText = "Disconnected";
    };
  } catch (err) {
    console.error("WS Error:", err);
  }
}

function addLogEntry(time, level, message) {
  const stream = document.getElementById("consoleStream");
  const entry = document.createElement("div");
  entry.className = `log-entry ${level.toLowerCase()}`;

  entry.innerHTML = `
    <span class="log-time">[${time}]</span>
    <span class="log-level">[${level.toUpperCase()}]</span>
    <span class="log-msg">${escapeHtml(message)}</span>
  `;

  stream.appendChild(entry);

  const autoScroll = document.getElementById("chkAutoScroll").checked;
  if (autoScroll) {
    stream.scrollTop = stream.scrollHeight;
  }
}

function updateBrowserStatus(isRunning, url) {
  const pill = document.getElementById("browserStatusPill");
  const text = document.getElementById("browserStatusText");
  if (isRunning) {
    pill.classList.add("active");
    text.innerText = url ? `Active: ${truncateUrl(url)}` : "Browser: Active";
  } else {
    pill.classList.remove("active");
    text.innerText = "Browser: Standby";
  }
}

function truncateUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname;
  } catch {
    return "Portal";
  }
}

// KPI STATS
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    updateKpis(data);
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

function updateKpis(stats) {
  document.getElementById("kpiTotalNum").innerText = stats.total_applied || 0;
  document.getElementById("kpiPercentBadge").innerText = `${stats.progress_percent || 0}%`;
  document.getElementById("kpiTotalFill").style.width = `${stats.progress_percent || 0}%`;

  document.getElementById("kpiTechNum").innerText = stats.tech_count || 0;
  const techPercent = Math.min(100, Math.round(((stats.tech_count || 0) / 100) * 100));
  document.getElementById("kpiTechFill").style.width = `${techPercent}%`;

  document.getElementById("kpiSocialNum").innerText = stats.social_count || 0;
  const socialPercent = Math.min(100, Math.round(((stats.social_count || 0) / 50) * 100));
  document.getElementById("kpiSocialFill").style.width = `${socialPercent}%`;
}

// COPILOT CONTROLS
function bindCopilotControls() {
  // Clear Logs
  document.getElementById("btnClearLogs").addEventListener("click", () => {
    document.getElementById("consoleStream").innerHTML = "";
  });

  // Portal Buttons
  document.querySelectorAll(".portal-btn[data-url]").forEach(btn => {
    btn.addEventListener("click", () => {
      const url = btn.getAttribute("data-url");
      launchBrowser(url);
    });
  });

  // Custom URL Button
  document.getElementById("btnCustomUrl").addEventListener("click", () => {
    const customUrl = prompt("Enter job portal or application URL:", "https://www.linkedin.com/jobs/");
    if (customUrl) launchBrowser(customUrl);
  });

  // Launch Browser
  document.getElementById("btnLaunchBrowser").addEventListener("click", () => {
    launchBrowser("https://www.linkedin.com/jobs/search/?f_AL=true&keywords=Full%20Stack%20Developer");
  });

  // Auto-Fill Form
  document.getElementById("btnAutofill").addEventListener("click", async () => {
    try {
      const res = await fetch("/api/browser/autofill", { method: "POST" });
      const data = await res.json();
    } catch (err) {
      console.error(err);
    }
  });

  // Inject Cover Letter
  document.getElementById("btnInjectCL").addEventListener("click", async () => {
    const company = prompt("Enter target Company Name (or leave blank for generic):", "");
    const role = prompt("Enter Job Title:", "Full-Stack Developer");
    try {
      await fetch("/api/browser/inject-cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, role, category: "Tech" })
      });
    } catch (err) {
      console.error(err);
    }
  });

  // Safe Batch Apply
  document.getElementById("btnSafeBatch").addEventListener("click", async () => {
    try {
      await fetch("/api/browser/safe-batch-step", { method: "POST" });
    } catch (err) {
      console.error(err);
    }
  });

  // Log Application
  document.getElementById("btnLogApplication").addEventListener("click", () => {
    document.getElementById("logModal").classList.add("open");
  });

  // Close Browser
  document.getElementById("btnCloseBrowser").addEventListener("click", async () => {
    try {
      await fetch("/api/browser/close", { method: "POST" });
    } catch (err) {
      console.error(err);
    }
  });
}

async function launchBrowser(targetUrl) {
  try {
    await fetch("/api/browser/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: targetUrl })
    });
  } catch (err) {
    console.error("Launch error:", err);
  }
}

// COVER LETTER STUDIO
function bindCoverLetterStudio() {
  const form = document.getElementById("clForm");
  const subjectBox = document.getElementById("clSubjectBox");
  const bodyBox = document.getElementById("clBodyBox");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const company = document.getElementById("clCompany").value.trim();
    const role = document.getElementById("clRole").value.trim();
    const category = document.getElementById("clCategory").value;

    try {
      const res = await fetch("/api/cover-letter/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, role, category })
      });
      const data = await res.json();
      subjectBox.innerText = `Subject: ${data.subject}`;
      bodyBox.value = data.body;
    } catch (err) {
      console.error(err);
    }
  });

  document.getElementById("btnCopyCL").addEventListener("click", () => {
    const text = `${document.getElementById("clSubjectBox").innerText}\n\n${bodyBox.value}`;
    navigator.clipboard.writeText(text);
    alert("Cover Letter copied to clipboard!");
  });

  document.getElementById("btnInjectFromStudio").addEventListener("click", async () => {
    const company = document.getElementById("clCompany").value.trim();
    const role = document.getElementById("clRole").value.trim();
    const category = document.getElementById("clCategory").value;

    try {
      await fetch("/api/browser/inject-cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, role, category })
      });
    } catch (err) {
      console.error(err);
    }
  });
}

// PROFILE TAB
async function fetchProfile() {
  try {
    const res = await fetch("/api/profile");
    currentProfile = await res.json();

    const p = currentProfile.personal || {};
    const w = currentProfile.work_authorization || {};
    const a = currentProfile.availability || {};
    const c = currentProfile.compensation || {};
    const s = currentProfile.screening_answers || {};

    document.getElementById("profFullName").value = p.full_name || "";
    document.getElementById("profEmail").value = p.email || "";
    document.getElementById("profPhone").value = p.phone || "";
    document.getElementById("profCity").value = p.city || "";
    document.getElementById("profLinkedin").value = p.linkedin || "";
    document.getElementById("profGithub").value = p.github || "";
    document.getElementById("profPortfolio").value = p.portfolio || "";

    document.getElementById("profWorkAuth").value = w.legally_authorized_to_work || "Yes";
    document.getElementById("profSponsorship").value = w.requires_sponsorship || "No";
    document.getElementById("profNotice").value = a.notice_period || "";
    document.getElementById("profRelocate").value = w.willing_to_relocate || "Yes";
    document.getElementById("profSalaryTech").value = c.expected_salary_tech || "";
    document.getElementById("profSalarySocial").value = c.expected_salary_social || "";

    document.getElementById("profPitch").value = s.elevator_pitch || "";
    document.getElementById("profWhyCompany").value = s.why_company || "";
    document.getElementById("profAchievement").value = s.key_achievement || "";
  } catch (err) {
    console.error("Failed to load profile:", err);
  }
}

function bindProfileForm() {
  document.getElementById("btnSaveProfile").addEventListener("click", async () => {
    const updated = {
      ...currentProfile,
      personal: {
        ...currentProfile.personal,
        full_name: document.getElementById("profFullName").value.trim(),
        email: document.getElementById("profEmail").value.trim(),
        phone: document.getElementById("profPhone").value.trim(),
        city: document.getElementById("profCity").value.trim(),
        linkedin: document.getElementById("profLinkedin").value.trim(),
        github: document.getElementById("profGithub").value.trim(),
        portfolio: document.getElementById("profPortfolio").value.trim()
      },
      work_authorization: {
        ...currentProfile.work_authorization,
        legally_authorized_to_work: document.getElementById("profWorkAuth").value,
        requires_sponsorship: document.getElementById("profSponsorship").value,
        willing_to_relocate: document.getElementById("profRelocate").value
      },
      availability: {
        ...currentProfile.availability,
        notice_period: document.getElementById("profNotice").value.trim()
      },
      compensation: {
        ...currentProfile.compensation,
        expected_salary_tech: document.getElementById("profSalaryTech").value.trim(),
        expected_salary_social: document.getElementById("profSalarySocial").value.trim()
      },
      screening_answers: {
        ...currentProfile.screening_answers,
        elevator_pitch: document.getElementById("profPitch").value.trim(),
        why_company: document.getElementById("profWhyCompany").value.trim(),
        key_achievement: document.getElementById("profAchievement").value.trim()
      }
    };

    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated)
      });
      if (res.ok) {
        alert("✅ Profile and screening questions saved successfully!");
        currentProfile = updated;
      }
    } catch (err) {
      console.error("Save profile error:", err);
    }
  });
}

// TRACKER TAB & MODAL
async function fetchApplications() {
  try {
    const res = await fetch("/api/applications");
    const apps = await res.json();
    const tbody = document.getElementById("appsTableBody");
    tbody.innerHTML = "";

    apps.forEach(app => {
      const tr = document.createElement("tr");
      const catClass = (app.Category || "").toLowerCase() === "tech" ? "tech" : "social";
      tr.innerHTML = `
        <td><strong>#${app.ID}</strong></td>
        <td>${app.Date || "-"}</td>
        <td><strong>${escapeHtml(app.Company || "-")}</strong></td>
        <td>${escapeHtml(app.Role || "-")}</td>
        <td><span class="badge-tag ${catClass}">${app.Category || "Tech"}</span></td>
        <td>${escapeHtml(app.Platform || "LinkedIn")}</td>
        <td><span class="badge-active">${app.Status || "Applied"}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load applications:", err);
  }
}

function bindTrackerModal() {
  const modal = document.getElementById("logModal");
  document.getElementById("btnManualLogModal").addEventListener("click", () => modal.classList.add("open"));
  document.getElementById("btnCloseModal").addEventListener("click", () => modal.classList.remove("open"));

  document.getElementById("manualLogForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      company: document.getElementById("logCompany").value.trim(),
      role: document.getElementById("logRole").value.trim(),
      category: document.getElementById("logCategory").value,
      platform: document.getElementById("logPlatform").value.trim()
    };

    try {
      await fetch("/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      modal.classList.remove("open");
      fetchApplications();
      fetchStats();
      document.getElementById("manualLogForm").reset();
    } catch (err) {
      console.error(err);
    }
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// WELLFOUND GUIDED QUEUE CONTROLS
function bindWellfoundQueueControls() {
  const btnStart = document.getElementById("btnStartWellfoundQueue");
  const btnConfirm = document.getElementById("btnConfirmSubmit");
  const btnSkip = document.getElementById("btnSkipCompany");
  const btnStop = document.getElementById("btnStopQueue");

  if (btnStart) {
    btnStart.addEventListener("click", async () => {
      const selectEl = document.getElementById("wellfoundBatchCount");
      const count = parseInt(selectEl ? selectEl.value : "10", 10);
      try {
        btnStart.innerText = "⏳ Starting Queue...";
        btnStart.disabled = true;
        await fetch("/api/wellfound/start-queue", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ max_companies: count })
        });
        setTimeout(() => {
          btnStart.innerText = "▶ Start Queue";
          btnStart.disabled = false;
        }, 2000);
      } catch (err) {
        console.error("Wellfound start error:", err);
        btnStart.disabled = false;
      }
    });
  }

  if (btnConfirm) {
    btnConfirm.addEventListener("click", async () => {
      hideWellfoundReview();
      try {
        await fetch("/api/wellfound/confirm-submit", { method: "POST" });
      } catch (err) {
        console.error("Confirm submit error:", err);
      }
    });
  }

  if (btnSkip) {
    btnSkip.addEventListener("click", async () => {
      hideWellfoundReview();
      try {
        await fetch("/api/wellfound/skip", { method: "POST" });
      } catch (err) {
        console.error("Skip error:", err);
      }
    });
  }

  if (btnStop) {
    btnStop.addEventListener("click", async () => {
      hideWellfoundReview();
      try {
        await fetch("/api/wellfound/stop", { method: "POST" });
      } catch (err) {
        console.error("Stop error:", err);
      }
    });
  }

  // Keyboard shortcut: Press Enter to submit review when overlay is active
  window.addEventListener("keydown", (e) => {
    const overlay = document.getElementById("wellfoundReviewOverlay");
    if (overlay && overlay.classList.contains("open") && e.key === "Enter" && !e.shiftKey) {
      if (btnConfirm) btnConfirm.click();
    }
  });
}

function showWellfoundReview(data) {
  const overlay = document.getElementById("wellfoundReviewOverlay");
  const title = document.getElementById("reviewCompanyTitle");
  const badge = document.getElementById("reviewProgressBadge");
  const noteBox = document.getElementById("reviewNotePreview");

  if (title) title.innerText = `${data.company || "Company"} — ${data.role || "Developer"}`;
  const isContinuous = (data.total_queue || 10) >= 900;
  if (badge) {
    badge.innerText = isContinuous
      ? `Company #${data.current_index || 1} (Continuous)`
      : `Company ${data.current_index || 1} of ${data.total_queue || 10}`;
  }
  if (noteBox) noteBox.innerText = data.note_preview || "";

  if (overlay) overlay.classList.add("open");
}

function hideWellfoundReview() {
  const overlay = document.getElementById("wellfoundReviewOverlay");
  if (overlay) overlay.classList.remove("open");
}

// INVISIBLE_DOTS CONTROL PLANE INTEGRATION
async function fetchInvisibleDotsStatus() {
  const pill = document.getElementById("dotsStatusPill");
  const pillText = document.getElementById("dotsStatusText");
  const badge = document.getElementById("dotsControlStatusBadge");
  const countBadge = document.getElementById("dotsCountBadge");
  const container = document.getElementById("dotsFleetContainer");
  const targetSelect = document.getElementById("taskTargetDot");
  const dbStatus = document.getElementById("dotsDbStatus");
  const llmStatus = document.getElementById("dotsLlmStatus");

  try {
    const res = await fetch("/api/invisibledots/status");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.server_online) {
      if (pill) pill.classList.add("online");
      const dotsCount = (data.dots || []).length;
      if (pillText) pillText.innerText = `Dots: ${dotsCount} VM${dotsCount === 1 ? '' : 's'}`;
      if (badge) {
        badge.className = "badge-dots-live online";
        badge.innerText = "ONLINE (CONTROL PLANE)";
      }
      if (countBadge) countBadge.innerText = `${dotsCount} provisioned`;
      if (dbStatus && data.health && data.health.database_kind) {
        dbStatus.innerText = `${data.health.database_kind.toUpperCase()} (${data.health.database || 'ok'})`;
      }
      if (llmStatus && data.health) {
        llmStatus.innerText = data.health.openrouter_configured ? "OpenRouter Active" : "OpenRouter Not Configured";
      }

      renderDotsFleet(data.dots || []);

      // Populate target select
      if (targetSelect && data.dots && data.dots.length > 0) {
        targetSelect.innerHTML = data.dots.map(d => `
          <option value="${d.name || d.id}">${d.name || d.id} (${(d.config && d.config.model && d.config.model.id) || "Gemini 2.0 Flash"})</option>
        `).join("");
      }
    } else {
      if (pill) pill.classList.remove("online");
      if (pillText) pillText.innerText = "Dots: Offline";
      if (badge) {
        badge.className = "badge-dots-live offline";
        badge.innerText = "OFFLINE (SERVER STOPPED)";
      }
      if (countBadge) countBadge.innerText = "0 provisioned";
      if (container) {
        container.innerHTML = `
          <div class="dots-empty-state">
            <span style="font-size: 32px;">🛑</span>
            <strong>InvisibleDots Server is Offline</strong>
            <p>Start the server in your terminal: <code>cd invisible_dots && node apps/cli/dist/invisible-dots.mjs server</code></p>
            <button class="btn-dots-secondary" onclick="fetchInvisibleDotsStatus()">🔄 Try Reconnecting</button>
          </div>
        `;
      }
    }
  } catch (err) {
    if (pill) pill.classList.remove("online");
    if (pillText) pillText.innerText = "Dots: Unreachable";
    if (badge) {
      badge.className = "badge-dots-live offline";
      badge.innerText = "UNREACHABLE";
    }
    if (container) {
      container.innerHTML = `
        <div class="dots-empty-state">
          <span>⚠️</span>
          <p>Could not connect to invisible-dots status endpoint.</p>
        </div>
      `;
    }
  }
}

function renderDotsFleet(dots) {
  const container = document.getElementById("dotsFleetContainer");
  if (!container) return;

  if (dots.length === 0) {
    container.innerHTML = `
      <div class="dots-empty-state">
        <span style="font-size: 36px;">🤖</span>
        <strong>No Dots Provisioned Yet</strong>
        <p>Click "Connect / Provision Dot" above to create your persistent Job Hunter Agent VM.</p>
        <button class="btn-provision-dot" onclick="handleProvisionJobDot()">➕ Provision job-copilot Dot</button>
      </div>
    `;
    return;
  }

  container.innerHTML = dots.map(dot => {
    const name = dot.name || "dot";
    const id = dot.id || "unknown";
    const status = (dot.status || "STANDBY").toUpperCase();
    const config = dot.config || {};
    const computer = config.computer || { cpu: 2, memory: "4gb", disk: "40gb", idle_timeout: "15m" };
    const model = (config.model && config.model.id) || "google/gemini-2.0-flash-001";
    
    let statusClass = "ready";
    if (status.includes("ERR")) statusClass = "error";
    else if (status.includes("SLEEP") || status.includes("IDLE")) statusClass = "idle";

    const errorHtml = dot.error ? `
      <div style="margin-top: 10px; font-size: 0.75rem; color: #f87171; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 8px 10px; border-radius: 6px;">
        ⚠️ <strong>Notice:</strong> ${escapeHtml(dot.error.includes("images") ? "VM Golden Image required for first boot. Run 'invisible-dots image build'." : dot.error)}
      </div>
    ` : "";

    return `
      <div class="dot-card" id="card-${id}">
        <div class="dot-card-header">
          <div class="dot-card-title-group">
            <div class="dot-card-name">
              <span>🤖</span> ${escapeHtml(name)}
              <span class="dot-id-tag">${id}</span>
            </div>
            <small style="color: var(--text-dim); font-size: 0.75rem;">Created: ${dot.created_at ? new Date(dot.created_at).toLocaleDateString() : 'Active'}</small>
          </div>
          <span class="dot-status-tag ${statusClass}">${status}</span>
        </div>

        <div class="dot-specs-grid">
          <div class="dot-spec-pill">
            <span class="lbl">vCPU</span>
            <span class="val">${computer.cpu || 2} Cores</span>
          </div>
          <div class="dot-spec-pill">
            <span class="lbl">Memory</span>
            <span class="val">${computer.memory || "4gb"} RAM</span>
          </div>
          <div class="dot-spec-pill">
            <span class="lbl">Disk</span>
            <span class="val">${computer.disk || "40gb"}</span>
          </div>
          <div class="dot-spec-pill">
            <span class="lbl">Idle Sleep</span>
            <span class="val">${computer.idle_timeout || "15m"}</span>
          </div>
        </div>

        <div class="dot-model-row">
          <span>🧠 Model: <strong class="dot-model-name">${escapeHtml(model)}</strong></span>
          <span style="font-size: 0.72rem; color: #34d399;">🛡️ Undetectable Playwright Active</span>
        </div>

        ${errorHtml}

        <div class="dot-card-actions">
          <button class="btn-dot-action primary" onclick="prepareTaskForDot('${escapeHtml(name)}')">
            ⚡ Dispatch Mission
          </button>
          <button class="btn-dot-action" onclick="copyToClipboard('${id}', 'Dot ID copied to clipboard!')">
            📋 Copy ID
          </button>
          <a href="http://127.0.0.2:3000/dots/${id}" target="_blank" class="btn-dot-action" style="text-decoration: none;">
            ↗ View in Control Plane
          </a>
        </div>
      </div>
    `;
  }).join("");
}

function prepareTaskForDot(dotName) {
  const select = document.getElementById("taskTargetDot");
  const promptInput = document.getElementById("taskPromptInput");
  if (select) select.value = dotName;
  if (promptInput) {
    promptInput.focus();
    promptInput.scrollIntoView({ behavior: "smooth" });
  }
}

async function handleProvisionJobDot() {
  const btn = document.getElementById("btnProvisionJobDot");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Provisioning...";
  }
  try {
    const res = await fetch("/api/invisibledots/provision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dot_name: "job-copilot", model_id: "google/gemini-2.0-flash-001" })
    });
    const result = await res.json();
    if (result.success) {
      alert("✅ Dot 'job-copilot' successfully connected / provisioned!");
      fetchInvisibleDotsStatus();
    } else {
      alert(`⚠️ Provision notice: ${JSON.stringify(result)}`);
    }
  } catch (err) {
    alert(`Failed to provision dot: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "➕ Connect / Provision Dot";
    }
  }
}

function bindInvisibleDotsControls() {
  const pill = document.getElementById("dotsStatusPill");
  if (pill) {
    pill.addEventListener("click", () => {
      const tabBtn = document.getElementById("tabBtnDots");
      if (tabBtn) tabBtn.click();
    });
  }

  const btnRefresh = document.getElementById("btnRefreshDots");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      fetchInvisibleDotsStatus();
    });
  }

  const btnProvision = document.getElementById("btnProvisionJobDot");
  if (btnProvision) {
    btnProvision.addEventListener("click", handleProvisionJobDot);
  }

  // Preset chips
  const chips = document.querySelectorAll(".chip-preset");
  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      const preset = chip.getAttribute("data-preset");
      const input = document.getElementById("taskPromptInput");
      if (input && preset) {
        input.value = preset;
        input.focus();
      }
    });
  });

  // Task form
  const taskForm = document.getElementById("dotsTaskForm");
  const feedback = document.getElementById("taskDispatchFeedback");
  if (taskForm) {
    taskForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const dotName = document.getElementById("taskTargetDot").value;
      const prompt = document.getElementById("taskPromptInput").value.trim();
      const btnSubmit = document.getElementById("btnDispatchMission");

      if (!prompt) return;

      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerText = "🚀 Dispatching to VM...";
      }

      if (feedback) {
        feedback.style.display = "block";
        feedback.innerText = "Submitting task to VM control plane...";
      }

      try {
        const res = await fetch("/api/invisibledots/task", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dot_name: dotName, prompt: prompt })
        });
        const data = await res.json();
        if (feedback) {
          feedback.innerText = `✅ Mission Queued Successfully!\nTask ID: ${(data.result && (data.result.task_id || data.result.id)) || 'Created'}\nTarget: ${dotName}\nPrompt: "${prompt}"\n\nMonitor live output on the Copilot terminal or at http://127.0.0.2:3000`;
        }
      } catch (err) {
        if (feedback) {
          feedback.innerText = `❌ Error dispatching task: ${err.message}`;
        }
      } finally {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.innerText = "🚀 Dispatch Task to VM";
        }
      }
    });
  }
}


