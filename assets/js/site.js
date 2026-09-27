const DATA_URL = "/assets/data/programs.min.json";
const CONTACT_EMAIL = "steve@northeastforests.com";
const PDF_URL = "/assets/pdf/NFPTC-2026.pdf";
let programsPromise;

const synonyms = new Map([
  ["r&d", "research development"],
  ["research", "r&d research and development"],
  ["machinery", "equipment"],
  ["equipment", "machinery"],
  ["jobs", "hiring employment workforce payroll"],
  ["employees", "workers jobs hiring payroll"],
  ["mill", "sawmill wood-products plant manufacturing"],
  ["sawmill", "mill lumber primary processing"],
  ["kiln", "drying lumber manufacturing"],
  ["pellet", "biomass wood energy fuel"],
  ["chipper", "equipment biomass logging"],
  ["skidder", "logging harvesting equipment"],
  ["forwarder", "logging harvesting equipment"],
  ["truck", "log truck freight hauling"],
  ["chp", "combined heat power biomass energy"],
  ["apprentice", "apprenticeship training workforce"],
  ["payroll", "wages jobs employment"],
  ["enterprise", "enterprise zone economic development"],
  ["opportunity", "opportunity zone rural geographic"],
  ["manufacturing", "mill production wood products"],
  ["logging", "harvesting timber"],
  ["biomass", "wood energy forest residues"],
]);

function loadPrograms() {
  if (!programsPromise) {
    programsPromise = fetch(DATA_URL).then((r) => {
      if (!r.ok) throw new Error(`Unable to load program data: ${r.status}`);
      return r.json();
    });
  }
  return programsPromise;
}

function norm(s) {
  return String(s || "").toLowerCase().replace(/[^a-z0-9&]+/g, " ").trim();
}

function slug(s) {
  return norm(s).replace(/\s+/g, "-");
}

function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}

function truncate(s, n = 180) {
  s = String(s || "").replace(/\s+/g, " ").trim();
  if (s.length <= n) return s;
  const cut = s.slice(0, n - 1).replace(/\s+\S*$/, "").replace(/[ ,;:-]+$/, "");
  return `${cut || s.slice(0, n - 1)}...`;
}

function textFor(p) {
  return norm(Object.values(p).flat(Infinity).join(" "));
}

function expandQuery(q) {
  const parts = norm(q).split(/\s+/).filter(Boolean);
  const out = [...parts];
  for (const part of parts) if (synonyms.has(part)) out.push(...synonyms.get(part).split(/\s+/));
  return [...new Set(out)];
}

function termMatch(haystack, term) {
  return haystack.includes(term) || (term.length >= 4 && haystack.split(/\s+/).some((w) => w.startsWith(term)));
}

function score(p, terms) {
  if (!terms.length) return Number(p.forest_products_fit_score || 0);
  const title = norm(p.title), id = norm(p.id), juris = norm(p.jurisdiction), activity = norm(p.activity), body = p._text || textFor(p);
  let s = 0;
  for (const t of terms) {
    if (termMatch(id, t)) s += 80;
    if (termMatch(title, t)) s += 45;
    if (termMatch(juris, t)) s += 30;
    if (termMatch(activity, t)) s += 20;
    if (termMatch(body, t)) s += 5;
  }
  return s;
}

function params() {
  return new URLSearchParams(location.search);
}

function selected(name) {
  return params().getAll(name).flatMap((v) => v.split(",")).map((v) => v.trim()).filter(Boolean);
}

function setParams(state) {
  const defaults = { sort: state.q ? "relevance" : "fit", federal: true };
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(state)) {
    if (Array.isArray(v) && v.length) sp.set(k, v.join(","));
    else if (typeof v === "string" && v && v !== defaults[k]) sp.set(k, v);
    else if (typeof v === "boolean" && v !== defaults[k]) sp.set(k, v ? "1" : "0");
  }
  const qs = sp.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

function countsFor(rows, values, getter) {
  const c = new Map(values.map((v) => [v, 0]));
  rows.forEach((p) => {
    const got = getter(p);
    (Array.isArray(got) ? got : [got]).forEach((v) => c.set(v, (c.get(v) || 0) + 1));
  });
  return c;
}

function optionList(values, name, selectedVals, counts, labels = {}) {
  return `<div class="check-list">${values.map((v) => {
    const count = counts?.get(v) || 0;
    return `<label class="${count ? "" : "is-zero"}"><input type="checkbox" name="${name}" value="${escapeHtml(v)}" ${selectedVals.includes(String(v)) ? "checked" : ""}> <span>${escapeHtml(labels[v] || v)} <small>(${count})</small></span></label>`;
  }).join("")}</div>`;
}

function highlight(s, terms) {
  const text = truncate(s, 210);
  const words = terms.filter((x) => x.length >= 3).slice(0, 5).map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (!words.length) return escapeHtml(text);
  const re = new RegExp(`(${words.join("|")})`, "ig");
  let out = "", last = 0, match;
  while ((match = re.exec(text))) {
    out += escapeHtml(text.slice(last, match.index));
    out += `<mark>${escapeHtml(match[0])}</mark>`;
    last = match.index + match[0].length;
  }
  return out + escapeHtml(text.slice(last));
}

function card(p, terms = []) {
  const refund = { yes: "Refundable", no: "Not refundable", conditional: "Conditional", "not established": "Not established" }[p.refundable_status] || "Not established";
  const headline = p.headline ? `<p class="formula">${highlight(p.headline, terms)}</p>` : "";
  return `<article class="program-card" data-program-id="${escapeHtml(p.id)}">
    <a class="card-link" href="${escapeHtml(p.url)}">
      <span class="card-top"><span class="jurisdiction-pill">${escapeHtml(p.state_code || "FED")}</span><span class="program-id">${escapeHtml(p.id)}</span></span>
      <h3>${highlight(p.title, terms)}</h3>
      ${headline}
      <p>${highlight(p.summary || p.timing_first_action, terms)}</p>
    </a>
    <div class="badges"><span>Fit ${p.forest_products_fit_score || "?"}/3</span><span>Difficulty ${p.difficulty_score || "?"}/3</span><span>${escapeHtml(refund)}</span></div>
    <button type="button" class="compare-toggle" data-compare-id="${escapeHtml(p.id)}">Compare</button>
  </article>`;
}

function storage(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); } catch { return fallback; }
}

function saveStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}

function compareIdsFromUrl() {
  const ids = params().get("ids");
  return ids ? ids.split(",").map((x) => x.trim()).filter(Boolean).slice(0, 3) : [];
}

function setCompareIds(ids) {
  ids = [...new Set(ids)].slice(0, 3);
  saveStorage("compare", ids);
  if (document.querySelector("[data-compare-page]")) {
    const sp = new URLSearchParams(location.search);
    ids.length ? sp.set("ids", ids.join(",")) : sp.delete("ids");
    history.replaceState(null, "", sp.toString() ? `?${sp.toString()}` : location.pathname);
    initCompare();
  }
  renderCompareTray();
  updateCompareButtons();
}

function getCompareIds() {
  return compareIdsFromUrl().length ? compareIdsFromUrl() : storage("compare", []);
}

async function renderCompareTray() {
  const tray = document.querySelector("[data-compare-tray]");
  if (!tray) return;
  if (document.querySelector("[data-compare-page]")) {
    tray.hidden = true;
    tray.innerHTML = "";
    return;
  }
  const ids = getCompareIds();
  if (!ids.length) {
    tray.hidden = true;
    tray.innerHTML = "";
    return;
  }
  tray.hidden = false;
  const full = ids.length >= 3 ? "<span>Tray full: remove one to add another.</span>" : "";
  tray.innerHTML = `<strong>${ids.length} of 3 selected</strong><span>${ids.map(escapeHtml).join(", ")}</span>${full}<a class="button primary" href="/compare/?ids=${ids.map(encodeURIComponent).join(",")}">Compare now</a><button type="button" data-clear-compare>Clear</button>`;
  tray.querySelector("[data-clear-compare]").onclick = () => setCompareIds([]);
}

function updateCompareButtons(root = document) {
  const ids = getCompareIds();
  root.querySelectorAll("[data-compare-id]").forEach((b) => {
    const on = ids.includes(b.dataset.compareId);
    b.textContent = on ? "Added ✓" : "Compare";
    b.classList.toggle("is-added", on);
    b.disabled = !on && ids.length >= 3;
    b.title = b.disabled ? "Compare tray full: remove one to add another." : "";
    b.onclick = () => {
      let next = getCompareIds();
      if (next.includes(b.dataset.compareId)) next = next.filter((id) => id !== b.dataset.compareId);
      else if (next.length < 3) next = [...next, b.dataset.compareId];
      setCompareIds(next);
    };
  });
}

async function initCompare() {
  const box = document.querySelector("[data-compare-page]");
  if (!box) return;
  const programs = await loadPrograms();
  const rows = getCompareIds().map((id) => programs.find((p) => p.id === id)).filter(Boolean);
  if (!rows.length) {
    box.innerHTML = '<p class="empty">Choose Compare from a result card to add up to three programs.</p>';
    return;
  }
  const fields = [["jurisdiction", "Jurisdiction"], ["activity", "Activity"], ["headline", "Key figure"], ["summary", "Summary"], ["timing_first_action", "Timing"], ["refundable", "Refundable"], ["transferable", "Transferable"], ["carryforward", "Carryforward"], ["difficulty_label", "Difficulty"]];
  box.innerHTML = `<div class="compare-actions"><button type="button" data-print>Print comparison</button><button type="button" data-clear-compare>Clear comparison</button></div><table class="compare-table"><thead><tr><th>Field</th>${rows.map((p) => `<th><a href="${p.url}">${escapeHtml(p.title)}</a><br><small>${escapeHtml(p.id)}</small><br><button type="button" data-remove-compare="${escapeHtml(p.id)}">Remove</button></th>`).join("")}</tr></thead><tbody>${fields.map(([k, l]) => `<tr><th>${l}</th>${rows.map((p) => `<td>${escapeHtml(p[k] || "Not established")}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  box.querySelector("[data-clear-compare]").onclick = () => setCompareIds([]);
  box.querySelectorAll("[data-remove-compare]").forEach((b) => b.onclick = () => setCompareIds(getCompareIds().filter((id) => id !== b.dataset.removeCompare)));
  box.querySelector("[data-print]").onclick = () => print();
}

function debounce(fn, wait = 150) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

async function initSearch(app) {
  const programs = (await loadPrograms()).map((p) => ({ ...p, _text: textFor(p) }));
  const zeroProgramStates = ["Nevada", "South Dakota", "Wyoming"];
  const stateNames = [...new Set([...programs.map((p) => p.jurisdiction), ...zeroProgramStates])].sort((a, b) => (a === "Federal Tax Credits" ? -1 : b === "Federal Tax Credits" ? 1 : a.localeCompare(b)));
  const opts = {
    state: stateNames,
    activity: [...new Set(programs.flatMap((p) => p.activity_tags || []))].sort(),
    business: [...new Set(programs.flatMap((p) => p.business_relevance || []))].sort(),
    timing: [...new Set(programs.flatMap((p) => p.timing_tags || []))].sort(),
    refundable: ["yes", "no", "conditional", "not established"],
    difficulty: ["1", "2", "3"],
    fit: ["3", "2", "1"],
  };
  const labels = {
    refundable: { yes: "Refundable", no: "Not refundable", conditional: "Conditional", "not established": "Not established" },
    difficulty: { 1: "1 - Straightforward", 2: "2 - Certified", 3: "3 - Complex" },
    fit: { 3: "3 - Strong fit", 2: "2 - Conditional fit", 1: "1 - Specialized fit" },
  };
  const q = app.querySelector("#q");
  const sp = params();
  q.value = sp.get("q") || "";
  let visible = 24;

  function getChecked(name) {
    return [...app.querySelectorAll(`input[name="${name}"]:checked`)].map((i) => i.value);
  }

  const categoryLabels = { state: "Jurisdiction", activity: "Activity", business: "Business relevance", timing: "Timing", refundable: "Refundability", difficulty: "Difficulty", fit: "Fit" };

  function getSelections() {
    return {
      state: getChecked("state"),
      activity: getChecked("activity"),
      business: getChecked("business"),
      timing: getChecked("timing"),
      refundable: getChecked("refundable"),
      difficulty: getChecked("difficulty"),
      fit: getChecked("fit"),
    };
  }

  function matchesFilters(p, terms, selections, includeFederal, exclude = "") {
    if (terms.length && score(p, terms) <= 0) return false;
    if (exclude !== "state" && selections.state.length && !(selections.state.includes(p.jurisdiction) || (includeFederal && p.jurisdiction_type === "Federal"))) return false;
    if (exclude !== "activity" && selections.activity.length && !selections.activity.some((x) => (p.activity_tags || []).includes(x))) return false;
    if (exclude !== "business" && selections.business.length && !selections.business.some((x) => (p.business_relevance || []).includes(x))) return false;
    if (exclude !== "timing" && selections.timing.length && !selections.timing.some((x) => (p.timing_tags || []).includes(x))) return false;
    if (exclude !== "refundable" && selections.refundable.length && !selections.refundable.includes(p.refundable_status)) return false;
    if (exclude !== "difficulty" && selections.difficulty.length && !selections.difficulty.includes(String(p.difficulty_score))) return false;
    if (exclude !== "fit" && selections.fit.length && !selections.fit.includes(String(p.forest_products_fit_score))) return false;
    return true;
  }

  function renderFilters(terms = [], selections = {}, includeFederal = true) {
    for (const [name, values] of Object.entries(opts)) {
      const selectedVals = selections[name] || selected(name);
      const seedRows = programs.filter((p) => matchesFilters(p, terms, selections, includeFederal, name));
      const counts = countsFor(seedRows, values, (p) => name === "state" ? p.jurisdiction : name === "activity" ? p.activity_tags : name === "business" ? p.business_relevance : name === "timing" ? p.timing_tags : name === "refundable" ? p.refundable_status : name === "difficulty" ? String(p.difficulty_score) : String(p.forest_products_fit_score));
      app.querySelector(`[data-filter="${name}"]`).innerHTML = optionList(values, name, selectedVals, counts, labels[name] || {});
    }
  }

  renderFilters([], Object.fromEntries(Object.keys(opts).map((name) => [name, selected(name)])), sp.get("federal") !== "0");
  app.querySelector("#includeFederal").checked = sp.get("federal") !== "0";
  app.querySelector("#sort").value = sp.get("sort") || (q.value ? "relevance" : "fit");

  function run(resetVisible = true) {
    if (resetVisible) visible = 24;
    const terms = expandQuery(q.value);
    const selections = getSelections();
    const { state, activity, business, timing, refundable, difficulty, fit } = selections;
    const includeFederal = app.querySelector("#includeFederal").checked;
    renderFilters(terms, selections, includeFederal);
    let rows = programs.map((p) => [p, score(p, terms)]).filter(([p, s]) => {
      return matchesFilters(p, terms, selections, includeFederal) && (!terms.length || s > 0);
    });
    const sort = app.querySelector("#sort").value;
    rows.sort((a, b) => sort === "difficulty" ? (a[0].difficulty_score || 9) - (b[0].difficulty_score || 9) || a[0].title.localeCompare(b[0].title) : sort === "state" ? a[0].jurisdiction.localeCompare(b[0].jurisdiction) || a[0].title.localeCompare(b[0].title) : sort === "name" ? a[0].title.localeCompare(b[0].title) : sort === "fit" ? (b[0].forest_products_fit_score || 0) - (a[0].forest_products_fit_score || 0) || a[0].title.localeCompare(b[0].title) : b[1] - a[1] || a[0].title.localeCompare(b[0].title));
    const slice = rows.slice(0, visible);
    const stateOnly = state.length ? rows.filter(([p]) => p.jurisdiction_type !== "Federal").length : rows.length;
    const fedOnly = state.length ? rows.filter(([p]) => p.jurisdiction_type === "Federal").length : 0;
    app.querySelector("[data-result-count]").textContent = state.length ? `Showing ${Math.min(visible, rows.length)} of ${rows.length}: ${stateOnly} selected-state + ${fedOnly} federal` : `Showing ${Math.min(visible, rows.length)} of ${rows.length} programs`;
    app.querySelector("[data-results]").innerHTML = rows.length ? slice.map(([p]) => card(p, terms)).join("") : '<p class="empty">No programs match the current search. <button type="button" data-remove-last>Remove last filter</button> <a href="/search/">Search all states</a> <a href="/states/federal/">Browse federal credits</a>. This does not mean a business is ineligible.</p>';
    app.querySelector("[data-remove-last]")?.addEventListener("click", () => removeLastFilter({ q, state, activity, business, timing, refundable, difficulty, fit }));
    const show = app.querySelector("[data-show-more]");
    show.hidden = visible >= rows.length;
    show.textContent = `Show more (${rows.length - visible} remaining)`;
    setParams({ q: q.value, state, activity, business, timing, refundable, difficulty, fit, sort, federal: includeFederal });
    renderActive({ q: q.value, state, activity, business, timing, refundable, difficulty, fit });
    updateCompareButtons(app);
  }

  function renderActive(state) {
    const box = app.querySelector("[data-active-filters]");
    const chips = [];
    if (state.q) chips.push(`<button type="button" data-search-chip aria-label="Remove search term">Search: ${escapeHtml(state.q)} ×</button>`);
    for (const [k, v] of Object.entries(state)) {
      if (Array.isArray(v)) for (const item of v) {
        const label = labels[k]?.[item] || item;
        chips.push(`<button type="button" data-chip="${k}" data-value="${escapeHtml(item)}" aria-label="Remove filter ${categoryLabels[k] || k}: ${escapeHtml(label)}">${escapeHtml(categoryLabels[k] || k)}: ${escapeHtml(label)} ×</button>`);
      }
    }
    if (chips.length) chips.push('<button type="button" data-clear-all-chip>Clear all</button>');
    box.innerHTML = chips.join("");
    box.querySelector("[data-search-chip]")?.addEventListener("click", () => { q.value = ""; run(); });
    box.querySelector("[data-clear-all-chip]")?.addEventListener("click", clearAll);
    box.querySelectorAll("[data-chip]").forEach((b) => b.addEventListener("click", () => {
      const input = [...app.querySelectorAll(`input[name="${b.dataset.chip}"]`)].find((i) => i.value === b.dataset.value);
      if (input) input.checked = false;
      run();
    }));
  }

  function removeLastFilter(state) {
    const order = ["fit", "difficulty", "refundable", "timing", "business", "activity", "state"];
    for (const name of order) {
      if (state[name]?.length) {
        const value = state[name][state[name].length - 1];
        const input = [...app.querySelectorAll(`input[name="${name}"]`)].find((i) => i.value === value);
        if (input) input.checked = false;
        run();
        return;
      }
    }
    if (q.value) {
      q.value = "";
      run();
    }
  }

  function clearAll() {
    app.querySelectorAll('input[type="checkbox"]').forEach((i) => { i.checked = i.id === "includeFederal"; });
    q.value = "";
    app.querySelector("#sort").value = "fit";
    run();
  }

  q.addEventListener("input", debounce(() => run()));
  app.querySelector("[data-filter-search='state']")?.addEventListener("input", debounce(() => run(false)));
  app.addEventListener("change", (e) => {
    if (e.target.matches("input[type='checkbox'], select")) run();
  });
  app.querySelector("[data-clear-search]").onclick = () => { q.value = ""; run(); };
  app.querySelector("[data-clear-all]").onclick = clearAll;
  app.querySelector("[data-show-more]").onclick = () => { visible += 24; run(false); };
  app.querySelector("[data-filter-toggle]").onclick = () => app.querySelector("[data-filters]").classList.toggle("is-open");
  app.querySelector("[data-filter-search='state']")?.addEventListener("input", (e) => {
    const term = norm(e.target.value);
    app.querySelectorAll('[data-filter="state"] label').forEach((l) => l.hidden = Boolean(term && !norm(l.textContent).includes(term)));
  });
  if (matchMedia("(min-width: 901px)").matches) app.querySelector("[data-filters]").classList.add("is-open");
  run();
}

function initStateJump() {
  document.querySelectorAll("[data-state-jump]").forEach((select) => {
    const go = select.parentElement.querySelector("[data-state-jump-go]") || document.querySelector("[data-state-jump-go]");
    if (go) go.addEventListener("click", () => { if (select.value) location.href = select.value; });
  });
}

function initFeedback() {
  const dialog = document.querySelector("#feedbackDialog");
  if (!dialog) return;
  document.querySelectorAll("[data-feedback]").forEach((b) => b.addEventListener("click", () => dialog.showModal()));
  const button = document.querySelector("#feedbackEmailButton");
  const msg = document.querySelector("#feedbackMessage");
  const error = document.querySelector("#feedbackError");
  const status = document.querySelector("#feedbackStatus");
  if (!button || !msg || !error || !status) return;
  dialog.querySelectorAll("[data-close-feedback]").forEach((b) => b.addEventListener("click", () => dialog.close()));
  button.onclick = () => {
    if (!msg.value.trim()) {
      error.textContent = "Please enter a correction or question before preparing the email.";
      error.hidden = false;
      msg.focus();
      return;
    }
    error.hidden = true;
    const detail = document.querySelector("[data-program-id]");
    const id = detail?.dataset.programId || "general";
    const subject = `NFPTC correction: ${id}`;
    const body = `Type: ${document.querySelector("#feedbackType").value}\nProgram: ${detail?.dataset.programTitle || ""}\nProgram ID: ${id}\nJurisdiction: ${detail?.dataset.jurisdiction || ""}\nPage URL: ${location.href}\nName: ${document.querySelector("#feedbackName").value}\nEmail: ${document.querySelector("#feedbackEmail").value}\n\nMessage:\n${msg.value}`;
    location.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    status.textContent = "Your email app should now be open.";
    status.hidden = false;
    setTimeout(() => dialog.close(), 350);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  initStateJump();
  document.querySelectorAll("[data-search-app]").forEach(initSearch);
  updateCompareButtons();
  renderCompareTray();
  initCompare();
  initFeedback();
  document.querySelectorAll("[data-print]").forEach((b) => b.addEventListener("click", () => print()));
});
