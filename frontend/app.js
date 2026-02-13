const state = {
  user: {
    token: "",
    actorId: "",
    consentId: "",
    uploadId: "",
    preferenceId: "",
    generationId: "",
    conceptIds: [],
    collaborationId: "",
    collaborationStatus: "",
    pendingUploadFile: null,
    conceptsById: {},
    maskSaved: false,
    maskUri: "",
  },
  artist: {
    token: "",
    actorId: "",
    collaborationId: "",
  },
  admin: {
    token: "",
    actorId: "",
  },
};

  const toastEl = document.getElementById("toast");
  const conceptGridEl = document.getElementById("concept-grid");
  const maskEditorEl = document.getElementById("mask-editor");
  const maskBaseImageEl = document.getElementById("mask-base-image");
  const maskCanvasEl = document.getElementById("mask-canvas");
  const maskBrushEl = document.getElementById("mask-brush");
  const maskClearBtn = document.getElementById("mask-clear-btn");
  const maskSaveBtn = document.getElementById("mask-save-btn");
  const maskContinueBtn = document.getElementById("mask-continue-btn");
  const maskMetaEl = document.getElementById("mask-meta");
  const generationLoadingEl = document.getElementById("generation-loading");
  const generateBtn = document.getElementById("generate-btn");
  const generationElapsedEl = document.getElementById("generation-elapsed");
  const generationCancelBtn = document.getElementById("generation-cancel-btn");
  const generationHintEl = document.getElementById("generation-hint");
  const maskStatusTextEl = document.getElementById("mask-status-text");
  const maskSkipCheckboxEl = document.getElementById("mask-skip-checkbox");
  const inpaintCheckboxEl = document.getElementById("inpaint-checkbox");
const clientStepButtons = [...document.querySelectorAll("#client-stepper .step-btn")];
const clientStepPanels = [...document.querySelectorAll("#user-panel .step-panel")];
const artistStepButtons = [...document.querySelectorAll("#artist-stepper .step-btn")];
const artistStepPanels = [...document.querySelectorAll("#artist-panel .step-panel")];
const adminStepButtons = [...document.querySelectorAll("#admin-stepper .step-btn")];
const adminStepPanels = [...document.querySelectorAll("#admin-panel .step-panel")];
const lightboxEl = document.getElementById("concept-lightbox");
const lightboxImageEl = document.getElementById("lightbox-image");
const lightboxMetaEl = document.getElementById("lightbox-meta");
const lightboxTitleEl = document.getElementById("lightbox-title");
const artistNotesEl = document.getElementById("artist-notes-list");
const journeyLogEl = document.getElementById("journey-log");
const progressEls = {
  userSession: document.getElementById("progress-user-session"),
  consent: document.getElementById("progress-consent"),
  upload: document.getElementById("progress-upload"),
  preference: document.getElementById("progress-preference"),
  generation: document.getElementById("progress-generation"),
  collaboration: document.getElementById("progress-collaboration"),
};
const clientStepOrder = ["intake", "upload", "preference", "generation", "collaboration"];
const artistStepOrder = ["session", "collaboration", "notes"];
const adminStepOrder = ["session", "controls", "metrics"];
let activeClientStep = "intake";
let activeArtistStep = "session";
let activeAdminStep = "session";

function showToast(message, type = "info") {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  toastEl.classList.toggle("error", type === "error");
  window.clearTimeout(showToast.timerId);
  showToast.timerId = window.setTimeout(() => {
    toastEl.classList.remove("show");
  }, 2200);
}

function appendJourney(message) {
  if (!journeyLogEl) {
    return;
  }
  const timestamp = new Date().toLocaleTimeString();
  const existing = journeyLogEl.textContent.trim();
  const lines = existing ? existing.split("\n") : [];
  lines.push(`[${timestamp}] ${message}`);
  journeyLogEl.textContent = lines.slice(-22).join("\n");
  journeyLogEl.scrollTop = journeyLogEl.scrollHeight;
}

function setMeta(id, message) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = message;
  }
}

function setUploadFileLabel(text) {
  const label = document.getElementById("upload-file-label");
  if (label) {
    label.textContent = text;
  }
}

function markProgressStep(element, done) {
  if (!element) {
    return;
  }
  element.classList.toggle("done", Boolean(done));
}

function refreshFlowProgress() {
  markProgressStep(progressEls.userSession, Boolean(state.user.token));
  markProgressStep(progressEls.consent, Boolean(state.user.consentId));
  markProgressStep(progressEls.upload, Boolean(state.user.uploadId));
  markProgressStep(progressEls.preference, Boolean(state.user.preferenceId));
  markProgressStep(progressEls.generation, state.user.conceptIds.length > 0);
  markProgressStep(progressEls.collaboration, state.user.collaborationStatus === "active");
  refreshClientStepper();
}

function refreshClientStepper() {
  if (!clientStepButtons.length) {
    return;
  }
  const completion = {
    intake: Boolean(state.user.token && state.user.consentId),
    upload: Boolean(state.user.uploadId),
    preference: Boolean(state.user.preferenceId),
    generation: state.user.conceptIds.length > 0,
    collaboration: state.user.collaborationStatus === "active",
  };
  for (const button of clientStepButtons) {
    const step = button.dataset.stepTarget;
    button.classList.toggle("active", step === activeClientStep);
    button.classList.toggle("done", Boolean(step && completion[step]));
  }
}

function setActiveClientStep(stepName) {
  if (!stepName || !clientStepOrder.includes(stepName)) {
    return;
  }
  activeClientStep = stepName;
  for (const panel of clientStepPanels) {
    panel.classList.toggle("active", panel.id === `step-${stepName}`);
  }
  refreshClientStepper();
}

function refreshArtistStepper() {
  if (!artistStepButtons.length) {
    return;
  }
  const completion = {
    session: Boolean(state.artist.token),
    collaboration: Boolean(state.artist.collaborationId),
    notes: false,
  };
  for (const button of artistStepButtons) {
    const step = button.dataset.artistStepTarget;
    button.classList.toggle("active", step === activeArtistStep);
    button.classList.toggle("done", Boolean(step && completion[step]));
  }
}

function setActiveArtistStep(stepName) {
  if (!stepName || !artistStepOrder.includes(stepName)) {
    return;
  }
  activeArtistStep = stepName;
  for (const panel of artistStepPanels) {
    panel.classList.toggle("active", panel.id === `artist-step-${stepName}`);
  }
  refreshArtistStepper();
}

function refreshAdminStepper() {
  if (!adminStepButtons.length) {
    return;
  }
  const completion = {
    session: Boolean(state.admin.token),
    controls: Boolean(state.admin.token),
    metrics: false,
  };
  for (const button of adminStepButtons) {
    const step = button.dataset.adminStepTarget;
    button.classList.toggle("active", step === activeAdminStep);
    button.classList.toggle("done", Boolean(step && completion[step]));
  }
}

function setActiveAdminStep(stepName) {
  if (!stepName || !adminStepOrder.includes(stepName)) {
    return;
  }
  activeAdminStep = stepName;
  for (const panel of adminStepPanels) {
    panel.classList.toggle("active", panel.id === `admin-step-${stepName}`);
  }
  refreshAdminStepper();
}

function parseCsv(rawValue) {
  if (!rawValue) {
    return [];
  }
  return rawValue
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function requireToken(role) {
  const token = state[role].token;
  if (!token) {
    throw new Error(`Create ${role} session first.`);
  }
  return token;
}

function setInputValue(formId, name, value) {
  const form = document.getElementById(formId);
  if (!form) {
    return;
  }
  const input = form.elements.namedItem(name);
  if (input && typeof input.value !== "undefined") {
    input.value = value;
  }
}

function setPill(id, label, stateName = "neutral") {
  const el = document.getElementById(id);
  if (!el) {
    return;
  }
  el.textContent = label;
  el.classList.remove("neutral", "good", "warn");
  el.classList.add(stateName);
}

function setActivePanel(panelId) {
  const tabs = [...document.querySelectorAll(".tab")];
  const panels = [...document.querySelectorAll(".panel")];
  for (const panel of panels) {
    panel.classList.toggle("active", panel.id === panelId);
  }
  for (const tab of tabs) {
    tab.classList.toggle("active", tab.dataset.panel === panelId);
  }
}

function openConceptLightbox(concept) {
  if (!lightboxEl || !lightboxImageEl || !lightboxMetaEl || !lightboxTitleEl || !concept) {
    return;
  }
  lightboxImageEl.src = concept.storage_uri;
  lightboxImageEl.alt = `Concept ${concept.id}`;
  lightboxMetaEl.textContent = `Concept ID: ${concept.id} · ${concept.selected ? "Selected" : "Not selected"}`;
  lightboxTitleEl.textContent = `Concept ${concept.id}`;
  lightboxEl.classList.add("open");
  lightboxEl.setAttribute("aria-hidden", "false");
}

function closeConceptLightbox() {
  if (!lightboxEl) {
    return;
  }
  lightboxEl.classList.remove("open");
  lightboxEl.setAttribute("aria-hidden", "true");
}

async function request(path, { method = "GET", token = "", json = undefined, formData = undefined } = {}) {
  const options = { method, headers: {} };
  if (token) {
    options.headers.Authorization = `Bearer ${token}`;
  }
  if (json !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(json);
  }
  if (formData) {
    options.body = formData;
  }
  const response = await fetch(path, options);
  const raw = await response.text();
  let payload = null;
  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = raw;
    }
  }
  if (!response.ok) {
    const code = payload && typeof payload === "object" ? payload.code || "API_ERROR" : "API_ERROR";
    const message =
      payload && typeof payload === "object" ? payload.message || response.statusText : response.statusText;
    throw new Error(`${response.status} ${code}: ${message}`);
  }
  return payload;
}

function formatSeconds(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

async function requestWithTimeout(
  path,
  { method = "GET", token = "", json = undefined, formData = undefined, timeoutMs = 130000, signal = undefined } = {},
) {
  const controller = new AbortController();
  const linked = signal;
  const onAbort = () => controller.abort();
  if (linked) {
    if (linked.aborted) {
      controller.abort();
    } else {
      linked.addEventListener("abort", onAbort, { once: true });
    }
  }
  const timerId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const options = { method, headers: {}, signal: controller.signal };
    if (token) {
      options.headers.Authorization = `Bearer ${token}`;
    }
    if (json !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(json);
    }
    if (formData) {
      options.body = formData;
    }
    const response = await fetch(path, options);
    const raw = await response.text();
    let payload = null;
    if (raw) {
      try {
        payload = JSON.parse(raw);
      } catch {
        payload = raw;
      }
    }
    if (!response.ok) {
      const code = payload && typeof payload === "object" ? payload.code || "API_ERROR" : "API_ERROR";
      const message =
        payload && typeof payload === "object" ? payload.message || response.statusText : response.statusText;
      const details = payload && typeof payload === "object" ? payload.details : null;
      const error = new Error(`${response.status} ${code}: ${message}`);
      error.details = details;
      throw error;
    }
    return payload;
  } finally {
    window.clearTimeout(timerId);
    if (linked) {
      linked.removeEventListener("abort", onAbort);
    }
  }
}

function renderConcepts(concepts) {
  if (!conceptGridEl) {
    return;
  }
  state.user.conceptsById = {};
  conceptGridEl.innerHTML = "";
  if (!concepts.length) {
    const empty = document.createElement("article");
    empty.className = "concept-empty";
    empty.textContent = "No concepts yet. Generate to open your private gallery.";
    conceptGridEl.appendChild(empty);
    return;
  }
  for (const concept of concepts) {
    state.user.conceptsById[concept.id] = concept;
    const card = document.createElement("article");
    card.className = "concept-card";

    const preview = document.createElement("img");
    preview.className = "concept-preview";
    preview.src = concept.storage_uri;
    preview.alt = `Concept ${concept.id}`;
    card.appendChild(preview);

    const row = document.createElement("div");
    row.className = "concept-row";
    const idSpan = document.createElement("span");
    idSpan.textContent = concept.id;
    const selectedSpan = document.createElement("span");
    selectedSpan.textContent = concept.selected ? "selected" : "not selected";
    row.append(idSpan, selectedSpan);
    card.appendChild(row);

    const actions = document.createElement("div");
    actions.className = "concept-actions";

    const viewBtn = document.createElement("button");
    viewBtn.type = "button";
    viewBtn.className = "btn small ghost";
    viewBtn.dataset.action = "view";
    viewBtn.dataset.conceptId = concept.id;
    viewBtn.textContent = "View";

    const selectBtn = document.createElement("button");
    selectBtn.type = "button";
    selectBtn.className = "btn small";
    selectBtn.dataset.action = "select";
    selectBtn.dataset.conceptId = concept.id;
    selectBtn.textContent = "Select";

    const likeBtn = document.createElement("button");
    likeBtn.type = "button";
    likeBtn.className = "btn small ghost";
    likeBtn.dataset.action = "like";
    likeBtn.dataset.conceptId = concept.id;
    likeBtn.textContent = "Like";

    const dislikeBtn = document.createElement("button");
    dislikeBtn.type = "button";
    dislikeBtn.className = "btn small ghost";
    dislikeBtn.dataset.action = "dislike";
    dislikeBtn.dataset.conceptId = concept.id;
    dislikeBtn.textContent = "Dislike";

    actions.append(viewBtn, selectBtn, likeBtn, dislikeBtn);
    card.appendChild(actions);
    conceptGridEl.appendChild(card);
  }
}

function renderNotes(notes) {
  if (!artistNotesEl) {
    return;
  }
  artistNotesEl.innerHTML = "";
  if (!notes.length) {
    artistNotesEl.textContent = "No notes yet.";
    return;
  }
  for (const note of notes) {
    const node = document.createElement("article");
    node.className = "note-item";
    const conceptId = note.concept_id || "general";
    node.textContent = `[${conceptId}] ${note.note_text}`;
    artistNotesEl.appendChild(node);
  }
}

async function refreshHealthStatus() {
  try {
    const data = await request("/healthz");
    setPill("status-health", data.status === "ok" ? "healthy" : "unknown", data.status === "ok" ? "good" : "warn");
    setPill("status-env", String(data.env || "-"), "neutral");
    setPill("status-provider", String(data.model_provider || "-"), "neutral");
    setPill("status-fallback", data.fallback_enabled ? "enabled" : "disabled", data.fallback_enabled ? "good" : "warn");
  } catch (error) {
    setPill("status-health", "offline", "warn");
    appendJourney(`Health check failed: ${error.message}`);
  }
}

function setupTabs() {
  const tabs = [...document.querySelectorAll(".tab")];
  for (const tab of tabs) {
    tab.addEventListener("click", () => setActivePanel(tab.dataset.panel));
  }
}

function setupClientStepper() {
  if (!clientStepButtons.length || !clientStepPanels.length) {
    return;
  }
  for (const button of clientStepButtons) {
    button.addEventListener("click", () => {
      const targetStep = button.dataset.stepTarget;
      if (targetStep) {
        setActiveClientStep(targetStep);
      }
    });
  }
  setActiveClientStep(activeClientStep);
}

function setupArtistStepper() {
  if (!artistStepButtons.length || !artistStepPanels.length) {
    return;
  }
  for (const button of artistStepButtons) {
    button.addEventListener("click", () => {
      const targetStep = button.dataset.artistStepTarget;
      if (targetStep) {
        setActiveArtistStep(targetStep);
      }
    });
  }
  setActiveArtistStep(activeArtistStep);
}

function setupAdminStepper() {
  if (!adminStepButtons.length || !adminStepPanels.length) {
    return;
  }
  for (const button of adminStepButtons) {
    button.addEventListener("click", () => {
      const targetStep = button.dataset.adminStepTarget;
      if (targetStep) {
        setActiveAdminStep(targetStep);
      }
    });
  }
  setActiveAdminStep(activeAdminStep);
}

function setupConceptLightbox() {
  if (!lightboxEl) {
    return;
  }
  const closeButton = document.getElementById("lightbox-close-btn");
  if (closeButton) {
    closeButton.addEventListener("click", closeConceptLightbox);
  }
  lightboxEl.addEventListener("click", (event) => {
    const target = event.target;
    if (target instanceof Element && target.getAttribute("data-lightbox-close") === "true") {
      closeConceptLightbox();
    }
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeConceptLightbox();
    }
  });
}

function setupUploadDropzone() {
  const zone = document.getElementById("upload-dropzone");
  const form = document.getElementById("upload-form");
  if (!zone || !form) {
    return;
  }
  const input = form.elements.namedItem("file");
  if (!(input instanceof HTMLInputElement)) {
    return;
  }

  const assignFile = (file) => {
    if (!(file instanceof File)) {
      return;
    }
    state.user.pendingUploadFile = file;
    setUploadFileLabel(`${file.name} (${Math.round(file.size / 1024)} KB)`);
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
    } catch {
      // Some browsers block programmatic file assignment. Pending file is still kept in state.
    }
  };

  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (file) {
      assignFile(file);
    }
  });

  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("dragover");
  });

  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("dragover");
    const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
    if (file) {
      assignFile(file);
    }
  });
}

function setupPreferenceAssist() {
  const form = document.getElementById("preference-form");
  if (!form) {
    return;
  }
  const chips = [...document.querySelectorAll(".choice-chip")];
  for (const chip of chips) {
    chip.addEventListener("click", () => {
      const target = chip.dataset.prefTarget;
      const addTarget = chip.dataset.prefAdd;
      const value = chip.dataset.prefValue || "";
      if (!value) {
        return;
      }
      if (target) {
        setInputValue("preference-form", target, value);
      } else if (addTarget) {
        const input = form.elements.namedItem(addTarget);
        if (input && typeof input.value === "string") {
          const values = parseCsv(input.value);
          if (!values.includes(value)) {
            values.push(value);
          }
          input.value = values.join(",");
        }
      }
    });
  }
}

async function createSession(role) {
  return request("/api/v1/auth/session", { method: "POST", json: { role } });
}

async function buildSyntheticScarFile() {
  const canvas = document.createElement("canvas");
  canvas.width = 768;
  canvas.height = 768;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Canvas rendering context unavailable.");
  }

  const gradient = ctx.createLinearGradient(0, 0, 768, 768);
  gradient.addColorStop(0, "#f6e6d0");
  gradient.addColorStop(1, "#f2cfad");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 768, 768);

  ctx.strokeStyle = "rgba(179, 72, 57, 0.42)";
  ctx.lineWidth = 16;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(170, 220);
  ctx.bezierCurveTo(330, 170, 430, 430, 590, 360);
  ctx.stroke();

  ctx.strokeStyle = "rgba(250, 240, 230, 0.65)";
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.moveTo(190, 230);
  ctx.bezierCurveTo(320, 210, 430, 420, 560, 350);
  ctx.stroke();

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error("Failed to produce sandbox image blob."));
        return;
      }
      resolve(new File([blob], "sandbox-scar.png", { type: "image/png" }));
    }, "image/png");
  });
}

function setupUserFlow() {
  const userSessionBtn = document.getElementById("user-session-btn");
  const consentForm = document.getElementById("consent-form");
  const uploadForm = document.getElementById("upload-form");
  const preferenceForm = document.getElementById("preference-form");
  const generateForm = document.getElementById("generate-form");
  const inviteForm = document.getElementById("invite-form");
  const revokeBtn = document.getElementById("revoke-btn");
  if (!userSessionBtn || !consentForm || !uploadForm || !preferenceForm || !generateForm || !inviteForm || !revokeBtn) {
    return;
  }

  let generationController = null;
  let generationStartedAt = 0;
  let generationTickTimerId = 0;

  function updateMaskStatus() {
    if (!maskStatusTextEl) {
      return;
    }
    if (state.user.maskSaved && state.user.maskUri) {
      maskStatusTextEl.textContent = "Saved.";
    } else {
      maskStatusTextEl.textContent = "Not marked yet.";
    }
  }

  updateMaskStatus();

  function refreshMaskContinueState() {
    if (!maskContinueBtn) {
      return;
    }
    const skipMask = Boolean(maskSkipCheckboxEl && maskSkipCheckboxEl.checked);
    maskContinueBtn.disabled = !(state.user.maskSaved || skipMask);
  }

  if (maskSkipCheckboxEl) {
    maskSkipCheckboxEl.addEventListener("change", () => refreshMaskContinueState());
  }
  refreshMaskContinueState();

  if (maskContinueBtn) {
    maskContinueBtn.addEventListener("click", () => {
      // Keep the flow gentle: user stays in control.
      setActiveClientStep("preference");
    });
  }

  if (generationCancelBtn) {
    generationCancelBtn.addEventListener("click", () => {
      if (generationController) {
        generationController.abort();
      }
    });
  }

  userSessionBtn.addEventListener("click", async () => {
    try {
      const session = await createSession("user");
      state.user.token = session.token;
      state.user.actorId = session.actor_id;
      setMeta("user-session-meta", `actor_id=${session.actor_id}`);
      refreshFlowProgress();
      showToast("User session created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  consentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("user");
      const form = new FormData(event.currentTarget);
      const payload = {
        policy_version: String(form.get("policy_version") || "consent-v1"),
        disclaimer_accepted: Boolean(form.get("disclaimer_accepted")),
      };
      const consent = await request("/api/v1/consents", { method: "POST", token, json: payload });
      state.user.consentId = consent.id;
      setInputValue("upload-form", "consent_id", consent.id);
      setMeta("consent-meta", `consent_id=${consent.id}`);
      refreshFlowProgress();
      setActiveClientStep("upload");
      showToast("Consent created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("user");
      const form = new FormData(event.currentTarget);
      const consentId = String(form.get("consent_id") || state.user.consentId);
      const file = form.get("file") instanceof File && form.get("file").size > 0 ? form.get("file") : state.user.pendingUploadFile;
      if (!consentId) {
        throw new Error("Consent ID is required.");
      }
      if (!(file instanceof File) || file.size === 0) {
        throw new Error("Select an image file first.");
      }
      const payload = new FormData();
      payload.append("consent_id", consentId);
      payload.append("file", file);
      const upload = await request("/api/v1/uploads/file", { method: "POST", token, formData: payload });
      state.user.uploadId = upload.id;
      state.user.uploadStorageUri = upload.storage_uri;
      state.user.maskSaved = false;
      state.user.maskUri = "";
      if (maskSkipCheckboxEl) {
        maskSkipCheckboxEl.checked = false;
      }
      if (inpaintCheckboxEl) {
        inpaintCheckboxEl.checked = false;
      }
      updateMaskStatus();
      refreshMaskContinueState();
      state.user.pendingUploadFile = null;
      setUploadFileLabel("PNG, JPG, WEBP");
      setInputValue("generate-form", "upload_id", upload.id);
      setMeta("upload-meta", `upload_id=${upload.id}\nuri=${upload.storage_uri}`);
      refreshFlowProgress();
      initMaskEditor(upload.storage_uri, upload.id);
      setActiveClientStep("upload");
      showToast("Uploaded. Mark the scar area (recommended), then continue.", "info");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  preferenceForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("user");
      const form = new FormData(event.currentTarget);
      const payload = {
        style: String(form.get("style") || "").trim(),
        motifs: parseCsv(String(form.get("motifs") || "")),
        meaning_keywords: parseCsv(String(form.get("meaning_keywords") || "")),
        avoid_list: parseCsv(String(form.get("avoid_list") || "")),
        mood: String(form.get("mood") || "").trim() || null,
      };
      const pref = await request("/api/v1/preferences", { method: "POST", token, json: payload });
      state.user.preferenceId = pref.id;
      setInputValue("generate-form", "preference_id", pref.id);
      setMeta("preference-meta", `preference_id=${pref.id} (version ${pref.version})`);
      refreshFlowProgress();
      setActiveClientStep("generation");
      showToast("Preference saved.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  generateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("user");
      const form = new FormData(event.currentTarget);
      const inpaintOptIn = Boolean(inpaintCheckboxEl && inpaintCheckboxEl.checked);
      const payload = {
        upload_id: String(form.get("upload_id") || state.user.uploadId),
        preference_id: String(form.get("preference_id") || state.user.preferenceId),
        variant_count: Number(form.get("variant_count") || 1),
        preview_mode: inpaintOptIn ? "inpaint" : "overlay",
        send_image_to_provider: Boolean(inpaintOptIn),
      };
      if (!payload.upload_id || !payload.preference_id) {
        throw new Error("Upload ID and Preference ID are required.");
      }

      const skipMask = Boolean(maskSkipCheckboxEl && maskSkipCheckboxEl.checked);
      if (!state.user.maskSaved && !skipMask) {
        setActiveClientStep("upload");
        showToast("Please mark the scar area first (recommended), then generate.", "error");
        return;
      }
      if (inpaintOptIn && !state.user.maskSaved) {
        setActiveClientStep("upload");
        showToast("Photo-realistic preview requires a saved scar area mask.", "error");
        return;
      }

      setGenerating(true);
      generationController = new AbortController();
      generationStartedAt = Date.now();
      if (generationElapsedEl) {
        generationElapsedEl.textContent = "0s";
      }
      if (generationHintEl) {
        generationHintEl.textContent = "This can take 20 to 90 seconds. Please do not refresh or click repeatedly.";
      }
      window.clearInterval(generationTickTimerId);
      generationTickTimerId = window.setInterval(() => {
        const elapsed = (Date.now() - generationStartedAt) / 1000;
        if (generationElapsedEl) {
          generationElapsedEl.textContent = formatSeconds(elapsed);
        }
        if (generationHintEl && elapsed > 40) {
          generationHintEl.textContent = "Still working. If this feels slow, you can cancel and try again later.";
        }
      }, 1000);

      const generation = await requestWithTimeout("/api/v1/generations", {
        method: "POST",
        token,
        json: payload,
        timeoutMs: 130000,
        signal: generationController.signal,
      });
      state.user.generationId = generation.id;
      state.user.conceptIds = generation.concepts.map((item) => item.id);
      setInputValue("invite-form", "concept_ids", state.user.conceptIds.join(","));
      setMeta(
        "generation-meta",
        `generation_id=${generation.id}\nmodel=${generation.model_version}\nconcepts=${generation.concepts.length}`,
      );
      renderConcepts(generation.concepts);
      refreshFlowProgress();
      setActiveClientStep("generation");
      showToast("Concept generation completed.");
    } catch (error) {
      if (error && (error.name === "AbortError" || String(error.message || "").includes("AbortError"))) {
        showToast("Generation canceled.", "error");
      } else if (error && typeof error.message === "string" && error.message.includes("429 RATE_LIMITED")) {
        const retryAfter = error.details && Number(error.details.retry_after_seconds || 0);
        if (retryAfter > 0) {
          showToast(`Rate limited. Try again in ~${retryAfter}s.`, "error");
        } else {
          showToast("Rate limited. Please wait and try again.", "error");
        }
      } else if (error && typeof error.message === "string" && error.message.includes("503")) {
        showToast("Generation temporarily unavailable (503). Please wait and try again.", "error");
      } else if (error && typeof error.message === "string" && error.message.includes("502")) {
        showToast("Provider error (502). Please try again shortly.", "error");
      } else if (error && (error.name === "TypeError" || String(error.message || "").includes("Failed to fetch"))) {
        showToast("Network error. Please retry.", "error");
      } else {
        showToast(error.message, "error");
      }
    } finally {
      setGenerating(false);
      generationController = null;
      window.clearInterval(generationTickTimerId);
    }
  });

  function setGenerating(active) {
    if (generationLoadingEl) {
      generationLoadingEl.hidden = !active;
    }
    if (generateBtn) {
      generateBtn.disabled = Boolean(active);
      generateBtn.textContent = active ? "Generating..." : "Generate Concepts";
    }
    if (generationCancelBtn) {
      generationCancelBtn.disabled = !active;
    }
  }

  function initMaskEditor(imageUri, uploadId) {
    if (!maskEditorEl || !maskBaseImageEl || !maskCanvasEl || !maskBrushEl || !maskClearBtn || !maskSaveBtn) {
      return;
    }
    maskEditorEl.hidden = false;
    maskBaseImageEl.src = imageUri;

    const ctx = maskCanvasEl.getContext("2d");
    if (!ctx) {
      return;
    }
    let drawing = false;
    let last = null;

    function resizeCanvasToImage() {
      const rect = maskBaseImageEl.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(1, Math.round(rect.height));
      const prev = ctx.getImageData(0, 0, maskCanvasEl.width || 1, maskCanvasEl.height || 1);
      maskCanvasEl.width = width;
      maskCanvasEl.height = height;
      ctx.clearRect(0, 0, width, height);
      try {
        ctx.putImageData(prev, 0, 0);
      } catch {
        // ignore if previous canvas was empty or mismatched
      }
    }

    maskBaseImageEl.addEventListener("load", () => {
      resizeCanvasToImage();
      if (maskMetaEl) {
        maskMetaEl.textContent = "Draw on top of the photo to mark the scar area, then save.";
      }
    });
    window.addEventListener("resize", () => resizeCanvasToImage());

    function toLocalPoint(event) {
      const rect = maskCanvasEl.getBoundingClientRect();
      const clientX = event.touches && event.touches[0] ? event.touches[0].clientX : event.clientX;
      const clientY = event.touches && event.touches[0] ? event.touches[0].clientY : event.clientY;
      return {
        x: (clientX - rect.left) * (maskCanvasEl.width / rect.width),
        y: (clientY - rect.top) * (maskCanvasEl.height / rect.height),
      };
    }

    function stroke(from, to) {
      const brush = Number(maskBrushEl.value || 18);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "rgba(255, 80, 120, 0.55)";
      ctx.lineWidth = brush;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    }

    function onDown(event) {
      drawing = true;
      last = toLocalPoint(event);
      event.preventDefault();
    }
    function onMove(event) {
      if (!drawing || !last) {
        return;
      }
      const next = toLocalPoint(event);
      stroke(last, next);
      last = next;
      event.preventDefault();
    }
    function onUp(event) {
      drawing = false;
      last = null;
      event.preventDefault();
    }

    maskCanvasEl.onmousedown = onDown;
    maskCanvasEl.onmousemove = onMove;
    window.addEventListener("mouseup", onUp);
    maskCanvasEl.ontouchstart = onDown;
    maskCanvasEl.ontouchmove = onMove;
    maskCanvasEl.ontouchend = onUp;

    maskClearBtn.onclick = () => {
      ctx.clearRect(0, 0, maskCanvasEl.width, maskCanvasEl.height);
      if (maskMetaEl) {
        maskMetaEl.textContent = "Cleared. Draw again, then save.";
      }
    };

    maskSaveBtn.onclick = async () => {
      try {
        const token = requireToken("user");
        const blob = await new Promise((resolve) => maskCanvasEl.toBlob(resolve, "image/png"));
        if (!blob) {
          throw new Error("Unable to export mask.");
        }
        const fd = new FormData();
        fd.append("file", blob, "scar_mask.png");
        const result = await requestWithTimeout(`/api/v1/uploads/${uploadId}/mask`, {
          method: "POST",
          token,
          formData: fd,
          timeoutMs: 30000,
        });
        state.user.maskSaved = true;
        state.user.maskUri = String(result.storage_uri || "");
        updateMaskStatus();
        refreshMaskContinueState();
        if (maskMetaEl) {
          maskMetaEl.textContent = `Saved. mask_uri=${result.storage_uri}`;
        }
        showToast("Scar area saved.");
      } catch (error) {
        showToast(error.message, "error");
      }
    };
  }

  conceptGridEl && conceptGridEl.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }
    try {
      const token = requireToken("user");
      const conceptId = button.dataset.conceptId;
      const action = button.dataset.action;
      if (!conceptId) {
        return;
      }
      if (action === "view") {
        openConceptLightbox(state.user.conceptsById[conceptId]);
      } else if (action === "select") {
        await request(`/api/v1/concepts/${conceptId}/select`, { method: "POST", token });
        showToast(`Selected concept ${conceptId}.`);
      } else {
        const sentiment = action === "like" ? "like" : "dislike";
        await request(`/api/v1/concepts/${conceptId}/feedback`, {
          method: "POST",
          token,
          json: { sentiment, reason_tags: ["ui-feedback"] },
        });
        showToast(`${sentiment} feedback saved for ${conceptId}.`);
      }
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  inviteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("user");
      const form = new FormData(event.currentTarget);
      const artistActorId = String(form.get("artist_actor_id") || state.artist.actorId).trim();
      const conceptsRaw = String(form.get("concept_ids") || "");
      const conceptIds = parseCsv(conceptsRaw).length ? parseCsv(conceptsRaw) : state.user.conceptIds;
      if (!artistActorId) {
        throw new Error("Artist actor ID is required.");
      }
      if (!conceptIds.length) {
        throw new Error("Provide at least one concept ID.");
      }
      const collaboration = await request("/api/v1/collaborations/invite", {
        method: "POST",
        token,
        json: { artist_actor_id: artistActorId, concept_ids: conceptIds },
      });
      state.user.collaborationId = collaboration.id;
      state.user.collaborationStatus = collaboration.status;
      state.artist.collaborationId = collaboration.id;
      setInputValue("artist-collab-form", "collaboration_id", collaboration.id);
      setInputValue("artist-note-form", "collaboration_id", collaboration.id);
      setMeta("invite-meta", `collaboration_id=${collaboration.id}\nstatus=${collaboration.status}`);
      refreshFlowProgress();
      setActiveClientStep("collaboration");
      showToast("Artist invited.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  revokeBtn.addEventListener("click", async () => {
    try {
      const token = requireToken("user");
      const collaborationId = state.user.collaborationId;
      if (!collaborationId) {
        throw new Error("No collaboration to revoke.");
      }
      const updated = await request(`/api/v1/collaborations/${collaborationId}/revoke`, {
        method: "POST",
        token,
      });
      state.user.collaborationStatus = updated.status;
      setMeta("invite-meta", `collaboration_id=${updated.id}\nstatus=${updated.status}`);
      refreshFlowProgress();
      showToast("Collaboration revoked.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

function setupArtistFlow() {
  const artistSessionBtn = document.getElementById("artist-session-btn");
  const artistCollabForm = document.getElementById("artist-collab-form");
  const artistNoteForm = document.getElementById("artist-note-form");
  const artistListNotesBtn = document.getElementById("artist-list-notes-btn");
  if (!artistSessionBtn || !artistCollabForm || !artistNoteForm || !artistListNotesBtn) {
    return;
  }

  artistSessionBtn.addEventListener("click", async () => {
    try {
      const session = await createSession("artist");
      state.artist.token = session.token;
      state.artist.actorId = session.actor_id;
      setInputValue("invite-form", "artist_actor_id", session.actor_id);
      setMeta("artist-session-meta", `actor_id=${session.actor_id}`);
      setActiveArtistStep("collaboration");
      showToast("Artist session created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  artistCollabForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("artist");
      const form = new FormData(event.currentTarget);
      const collaborationId = String(form.get("collaboration_id") || state.artist.collaborationId).trim();
      if (!collaborationId) {
        throw new Error("Collaboration ID is required.");
      }
      const collaboration = await request(`/api/v1/collaborations/${collaborationId}`, { token });
      state.artist.collaborationId = collaboration.id;
      setInputValue("artist-note-form", "collaboration_id", collaboration.id);
      setMeta(
        "artist-collab-meta",
        `status=${collaboration.status}\nconcept_ids=${collaboration.concept_ids.join(", ") || "-"}`,
      );
      setActiveArtistStep("notes");
      showToast("Collaboration loaded.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  artistNoteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("artist");
      const form = new FormData(event.currentTarget);
      const collaborationId = String(form.get("collaboration_id") || state.artist.collaborationId).trim();
      if (!collaborationId) {
        throw new Error("Collaboration ID is required.");
      }
      const conceptId = String(form.get("concept_id") || "").trim();
      const noteText = String(form.get("note_text") || "").trim();
      if (!noteText) {
        throw new Error("Note cannot be empty.");
      }
      await request(`/api/v1/collaborations/${collaborationId}/notes`, {
        method: "POST",
        token,
        json: {
          concept_id: conceptId || null,
          note_text: noteText,
        },
      });
      showToast("Artist note added.");
      const notes = await request(`/api/v1/collaborations/${collaborationId}/notes`, { token });
      renderNotes(notes);
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  artistListNotesBtn.addEventListener("click", async () => {
    try {
      const token = requireToken("artist");
      const collaborationId = state.artist.collaborationId;
      if (!collaborationId) {
        throw new Error("Load a collaboration first.");
      }
      const notes = await request(`/api/v1/collaborations/${collaborationId}/notes`, { token });
      renderNotes(notes);
      showToast("Notes refreshed.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

function setupAdminFlow() {
  const adminSessionBtn = document.getElementById("admin-session-btn");
  const adminToggleForm = document.getElementById("admin-toggle-form");
  const adminMetricsBtn = document.getElementById("admin-metrics-btn");
  if (!adminSessionBtn || !adminToggleForm || !adminMetricsBtn) {
    return;
  }

  adminSessionBtn.addEventListener("click", async () => {
    try {
      const session = await createSession("admin");
      state.admin.token = session.token;
      state.admin.actorId = session.actor_id;
      setMeta("admin-session-meta", `actor_id=${session.actor_id}`);
      setActiveAdminStep("controls");
      showToast("Admin session created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  adminToggleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const token = requireToken("admin");
      const form = new FormData(event.currentTarget);
      const disabled = Boolean(form.get("disabled"));
      const metrics = await request("/api/v1/admin/generation/disable", {
        method: "POST",
        token,
        json: { disabled, reason: "toggled from console" },
      });
      document.getElementById("admin-metrics").textContent = JSON.stringify(metrics, null, 2);
      setActiveAdminStep("metrics");
      showToast(`Generation ${disabled ? "disabled" : "enabled"}.`);
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  adminMetricsBtn.addEventListener("click", async () => {
    try {
      const token = requireToken("admin");
      const metrics = await request("/api/v1/admin/metrics", { token });
      document.getElementById("admin-metrics").textContent = JSON.stringify(metrics, null, 2);
      setActiveAdminStep("metrics");
      showToast("Metrics refreshed.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

function setupHeroActions() {
  const openStudioBtn = document.getElementById("open-studio-btn");
  if (openStudioBtn) {
    openStudioBtn.addEventListener("click", () => {
      window.location.href = "/ui/client.html";
    });
  }

  const runSandboxBtn = document.getElementById("run-sandbox-btn");
  if (runSandboxBtn) {
    runSandboxBtn.addEventListener("click", async () => {
      const hasUserFlow = Boolean(document.getElementById("user-session-btn"));
      if (!hasUserFlow) {
        window.location.href = "/ui/client.html?sandbox=1";
        return;
      }
      await runOnboardingSandbox();
    });
  }
}

async function runOnboardingSandbox() {
  const button = document.getElementById("run-sandbox-btn");
  button.disabled = true;
  appendJourney("Starting onboarding sandbox flow.");
  try {
    setActivePanel("user-panel");

    appendJourney("Creating user session.");
    const userSession = await createSession("user");
    state.user.token = userSession.token;
    state.user.actorId = userSession.actor_id;
    setMeta("user-session-meta", `actor_id=${userSession.actor_id}`);

    appendJourney("Recording consent.");
    const consent = await request("/api/v1/consents", {
      method: "POST",
      token: state.user.token,
      json: { policy_version: "consent-v1", disclaimer_accepted: true },
    });
    state.user.consentId = consent.id;
    setInputValue("upload-form", "consent_id", consent.id);
    setMeta("consent-meta", `consent_id=${consent.id}`);

    appendJourney("Creating privacy-safe synthetic test image.");
    const demoFile = await buildSyntheticScarFile();
    const uploadData = new FormData();
    uploadData.append("consent_id", consent.id);
    uploadData.append("file", demoFile);

    appendJourney("Uploading synthetic image.");
    const upload = await request("/api/v1/uploads/file", {
      method: "POST",
      token: state.user.token,
      formData: uploadData,
    });
    state.user.uploadId = upload.id;
    setInputValue("generate-form", "upload_id", upload.id);
    setMeta("upload-meta", `upload_id=${upload.id}\nuri=${upload.storage_uri}`);

    appendJourney("Saving preference profile.");
    const preference = await request("/api/v1/preferences", {
      method: "POST",
      token: state.user.token,
      json: {
        style: "floral linework",
        motifs: ["lotus", "contour", "wind"],
        meaning_keywords: ["rebirth", "strength", "calm"],
        avoid_list: ["weapons", "gore"],
        mood: "gentle",
      },
    });
    state.user.preferenceId = preference.id;
    setInputValue("generate-form", "preference_id", preference.id);
    setMeta("preference-meta", `preference_id=${preference.id} (version ${preference.version})`);

    appendJourney("Generating scar-aware concepts.");
    const generation = await request("/api/v1/generations", {
      method: "POST",
      token: state.user.token,
      json: {
        upload_id: upload.id,
        preference_id: preference.id,
        variant_count: 1,
      },
    });
    state.user.generationId = generation.id;
    state.user.conceptIds = generation.concepts.map((item) => item.id);
    setInputValue("invite-form", "concept_ids", state.user.conceptIds.join(","));
    setMeta(
      "generation-meta",
      `generation_id=${generation.id}\nmodel=${generation.model_version}\nconcepts=${generation.concepts.length}`,
    );
    renderConcepts(generation.concepts);
    refreshFlowProgress();

    appendJourney("Creating artist session and sharing concepts.");
    const artistSession = await createSession("artist");
    state.artist.token = artistSession.token;
    state.artist.actorId = artistSession.actor_id;
    setInputValue("invite-form", "artist_actor_id", artistSession.actor_id);
    setMeta("artist-session-meta", `actor_id=${artistSession.actor_id}`);

    const collaboration = await request("/api/v1/collaborations/invite", {
      method: "POST",
      token: state.user.token,
      json: {
        artist_actor_id: artistSession.actor_id,
        concept_ids: state.user.conceptIds,
      },
    });
    state.user.collaborationId = collaboration.id;
    state.user.collaborationStatus = collaboration.status;
    state.artist.collaborationId = collaboration.id;
    setInputValue("artist-collab-form", "collaboration_id", collaboration.id);
    setInputValue("artist-note-form", "collaboration_id", collaboration.id);
    setMeta("invite-meta", `collaboration_id=${collaboration.id}\nstatus=${collaboration.status}`);
    refreshFlowProgress();

    await request(`/api/v1/collaborations/${collaboration.id}/notes`, {
      method: "POST",
      token: state.artist.token,
      json: {
        concept_id: state.user.conceptIds[0] || null,
        note_text: "Favor lighter line density at scar edge, keep open space for skin breathing.",
      },
    });
    const notes = await request(`/api/v1/collaborations/${collaboration.id}/notes`, { token: state.artist.token });
    renderNotes(notes);
    appendJourney("Artist feedback added.");

    appendJourney("Creating admin session and loading reliability metrics.");
    const adminSession = await createSession("admin");
    state.admin.token = adminSession.token;
    state.admin.actorId = adminSession.actor_id;
    setMeta("admin-session-meta", `actor_id=${adminSession.actor_id}`);
    const metrics = await request("/api/v1/admin/metrics", { token: state.admin.token });
    document.getElementById("admin-metrics").textContent = JSON.stringify(metrics, null, 2);

    appendJourney("Onboarding sandbox flow completed.");
    showToast("Onboarding sandbox completed.");
    await refreshHealthStatus();
  } catch (error) {
    appendJourney(`Onboarding sandbox failed: ${error.message}`);
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

function init() {
  setupTabs();
  setupClientStepper();
  setupArtistStepper();
  setupAdminStepper();
  setupConceptLightbox();
  setupUploadDropzone();
  setupPreferenceAssist();
  setupUserFlow();
  setupArtistFlow();
  setupAdminFlow();
  setupHeroActions();
  refreshHealthStatus();
  refreshFlowProgress();

  const params = new URLSearchParams(window.location.search);
  if (params.get("sandbox") === "1" && document.getElementById("user-session-btn")) {
    runOnboardingSandbox();
  }
}

init();
