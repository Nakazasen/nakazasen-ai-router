const sensitiveMarkers = ["api_key", "authorization", "bearer", "secret", "token", "prompt", "payload"];
const blueprintsFallback = [
  { repo: "mat-the-website", pattern: "Backend SDK", workloads: ["content_generation", "summarization"], pieces: ["AIRouter", "quota", "metrics"] },
  { repo: "translation_app", pattern: "Embedded worker", workloads: ["long_context", "segmented_batch"], pieces: ["segment_text", "SQLiteJobStore", "AIRouter"] },
  { repo: "AIOS_habbit", pattern: "Local assistant", workloads: ["reasoning", "planning"], pieces: ["AIRouter", "jobs", "metrics"] },
  { repo: "SlideGenius", pattern: "Generation pipeline", workloads: ["structured_json", "content_generation"], pieces: ["segment_text", "quota", "AIRouter"] }
];

function normalizeDashboardData(raw) {
  const root = raw.metrics ? raw.metrics : raw;
  return {
    router: root.router || {},
    jobs: root.jobs || {},
    quota: raw.quota || root.quota || raw.snapshot || {},
    blueprints: raw.blueprints || blueprintsFallback,
    generated_at: root.generated_at || raw.generated_at || Date.now() / 1000
  };
}

function renderDashboard(raw) {
  const text = JSON.stringify(raw).toLowerCase();
  const hasSensitiveMarkers = sensitiveMarkers.some((marker) => text.includes(marker));
  const data = normalizeDashboardData(raw);
  renderOverview(data);
  renderProviders(data.router);
  renderJobs(data.jobs);
  renderQuota(data.quota);
  renderBlueprints(data.blueprints);
  document.getElementById("metricsSummary").textContent = JSON.stringify({
    generated_at: data.generated_at,
    router: data.router,
    jobs: data.jobs,
    quota_profiles: (data.quota.profiles || []).length
  }, null, 2);
  setStatus(hasSensitiveMarkers ? "Loaded with sensitive marker warning; values are summarized only." : "Dashboard updated successfully.", hasSensitiveMarkers);
}

function renderOverview(data) {
  const router = data.router || {};
  const jobs = data.jobs || {};
  const byStatus = jobs.by_status || {};
  document.getElementById("providerTotal").textContent = router.total_candidates || Object.keys(router.by_provider || {}).length || 0;
  document.getElementById("providerHealthy").textContent = `${router.healthy || 0} healthy`;
  document.getElementById("jobTotal").textContent = jobs.total_jobs || 0;
  document.getElementById("jobActive").textContent = `${(byStatus.pending || 0) + (byStatus.running || 0) + (byStatus.retry_later || 0)} active`;
  document.getElementById("successCount").textContent = router.success_count || byStatus.succeeded || 0;
  document.getElementById("failureCount").textContent = `${router.failure_count || byStatus.failed || 0} failures`;
  document.getElementById("latencyAvg").textContent = router.latency_ms_avg ? `${router.latency_ms_avg} ms` : "--";
  document.getElementById("healthLabel").textContent = (router.dead || byStatus.failed) ? "Needs attention" : "Operational";
}

function renderProviders(router) {
  const container = document.getElementById("providerCards");
  const providers = router.by_provider || {};
  container.innerHTML = Object.entries(providers).map(([name, stats]) => {
    const status = stats.healthy ? "healthy" : stats.cooldown ? "cooldown" : stats.dead ? "failed" : "unknown";
    return `<article class="mini-card"><h3>${escapeHtml(name)}</h3><span class="badge ${status}">${status}</span><p>${stats.total || 0} candidate · ${stats.healthy || 0} healthy · ${stats.cooldown || 0} cooldown</p></article>`;
  }).join("") || `<article class="mini-card"><h3>No providers</h3><p>Load metrics JSON to inspect provider health.</p></article>`;
}

function renderJobs(jobs) {
  const container = document.getElementById("jobBars");
  const byStatus = jobs.by_status || {};
  const total = Math.max(1, jobs.total_jobs || Object.values(byStatus).reduce((a, b) => a + Number(b || 0), 0));
  container.innerHTML = Object.entries(byStatus).map(([status, count]) => {
    const width = Math.round((Number(count || 0) / total) * 100);
    return `<div class="bar-row"><strong>${escapeHtml(status)}</strong><div class="bar"><span style="width:${width}%"></span></div><span>${count}</span></div>`;
  }).join("") + `<p class="status-text">Due now: ${jobs.due_now || 0} · Expired running: ${jobs.expired_running || 0}</p>`;
}

function renderQuota(quota) {
  const container = document.getElementById("quotaCards");
  const profiles = quota.profiles || [];
  container.innerHTML = profiles.map((profile) => {
    const policy = profile.policy || {};
    const usage = profile.usage || {};
    const enabled = policy.enabled !== false;
    return `<article class="mini-card"><h3>${escapeHtml(profile.provider || "provider")}</h3><span class="badge ${enabled ? "enabled" : "disabled"}">${enabled ? "enabled" : "disabled"}</span><p>RPM ${valueOrUnlimited(policy.requests_per_minute)} · TPM ${valueOrUnlimited(policy.tokens_per_minute)} · concurrency ${valueOrUnlimited(policy.max_concurrency)}</p><p>in-flight ${usage.in_flight || 0} · today ${usage.requests_today || 0} · cost ${escapeHtml(policy.cost_tier || "unknown")}</p></article>`;
  }).join("") || `<article class="mini-card"><h3>No quota profiles</h3><p>Load quota snapshot JSON to inspect capacity.</p></article>`;
}

function renderBlueprints(blueprints) {
  const container = document.getElementById("blueprintCards");
  container.innerHTML = blueprints.map((item) => `<article class="mini-card"><h3>${escapeHtml(item.repo)}</h3><span class="badge healthy">${escapeHtml(item.pattern)}</span><p>Workloads: ${(item.workloads || []).map(escapeHtml).join(", ")}</p><p>SDK pieces: ${(item.pieces || []).map(escapeHtml).join(" · ")}</p></article>`).join("");
}

function valueOrUnlimited(value) { return value === null || value === undefined ? "∞" : value; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[char])); }
function setStatus(message, warning = false) { const el = document.getElementById("importStatus"); el.textContent = message; el.style.color = warning ? "var(--warning)" : "var(--success)"; }

async function loadSample() {
  try {
    const response = await fetch("sample_metrics.json");
    renderDashboard(await response.json());
  } catch (error) {
    setStatus(`Could not auto-load sample JSON. Paste JSON below. ${error.message}`, true);
  }
}

document.getElementById("parseButton").addEventListener("click", () => {
  try { renderDashboard(JSON.parse(document.getElementById("jsonInput").value)); }
  catch (error) { setStatus(`Invalid JSON: ${error.message}`, true); }
});

document.getElementById("jsonFile").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try { renderDashboard(JSON.parse(await file.text())); }
  catch (error) { setStatus(`Invalid JSON file: ${error.message}`, true); }
});

loadSample();
