/**
 * Editor — vanilla JS, no build step required.
 *
 * Responsibilities:
 *  1. Hydrate form fields from existing draft (server-injected JSON).
 *  2. Manage dynamic list sections (experience, education, skills, projects, languages, certs).
 *  3. Serialize the entire form to ProfileData v1 JSON.
 *  4. POST the draft to /app/profiles/<id>/draft (frontend1 → backend proxy).
 *  5. POST publish and display the resulting public URL.
 *  6. DELETE draft on "Discard".
 */

"use strict";

// ── Helpers ──────────────────────────────────────────────────────────────────

const profileId = window.PROFILE_ID;

function $(sel, ctx = document) {
  return ctx.querySelector(sel);
}

function showError(msg) {
  const el = document.getElementById("error-banner");
  document.getElementById("error-msg").textContent = msg;
  el.classList.remove("hidden");
}

function hideError() {
  document.getElementById("error-banner").classList.add("hidden");
}

function showSaved() {
  const el = document.getElementById("save-status");
  el.textContent = "Saved ✓";
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
}

function csvToList(str) {
  return str
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function listToCsv(arr) {
  return (arr || []).join(", ");
}

// ── Template builders ────────────────────────────────────────────────────────

function buildExperienceCard(data = {}) {
  const id = "exp-" + Date.now() + Math.random();
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "experience";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="field-label">Company *</label>
        <input class="field-input" data-key="company" type="text" value="${esc(data.company)}" placeholder="Acme Corp" />
      </div>
      <div>
        <label class="field-label">Position *</label>
        <input class="field-input" data-key="position" type="text" value="${esc(data.position)}" placeholder="Senior Engineer" />
      </div>
      <div>
        <label class="field-label">Start Date * (YYYY-MM)</label>
        <input class="field-input" data-key="start_date" type="text" maxlength="7" value="${esc(data.start_date)}" placeholder="2020-01" />
      </div>
      <div>
        <label class="field-label">End Date (YYYY-MM or blank for present)</label>
        <input class="field-input" data-key="end_date" type="text" maxlength="7" value="${esc(data.end_date)}" placeholder="2024-06" />
      </div>
      <div>
        <label class="field-label">Location</label>
        <input class="field-input" data-key="location" type="text" value="${esc(data.location)}" placeholder="New York, NY" />
      </div>
      <div class="sm:col-span-2">
        <label class="field-label">Description</label>
        <textarea class="field-input" data-key="description" rows="2" placeholder="What you did in this role...">${esc(data.description)}</textarea>
      </div>
      <div class="sm:col-span-2">
        <label class="field-label">Key Highlights (one per line)</label>
        <textarea class="field-input" data-key="highlights_text" rows="3"
          placeholder="Reduced API latency by 40%&#10;Led migration to microservices">${esc((data.highlights || []).join("\n"))}</textarea>
      </div>
    </div>`;
  return div;
}

function buildEducationCard(data = {}) {
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "education";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="field-label">Institution *</label>
        <input class="field-input" data-key="institution" type="text" value="${esc(data.institution)}" placeholder="MIT" />
      </div>
      <div>
        <label class="field-label">Degree *</label>
        <input class="field-input" data-key="degree" type="text" value="${esc(data.degree)}" placeholder="Bachelor of Science" />
      </div>
      <div>
        <label class="field-label">Field of Study</label>
        <input class="field-input" data-key="field" type="text" value="${esc(data.field)}" placeholder="Computer Science" />
      </div>
      <div>
        <label class="field-label">GPA</label>
        <input class="field-input" data-key="gpa" type="text" value="${esc(data.gpa)}" placeholder="3.9" />
      </div>
      <div>
        <label class="field-label">Start Date * (YYYY-MM)</label>
        <input class="field-input" data-key="start_date" type="text" maxlength="7" value="${esc(data.start_date)}" placeholder="2018-09" />
      </div>
      <div>
        <label class="field-label">End Date (YYYY-MM)</label>
        <input class="field-input" data-key="end_date" type="text" maxlength="7" value="${esc(data.end_date)}" placeholder="2022-06" />
      </div>
    </div>`;
  return div;
}

function buildSkillsCard(data = {}) {
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "skills";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-1 gap-3">
      <div>
        <label class="field-label">Category *</label>
        <input class="field-input" data-key="category" type="text" value="${esc(data.category)}" placeholder="Backend" />
      </div>
      <div>
        <label class="field-label">Skills (comma-separated) *</label>
        <input class="field-input" data-key="items_csv" type="text"
          value="${esc(listToCsv(data.items))}" placeholder="Python, Go, PostgreSQL, Redis" />
        <p class="tag-input-hint">Separate skills with commas</p>
      </div>
    </div>`;
  return div;
}

function buildProjectCard(data = {}) {
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "projects";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="field-label">Project Name *</label>
        <input class="field-input" data-key="name" type="text" value="${esc(data.name)}" placeholder="My Cool Project" />
      </div>
      <div>
        <label class="field-label">URL</label>
        <input class="field-input" data-key="url" type="url" value="${esc(data.url)}" placeholder="https://github.com/..." />
      </div>
      <div class="sm:col-span-2">
        <label class="field-label">Description</label>
        <textarea class="field-input" data-key="description" rows="2"
          placeholder="What this project does and why it matters">${esc(data.description)}</textarea>
      </div>
      <div>
        <label class="field-label">Tech Stack (comma-separated)</label>
        <input class="field-input" data-key="tech_stack_csv" type="text"
          value="${esc(listToCsv(data.tech_stack))}" placeholder="React, TypeScript, Postgres" />
      </div>
      <div>
        <label class="field-label">Highlights (one per line)</label>
        <textarea class="field-input" data-key="highlights_text" rows="2"
          placeholder="Built in 2 weeks&#10;Used by 5k+ users">${esc((data.highlights || []).join("\n"))}</textarea>
      </div>
    </div>`;
  return div;
}

function buildLanguageCard(data = {}) {
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "languages";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="field-label">Language *</label>
        <input class="field-input" data-key="language" type="text" value="${esc(data.language)}" placeholder="English" />
      </div>
      <div>
        <label class="field-label">Proficiency *</label>
        <select class="field-input" data-key="proficiency">
          ${["Native","Fluent","Advanced","Intermediate","Basic"].map(
            (p) => `<option value="${p}" ${data.proficiency === p ? "selected" : ""}>${p}</option>`
          ).join("")}
        </select>
      </div>
    </div>`;
  return div;
}

function buildCertCard(data = {}) {
  const div = document.createElement("div");
  div.className = "list-item-card";
  div.dataset.type = "certifications";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="removeItem(this)">✕</button>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="field-label">Certification Name *</label>
        <input class="field-input" data-key="name" type="text" value="${esc(data.name)}" placeholder="AWS Solutions Architect" />
      </div>
      <div>
        <label class="field-label">Issuer *</label>
        <input class="field-input" data-key="issuer" type="text" value="${esc(data.issuer)}" placeholder="Amazon Web Services" />
      </div>
      <div>
        <label class="field-label">Date (YYYY-MM)</label>
        <input class="field-input" data-key="date" type="text" maxlength="7" value="${esc(data.date)}" placeholder="2023-04" />
      </div>
      <div>
        <label class="field-label">URL</label>
        <input class="field-input" data-key="url" type="url" value="${esc(data.url)}" placeholder="https://..." />
      </div>
    </div>`;
  return div;
}

// ── Item management ──────────────────────────────────────────────────────────

const BUILDERS = {
  experience: buildExperienceCard,
  education: buildEducationCard,
  skills: buildSkillsCard,
  projects: buildProjectCard,
  languages: buildLanguageCard,
  certifications: buildCertCard,
};

function addItem(type, data = {}) {
  const list = document.getElementById(type + "-list");
  const card = BUILDERS[type](data);
  list.appendChild(card);
}

function removeItem(btn) {
  btn.closest(".list-item-card").remove();
}

// ── Serialisation ─────────────────────────────────────────────────────────────

function getVal(el, key) {
  const input = el.querySelector(`[data-key="${key}"]`);
  return input ? input.value.trim() : "";
}

function serializeCard(card) {
  const type = card.dataset.type;

  const g = (k) => getVal(card, k) || null;
  const gs = (k) => getVal(card, k) || "";
  const gc = (k) => csvToList(getVal(card, k));
  const lines = (k) =>
    (getVal(card, k) || "")
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

  if (type === "experience") {
    return {
      company: gs("company"),
      position: gs("position"),
      start_date: gs("start_date"),
      end_date: g("end_date"),
      location: g("location"),
      description: g("description"),
      highlights: lines("highlights_text"),
    };
  }
  if (type === "education") {
    return {
      institution: gs("institution"),
      degree: gs("degree"),
      field: g("field"),
      gpa: g("gpa"),
      start_date: gs("start_date"),
      end_date: g("end_date"),
    };
  }
  if (type === "skills") {
    return { category: gs("category"), items: gc("items_csv") };
  }
  if (type === "projects") {
    return {
      name: gs("name"),
      description: g("description"),
      url: g("url"),
      tech_stack: gc("tech_stack_csv"),
      highlights: lines("highlights_text"),
    };
  }
  if (type === "languages") {
    return { language: gs("language"), proficiency: gs("proficiency") };
  }
  if (type === "certifications") {
    return {
      name: gs("name"),
      issuer: gs("issuer"),
      date: g("date"),
      url: g("url"),
    };
  }
  return {};
}

function collectList(type) {
  return Array.from(
    document.querySelectorAll(`#${type}-list .list-item-card`)
  ).map(serializeCard);
}

function buildPayload() {
  return {
    schema_version: 1,
    personal: {
      full_name: field("p-full_name"),
      title: field("p-title"),
      email: field("p-email"),
      phone: field("p-phone") || null,
      location: field("p-location") || null,
      linkedin: field("p-linkedin") || null,
      github: field("p-github") || null,
      website: field("p-website") || null,
      summary: field("p-summary"),
    },
    experience: collectList("experience"),
    education: collectList("education"),
    skills: collectList("skills"),
    projects: collectList("projects"),
    languages: collectList("languages"),
    certifications: collectList("certifications"),
  };
}

function field(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

// ── Hydration (load draft into form) ─────────────────────────────────────────

function hydrate(draft) {
  if (!draft) return;
  const p = draft.personal || {};
  setField("p-full_name", p.full_name);
  setField("p-title", p.title);
  setField("p-email", p.email);
  setField("p-phone", p.phone);
  setField("p-location", p.location);
  setField("p-linkedin", p.linkedin);
  setField("p-github", p.github);
  setField("p-website", p.website);
  setField("p-summary", p.summary);

  (draft.experience || []).forEach((d) => addItem("experience", d));
  (draft.education || []).forEach((d) => addItem("education", d));
  (draft.skills || []).forEach((d) => addItem("skills", d));
  (draft.projects || []).forEach((d) => addItem("projects", d));
  (draft.languages || []).forEach((d) => addItem("languages", d));
  (draft.certifications || []).forEach((d) => addItem("certifications", d));
}

function setField(id, val) {
  const el = document.getElementById(id);
  if (el && val != null) el.value = val;
}

// ── API calls ────────────────────────────────────────────────────────────────

async function saveDraft() {
  hideError();
  const btn = document.getElementById("btn-save");
  btn.disabled = true;
  btn.textContent = "Saving…";
  try {
    const payload = buildPayload();
    const resp = await fetch(`/app/profiles/${profileId}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError(data.error || "Failed to save draft.");
    } else {
      showSaved();
    }
  } catch (e) {
    showError("Network error while saving draft.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Save Draft";
  }
}

async function publishProfile() {
  hideError();
  const btn = document.getElementById("btn-publish");
  btn.disabled = true;
  btn.textContent = "Publishing…";

  try {
    // Always save draft first so publish sees latest state
    const saveResp = await fetch(`/app/profiles/${profileId}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    if (!saveResp.ok) {
      const d = await saveResp.json();
      showError(d.error || "Draft save failed before publish.");
      return;
    }

    const resp = await fetch(`/app/profiles/${profileId}/publish`, {
      method: "POST",
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError(data.error || "Publish failed.");
    } else {
      const link = document.getElementById("publish-link");
      link.href = data.public_url;
      link.textContent = data.public_url;
      document.getElementById("publish-banner").classList.remove("hidden");
    }
  } catch (e) {
    showError("Network error while publishing.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Publish ↗";
  }
}

async function discardDraft() {
  if (!confirm("Discard the current draft? This cannot be undone.")) return;
  hideError();
  try {
    await fetch(`/app/profiles/${profileId}/draft`, { method: "DELETE" });
    // Reset form
    document.getElementById("editor-form").reset();
    ["experience","education","skills","projects","languages","certifications"].forEach(
      (t) => { document.getElementById(t + "-list").innerHTML = ""; }
    );
    showSaved();
    document.getElementById("save-status").textContent = "Draft discarded";
  } catch (e) {
    showError("Could not discard draft.");
  }
}

// ── Escape helper to prevent XSS in innerHTML ──────────────────────────────

function esc(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── Wire up buttons ──────────────────────────────────────────────────────────

document.getElementById("btn-save").addEventListener("click", saveDraft);
document.getElementById("btn-publish").addEventListener("click", publishProfile);
document.getElementById("btn-discard").addEventListener("click", discardDraft);

// ── Boot: hydrate from server-injected draft ─────────────────────────────────

(function boot() {
  try {
    const raw = document.getElementById("initial-draft").textContent.trim();
    const draft = raw !== "null" ? JSON.parse(raw) : null;
    hydrate(draft);
  } catch (e) {
    console.warn("Could not hydrate draft:", e);
  }
})();
