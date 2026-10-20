const agentSelect = document.querySelector("#agent-select");
const modeSelect = document.querySelector("#mode-select");
const taskInput = document.querySelector("#task-input");
const submitButton = document.querySelector("#submit-task");
const projectList = document.querySelector("#project-list");
const projectCardList = document.querySelector("#project-card-list");
const activityBody = document.querySelector("#activity-body");
const activityTitle = document.querySelector("#activity-title");
const activityIndicator = document.querySelector("#activity-indicator");
const chatSessionList = document.querySelector("#chat-session-list");
const addChatSessionButton = document.querySelector("#add-chat-session");
const chatSessionCount = document.querySelector("#chat-session-count");
const toast = document.querySelector("#toast");
const agentsDialog = document.querySelector("#agents-dialog");
const agentChoiceList = document.querySelector("#agent-choice-list");
const agentSearch = document.querySelector("#agent-search");
const skillsDialog = document.querySelector("#skills-dialog");
const skillChoiceList = document.querySelector("#skill-choice-list");
const skillBrowser = document.querySelector("#skills-browser");
const skillCreateForm = document.querySelector("#skill-create-form");
const skillTopic = document.querySelector("#skill-topic");
const skillPreviewTitle = document.querySelector("#skill-preview-title");
const skillPreviewDescription = document.querySelector("#skill-preview-description");
const skillContent = document.querySelector("#skill-content code");
const settingsDialog = document.querySelector("#settings-dialog");
const settingsForm = document.querySelector("#environment-settings-form");
const settingsStatus = document.querySelector("#settings-status");

let apps = [];
let agents = [];
let skills = [];
let toastTimer;
let skillGenerating = false;
const chatSessionStorageKey = "dev-agent-chat-sessions";
const maxChatSessions = 5;
const taskSessionIds = Array.from(
    { length: maxChatSessions },
    (_, index) => `session-${String(index + 1).padStart(2, "0")}`,
);

try {
    localStorage.removeItem("dev-agent-google-api-key");
} catch (error) {
    showToast("Could not remove the old browser-stored Google API key.", true);
}

function createChatSession(id) {
    return {
        id,
        entries: [],
        running: false,
        status: "idle",
        pendingTask: "",
        initialUserLogHidden: false,
        stream: null,
    };
}

function loadChatSessions() {
    const firstSessionId = taskSessionIds[0];
    try {
        const stored = JSON.parse(localStorage.getItem(chatSessionStorageKey) || "{}");
        if (!Array.isArray(stored.sessionIds)) {
            return { sessions: [createChatSession(firstSessionId)], activeSessionId: firstSessionId };
        }

        const ids = [firstSessionId];
        const migratedIds = new Map([[firstSessionId, firstSessionId]]);
        for (const previousId of stored.sessionIds) {
            if (typeof previousId !== "string" || migratedIds.has(previousId)) continue;
            let id = taskSessionIds.includes(previousId) ? previousId : null;
            if (!id && previousId.startsWith("chat-")) {
                id = taskSessionIds.find((candidate) => !ids.includes(candidate));
            }
            if (!id || ids.includes(id) || ids.length >= maxChatSessions) continue;
            ids.push(id);
            migratedIds.set(previousId, id);
        }
        const sessions = ids.map(createChatSession);
        const activeSessionId = migratedIds.get(stored.activeSessionId) || firstSessionId;
        return { sessions, activeSessionId };
    } catch (error) {
        showToast("Could not load saved chat sessions. Starting a new session.", true);
        return { sessions: [createChatSession(firstSessionId)], activeSessionId: firstSessionId };
    }
}

const savedChatSessions = loadChatSessions();
let chatSessions = savedChatSessions.sessions;
let activeChatSession = chatSessions.find((session) => session.id === savedChatSessions.activeSessionId)
    || chatSessions[0];

async function api(url, options = {}) {
    const { headers: suppliedHeaders = {}, ...requestOptions } = options;
    const headers = { "Content-Type": "application/json", ...suppliedHeaders };
    const response = await fetch(url, {
        ...requestOptions,
        headers,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const error = new Error(data.error || data.detail || `Request failed (${response.status}).`);
        error.status = response.status;
        error.fieldErrors = data.field_errors || {};
        throw error;
    }
    return data;
}

function updateEnvironmentSettingsStatus(settings) {
    environmentSettingsState = settings;
    settingsRequired = !settings.file_has_data;
    document.querySelector("#close-settings").disabled = settingsRequired;
    for (const row of settingsForm.querySelectorAll("[data-setting-row]")) {
        const name = row.dataset.settingRow;
        const status = settings[name];
        row.querySelector("[data-setting-status]").textContent = status.saved
            ? status.valid
                ? "Saved in /data/env.txt"
                : "Saved value is invalid"
            : status.configured
                ? "Using server environment"
                : "Not configured";
        row.querySelector("[data-clear-setting]").disabled = !status.saved;
    }
}

let environmentSettingsState = {};
let settingsRequired = false;
let settingsValidationAttempted = false;

function validateSetting(name, value) {
    if (!value) {
        const savedStatus = environmentSettingsState[name];
        return savedStatus?.saved && savedStatus.valid
            ? ""
            : "This setting is required.";
    }
    if (value.length > (name === "GOOGLE_API_KEY" ? 512 : 4096)) {
        return "Value is too long.";
    }
    if (/[\r\n]/.test(value)) {
        return "Line breaks are not allowed.";
    }
    if (name === "URI" && !/^mongodb(?:\+srv)?:\/\/[^/\s?#]+(?:[/?#][^\s]*)?$/.test(value)) {
        return "Enter a valid MongoDB URI starting with mongodb:// or mongodb+srv://.";
    }
    if (name === "DB_NAME" && (value.length > 63 || /[\/\\."$*<>:|?\0]/.test(value))) {
        return "Enter a valid MongoDB database name (1–63 characters, without reserved characters).";
    }
    if (name === "COLLECTION_NAME" && (value.length > 120 || value.startsWith("system."))) {
        return "Enter a valid MongoDB collection name (up to 120 characters).";
    }
    return "";
}

function validateSettingsForm() {
    let isValid = true;
    for (const input of settingsForm.querySelectorAll("[data-setting-name]")) {
        const name = input.dataset.settingName;
        const error = validateSetting(name, input.value.trim());
        const row = input.closest("[data-setting-row]");
        const status = row.querySelector("[data-setting-status]");
        input.classList.toggle("is-invalid", Boolean(error));
        input.setAttribute("aria-invalid", String(Boolean(error)));
        row.classList.toggle("has-error", Boolean(error));
        if (error) {
            status.textContent = error;
            isValid = false;
        } else {
            const savedStatus = environmentSettingsState[name];
            status.textContent = savedStatus?.saved
                ? savedStatus.valid
                    ? "Saved in /data/env.txt"
                    : "Saved value is invalid"
                : savedStatus?.configured
                    ? "Using server environment"
                    : "Not configured";
        }
    }
    return isValid;
}

async function openSettingsDialog(initialStatus = null) {
    for (const input of settingsForm.querySelectorAll("[data-setting-name]")) {
        input.value = "";
        input.classList.remove("is-invalid");
        input.removeAttribute("aria-invalid");
    }
    settingsValidationAttempted = false;
    settingsRequired = false;
    document.querySelector("#close-settings").disabled = settingsRequired;
    settingsStatus.textContent = "Checking server settings…";
    settingsDialog.showModal();
    settingsForm.querySelector("[data-setting-name]").focus();
    try {
        updateEnvironmentSettingsStatus(
            initialStatus || await api("/api/settings/environment"),
        );
        settingsStatus.textContent = settingsRequired
            ? "Enter your configuration before continuing."
            : "";
        if (settingsValidationAttempted) validateSettingsForm();
    } catch (error) {
        settingsRequired = false;
        document.querySelector("#close-settings").disabled = false;
        settingsStatus.textContent = "Could not load server settings.";
        showToast(error.message, true);
    }
}

async function requireEnvironmentSettings() {
    try {
        const settings = await api("/api/settings/environment");
        updateEnvironmentSettingsStatus(settings);
        if (settingsRequired) await openSettingsDialog(settings);
    } catch (error) {
        showToast(error.message, true);
    }
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function updateSubmitState() {
    submitButton.disabled = activeChatSession.running || !taskInput.value.trim();
    document.querySelector("#submit-label").textContent = activeChatSession.running ? "Sending…" : "Send";
    document.querySelector("#char-count").textContent = `${taskInput.value.length.toLocaleString()} / 10,000`;
    document.querySelector("#agent-picker").hidden = modeSelect.value !== "individual";
}

function saveChatSessions() {
    try {
        localStorage.setItem(chatSessionStorageKey, JSON.stringify({
            sessionIds: chatSessions.map((session) => session.id),
            activeSessionId: activeChatSession.id,
        }));
    } catch (error) {
        showToast("Could not save chat sessions in this browser.", true);
    }
}

function renderChatSessions() {
    chatSessionList.replaceChildren();
    chatSessions.forEach((session) => {
        const sessionNumber = Number(session.id.slice(-2));
        const tab = document.createElement("div");
        tab.className = "chat-session-tab";
        tab.classList.toggle("is-active", session === activeChatSession);
        const button = document.createElement("button");
        button.className = "chat-session-button";
        button.type = "button";
        button.setAttribute("aria-pressed", String(session === activeChatSession));
        button.textContent = `Session ${sessionNumber}${session.running ? " ·" : ""}`;
        button.title = session.running
            ? `Session ${sessionNumber} is working`
            : `Switch to session ${sessionNumber}`;
        button.addEventListener("click", () => selectChatSession(session));
        tab.append(button);
        if (session.id !== taskSessionIds[0]) {
            const closeButton = document.createElement("button");
            closeButton.className = "chat-session-close";
            closeButton.type = "button";
            closeButton.textContent = "×";
            closeButton.setAttribute("aria-label", `Close session ${sessionNumber}`);
            closeButton.title = session.running
                ? "Wait for this session to finish before closing it"
                : `Close session ${sessionNumber}`;
            closeButton.disabled = session.running;
            closeButton.addEventListener("click", () => closeChatSession(session));
            tab.append(closeButton);
        }
        chatSessionList.append(tab);
    });
    addChatSessionButton.disabled = chatSessions.length >= maxChatSessions;
    addChatSessionButton.title = addChatSessionButton.disabled
        ? "Maximum of 5 chat sessions reached"
        : `Create a new chat session (${chatSessions.length}/${maxChatSessions})`;
    addChatSessionButton.setAttribute(
        "aria-label",
        addChatSessionButton.disabled
            ? "Maximum of 5 chat sessions reached"
            : "Create new chat session",
    );
    chatSessionCount.textContent = `${chatSessions.length} of ${maxChatSessions} chat sessions`;
}

function renderActivityIndicator() {
    const labels = {
        idle: "IDLE",
        running: "RUNNING",
        done: "COMPLETE",
        error: "ERROR",
    };
    const status = activeChatSession.status;
    activityIndicator.className = `activity-indicator${status === "running" || status === "done" ? ` ${status}` : ""}`;
    activityIndicator.replaceChildren(
        document.createElement("span"),
        document.createTextNode(labels[status]),
    );
    activityTitle.textContent = {
        idle: "Chat with Dev Agent",
        running: "Your agent is at work",
        done: "Build complete",
        error: "Build needs attention",
    }[status];
}

function renderActiveChatSession() {
    activityBody.replaceChildren();
    renderActivityIndicator();
    if (!activeChatSession.entries.length) {
        const empty = document.createElement("div");
        empty.className = "activity-empty";
        const glyph = document.createElement("span");
        glyph.className = "empty-glyph";
        glyph.setAttribute("aria-hidden", "true");
        glyph.textContent = "⌁";
        const message = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = "Your conversation starts here";
        const description = document.createElement("p");
        description.textContent = "Describe what you want to build. Your agent’s replies and progress will appear here.";
        message.append(title, description);
        empty.append(glyph, message);
        activityBody.append(empty);
        return;
    }

    const log = document.createElement("div");
    log.className = "activity-log";
    log.setAttribute("role", "log");
    log.setAttribute("aria-live", "polite");
    for (const entry of activeChatSession.entries) {
        if (entry.role === "Approval") {
            log.append(renderCodeApproval(entry, activeChatSession));
            continue;
        }
        const line = document.createElement("div");
        line.className = "activity-log-entry";
        const roleName = entry.role.toLowerCase().replace(/[^a-z0-9_-]/g, "");
        line.classList.add(`role-${roleName || "system"}`);
        const role = document.createElement("span");
        role.className = "activity-log-role";
        role.textContent = entry.role;
        const content = document.createElement("div");
        content.className = "activity-log-content";
        content.textContent = entry.content;
        line.append(role, content);
        log.append(line);
    }
    activityBody.append(log);
    activityBody.scrollTop = activityBody.scrollHeight;
}

function selectChatSession(session) {
    activeChatSession = session;
    renderChatSessions();
    renderActiveChatSession();
    updateSubmitState();
    saveChatSessions();
}

function closeChatSession(session) {
    if (session.id === taskSessionIds[0] || session.running) return;
    const index = chatSessions.indexOf(session);
    if (index < 0) return;
    session.stream?.close();
    chatSessions.splice(index, 1);
    if (activeChatSession === session) {
        activeChatSession = chatSessions[Math.min(index, chatSessions.length - 1)];
    }
    renderChatSessions();
    renderActiveChatSession();
    updateSubmitState();
    saveChatSessions();
}

function addChatSession() {
    if (chatSessions.length >= maxChatSessions) return;
    const id = taskSessionIds.find((candidate) => !chatSessions.some((session) => session.id === candidate));
    if (!id) return;
    const session = createChatSession(id);
    chatSessions.push(session);
    selectChatSession(session);
    connectTaskLogStream(session);
    taskInput.focus();
}

function openAgentDialogFromQuery() {
    const view = new URLSearchParams(window.location.search).get("view");
    if (view === "agents") {
        renderAgentChoices(agentSearch.value);
        agentsDialog.showModal();
        agentSearch.focus();
    } else if (view === "skills") {
        openSkillsDialog();
    }
}

function selectApp(appName) {
    if (appName === "None") return;
    window.location.assign(`/projects/${encodeURIComponent(appName)}`);
}

async function loadAgents() {
    try {
        agents = await api("/api/agents");
        agentSelect.replaceChildren();
        if (agents.length === 0) {
            agentSelect.add(new Option("Let Dev Agent decide", ""));
            document.querySelector("#agent-count").textContent = "0";
            renderAgentChoices();
            updateSubmitState();
            openAgentDialogFromQuery();
            return;
        }
        agentSelect.add(new Option("Let Dev Agent decide", ""));
        for (const agent of agents) {
            const option = new Option(agent.name || "Unnamed agent", agent.name);
            option.title = agent.action || "";
            agentSelect.add(option);
        }
        document.querySelector("#agent-count").textContent = String(agents.length);
        renderAgentChoices();
        openAgentDialogFromQuery();
    } catch (error) {
        agents = [];
        agentSelect.replaceChildren(new Option("Could not load agents", ""));
        renderAgentChoices();
        showToast(error.message, true);
        openAgentDialogFromQuery();
    }
    updateSubmitState();
}

function renderAgentChoices(search = "") {
    agentChoiceList.replaceChildren();
    const query = search.trim().toLowerCase();
    const matchingAgents = agents.filter((agent) => (
        `${agent.name || ""} ${agent.action || ""}`.toLowerCase().includes(query)
    ));

    if (!matchingAgents.length) {
        const empty = document.createElement("div");
        empty.className = "tree-empty";
        empty.textContent = agents.length ? "No agents match that search." : "No agents are available yet.";
        agentChoiceList.append(empty);
        return;
    }

    for (const agent of matchingAgents) {
        const choice = document.createElement("button");
        choice.className = "agent-choice";
        choice.type = "button";
        choice.setAttribute("role", "option");
        choice.setAttribute("aria-selected", String(agentSelect.value === agent.name));

        const icon = document.createElement("span");
        icon.className = "agent-choice-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = "◈";
        const details = document.createElement("span");
        details.className = "agent-choice-details";
        const name = document.createElement("strong");
        name.textContent = agent.name || "Unnamed agent";
        const action = document.createElement("span");
        action.className = "agent-choice-description";
        action.textContent = agent.action || "No role description provided.";
        details.append(name, action);
        const status = document.createElement("span");
        status.className = `agent-choice-status ${agent.status === "active" ? "is-active" : ""}`;
        status.textContent = agent.status || "inactive";
        choice.append(icon, details, status);
        choice.addEventListener("click", () => chooseAgent(agent.name));
        agentChoiceList.append(choice);
    }
}

function buildSkillTree(skillFiles) {
    const root = { children: new Map() };
    for (const skill of skillFiles) {
        const parts = skill.filename.split("/");
        let current = root;
        for (let index = 0; index < parts.length; index += 1) {
            const name = parts[index];
            const isFile = index === parts.length - 1;
            if (!current.children.has(name)) {
                current.children.set(name, {
                    name,
                    type: isFile ? "file" : "directory",
                    children: new Map(),
                    skill: isFile ? skill : null,
                });
            }
            current = current.children.get(name);
        }
    }

    function toArray(node) {
        return [...node.children.values()]
            .sort((left, right) => (
                Number(left.type !== "directory") - Number(right.type !== "directory")
                || left.name.localeCompare(right.name, undefined, { sensitivity: "base" })
            ))
            .map((child) => ({
                ...child,
                children: toArray(child),
            }));
    }

    return toArray(root);
}

function renderSkillChoices() {
    skillChoiceList.replaceChildren();
    document.querySelector("#skill-file-count").textContent = `${skills.length} ${skills.length === 1 ? "skill" : "skills"}`;

    if (!skills.length) {
        const empty = document.createElement("div");
        empty.className = "tree-empty";
        empty.textContent = "No Markdown skills were found in skills/.";
        skillChoiceList.append(empty);
        return;
    }

    skillChoiceList.append(makeSkillTreeList(buildSkillTree(skills)));
}

function makeSkillTreeList(nodes, depth = 0) {
    const list = document.createElement("ul");
    list.className = depth ? "tree-list nested" : "tree-list";
    list.setAttribute("role", "group");
    for (const node of nodes) {
        const entry = document.createElement("li");
        entry.className = "tree-entry";
        entry.setAttribute("role", "treeitem");
        const button = document.createElement("button");
        button.className = `tree-item${node.skill?.filename === selectedSkill ? " selected" : ""}`;
        button.type = "button";
        const caret = document.createElement("span");
        caret.className = "tree-caret";
        caret.setAttribute("aria-hidden", "true");
        caret.textContent = node.type === "directory" ? "▾" : "";
        const icon = document.createElement("span");
        icon.className = `tree-icon${node.type === "file" ? " file" : ""}`;
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = node.type === "directory" ? "▰" : "◇";
        const name = document.createElement("span");
        name.className = "tree-name";
        name.textContent = node.name;
        button.append(caret, icon, name);
        entry.append(button);

        if (node.type === "directory") {
            const children = makeSkillTreeList(node.children, depth + 1);
            entry.append(children);
            button.setAttribute("aria-expanded", "true");
            button.setAttribute("aria-label", `Collapse ${node.name}`);
            button.addEventListener("click", () => {
                const expanded = button.getAttribute("aria-expanded") === "true";
                button.setAttribute("aria-expanded", String(!expanded));
                button.setAttribute("aria-label", `${expanded ? "Expand" : "Collapse"} ${node.name}`);
                children.hidden = expanded;
                caret.textContent = expanded ? "▸" : "▾";
            });
        } else {
            button.setAttribute("aria-selected", String(node.skill.filename === selectedSkill));
            button.addEventListener("click", () => selectSkill(node.skill));
        }
        list.append(entry);
    }
    return list;
}

let selectedSkill = "";

function selectSkill(skill) {
    selectedSkill = skill.filename;
    skillPreviewTitle.textContent = skill.path || skill.filename;
    skillPreviewDescription.textContent = skill.description;
    skillContent.textContent = skill.content;
    renderSkillChoices();
}

async function loadSkills() {
    try {
        skills = await api("/api/skills");
        document.querySelector("#skill-count").textContent = String(skills.length);
        renderSkillChoices();
        const selected = skills.find((skill) => skill.filename === selectedSkill);
        if (selected) {
            selectSkill(selected);
        } else if (skills.length) {
            selectSkill(skills[0]);
        } else {
            selectedSkill = "";
            skillPreviewTitle.textContent = "No skills yet";
            skillPreviewDescription.textContent = "Add a skill to give your agents reusable instructions.";
            skillContent.textContent = "";
        }
    } catch (error) {
        skills = [];
        document.querySelector("#skill-count").textContent = "!";
        renderSkillChoices();
        showToast(error.message, true);
    }
}

function openSkillsDialog() {
    skillsDialog.showModal();
    skillBrowser.hidden = false;
    skillCreateForm.hidden = true;
    loadSkills();
}

function chooseAgent(name) {
    agentSelect.value = name;
    modeSelect.value = "individual";
    updateSubmitState();
    agentsDialog.close();
    showToast(`${name} selected for Individual mode.`);
    document.querySelector("#task-input").focus();
}

function renderProjects() {
    projectList.replaceChildren();
    projectCardList.replaceChildren();
    if (!apps.length) {
        const sidebarEmpty = document.createElement("div");
        sidebarEmpty.className = "sidebar-loading";
        sidebarEmpty.textContent = "Your generated apps will appear here.";
        projectList.append(sidebarEmpty);
        const cardEmpty = document.createElement("div");
        cardEmpty.className = "project-hub-empty";
        cardEmpty.textContent = "Build your first app and it will show up here.";
        projectCardList.append(cardEmpty);
        return;
    }

    for (const app of apps) {
        const href = `/projects/${encodeURIComponent(app.name)}`;
        const button = document.createElement("a");
        button.className = "project-link";
        button.href = href;
        const glyph = document.createElement("span");
        glyph.className = "project-glyph";
        glyph.setAttribute("aria-hidden", "true");
        glyph.textContent = "◧";
        const name = document.createElement("span");
        name.className = "project-title";
        name.textContent = app.name;
        button.append(glyph, name);
        projectList.append(button);

        const card = document.createElement("a");
        card.className = "project-card";
        card.href = href;
        const cardGlyph = document.createElement("span");
        cardGlyph.className = "project-card-glyph";
        cardGlyph.setAttribute("aria-hidden", "true");
        cardGlyph.textContent = "▣";
        const cardInfo = document.createElement("span");
        cardInfo.className = "project-card-info";
        const cardName = document.createElement("strong");
        cardName.textContent = app.name;
        const cardFiles = document.createElement("span");
        cardFiles.textContent = `${(app.files || []).length} files · Open workspace`;
        cardInfo.append(cardName, cardFiles);
        const arrow = document.createElement("span");
        arrow.className = "project-card-arrow";
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "↗";
        card.append(cardGlyph, cardInfo, arrow);
        projectCardList.append(card);
    }
}

async function loadApps(preferredApp = "") {
    try {
        apps = await api("/api/apps");
        renderProjects();
        if (preferredApp) selectApp(preferredApp);
    } catch (error) {
        showToast(error.message, true);
    }
}

function appendActivityLog(entry, session = activeChatSession) {
    if (
        !entry
        || typeof entry.role !== "string"
        || typeof entry.content !== "string"
    ) {
        showToast("Received an invalid build log entry.", true);
        return;
    }
    if (
        entry.role === "User"
        && entry.content === session.pendingTask
        && !session.initialUserLogHidden
    ) {
        session.initialUserLogHidden = true;
        return;
    }

    if (entry.role === "Approval") {
        const approval = JSON.parse(entry.content);
        if (
            !approval
            || typeof approval.approval_id !== "string"
            || typeof approval.file_name !== "string"
            || typeof approval.original_code !== "string"
            || typeof approval.proposed_code !== "string"
        ) {
            throw new Error("Received an invalid code review request.");
        }
        session.entries.push({
            role: entry.role,
            approval,
            decision: null,
            saved: false,
            completed: false,
            submitting: false,
        });
        if (session === activeChatSession) renderActiveChatSession();
        return;
    }
    if (entry.role === "ApprovalResult") {
        const result = JSON.parse(entry.content);
        if (
            !result
            || typeof result.approval_id !== "string"
            || typeof result.approved !== "boolean"
            || typeof result.saved !== "boolean"
        ) {
            throw new Error("Received an invalid code review result.");
        }
        const approvalEntry = session.entries.find(
            (item) => item.role === "Approval" && item.approval.approval_id === result.approval_id,
        );
        if (approvalEntry) {
            approvalEntry.decision = result.approved;
            approvalEntry.saved = result.saved;
            approvalEntry.completed = true;
        }
        if (session === activeChatSession) renderActiveChatSession();
        return;
    }

    session.entries.push({ role: entry.role, content: entry.content });
    if (entry.role === "System") {
        if (entry.content === "Task started") session.status = "running";
        if (entry.content === "Task complete") session.status = "done";
        if (entry.content === "Task failed") session.status = "error";
    }
    if (session === activeChatSession) renderActiveChatSession();
}

function renderCodeApproval(entry, session) {
    const card = document.createElement("section");
    card.className = "activity-log-entry role-approval";
    const role = document.createElement("span");
    role.className = "activity-log-role";
    role.textContent = "REVIEW CODE CHANGE";
    const filename = document.createElement("strong");
    filename.className = "approval-filename";
    filename.textContent = entry.approval.file_name;
    const instructions = document.createElement("p");
    instructions.className = "approval-description";
    instructions.textContent = "Review the proposed file contents. The agent will not save this change until you approve it.";

    const proposedDetails = document.createElement("details");
    proposedDetails.className = "approval-code";
    proposedDetails.open = true;
    const proposedSummary = document.createElement("summary");
    proposedSummary.textContent = "Proposed code";
    const proposed = document.createElement("pre");
    proposed.textContent = entry.approval.proposed_code;
    proposedDetails.append(proposedSummary, proposed);

    const originalDetails = document.createElement("details");
    originalDetails.className = "approval-code";
    const originalSummary = document.createElement("summary");
    originalSummary.textContent = "Current code";
    const original = document.createElement("pre");
    original.textContent = entry.approval.original_code;
    originalDetails.append(originalSummary, original);

    card.append(role, filename, instructions, proposedDetails, originalDetails);
    if (entry.completed) {
        const status = document.createElement("p");
        status.className = "approval-status";
        status.textContent = entry.decision
            ? entry.saved
                ? "Approved — changes saved."
                : "Approved, but the file could not be saved."
            : "Declined — file left unchanged.";
        card.append(status);
        return card;
    }
    if (entry.decision !== null) {
        const status = document.createElement("p");
        status.className = "approval-status";
        status.textContent = entry.decision
            ? "Approved — applying changes…"
            : "Declined — recording your decision…";
        card.append(status);
        return card;
    }
    if (entry.unavailable) {
        const status = document.createElement("p");
        status.className = "approval-status";
        status.textContent = "This review request is no longer active. Check the project files to confirm their current contents.";
        card.append(status);
        return card;
    }

    const actions = document.createElement("div");
    actions.className = "approval-actions";
    const reject = document.createElement("button");
    reject.type = "button";
    reject.className = "secondary-button";
    reject.textContent = "Decline";
    const approve = document.createElement("button");
    approve.type = "button";
    approve.className = "primary-button";
    approve.textContent = "Approve and save";
    for (const button of [reject, approve]) button.disabled = entry.submitting;
    const submitDecision = async (approved) => {
        entry.submitting = true;
        renderActiveChatSession();
        try {
            const result = await api(
                `/api/tasks/${encodeURIComponent(session.id)}/approvals/${encodeURIComponent(entry.approval.approval_id)}`,
                { method: "POST", body: JSON.stringify({ approved }) },
            );
            entry.decision = result.approved;
            showToast(approved ? "Code change approved." : "Code change declined.");
        } catch (error) {
            entry.submitting = false;
            if (error.status === 404) entry.unavailable = true;
            showToast(error.message, true);
        }
        if (session === activeChatSession) renderActiveChatSession();
    };
    reject.addEventListener("click", () => submitDecision(false));
    approve.addEventListener("click", () => submitDecision(true));
    actions.append(reject, approve);
    if (entry.submitting) {
        const waiting = document.createElement("p");
        waiting.className = "approval-status";
        waiting.textContent = "Sending your decision…";
        card.append(waiting);
    }
    card.append(actions);
    return card;
}

function connectTaskLogStream(session) {
    session.stream = new EventSource(
        `/api/tasks/${encodeURIComponent(session.id)}/logs`,
    );
    session.stream.onmessage = (message) => {
        try {
            appendActivityLog(JSON.parse(message.data), session);
        } catch {
            showToast("Could not read a build log entry.", true);
        }
    };
    session.stream.onerror = () => {
        if (session.stream.readyState === EventSource.CLOSED) {
            showToast("The Redis log stream connection closed.", true);
        }
    };
}

document.querySelector("#task-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const task = taskInput.value.trim();
    const session = activeChatSession;
    if (!task || session.running) return;

    session.running = true;
    session.status = "running";
    session.pendingTask = task;
    session.initialUserLogHidden = false;
    appendActivityLog({ role: "User", content: task }, session);
    renderChatSessions();
    updateSubmitState();
    taskInput.value = "";
    updateSubmitState();
    try {
        const result = await api("http://localhost:8000/api/tasks", {
            method: "POST",
            body: JSON.stringify({
                task,
                mode: modeSelect.value,
                agent: agentSelect.value || null,
                session_id: session.id,
            }),
        });
        appendActivityLog({ role: "AI", content: result.message }, session);
        session.status = "done";
        renderChatSessions();
        if (session === activeChatSession) renderActiveChatSession();
        showToast("Build finished successfully.");
        await loadApps(result.app);
    } catch (error) {
        appendActivityLog({ role: "AI", content: error.message }, session);
        session.status = "error";
        renderChatSessions();
        if (session === activeChatSession) renderActiveChatSession();
        showToast(error.message, true);
    } finally {
        session.running = false;
        renderChatSessions();
        updateSubmitState();
    }
});

taskInput.addEventListener("input", updateSubmitState);
taskInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        if (!submitButton.disabled) {
            document.querySelector("#task-form").requestSubmit();
        }
    }
});
agentSelect.addEventListener("change", updateSubmitState);
modeSelect.addEventListener("change", updateSubmitState);
document.querySelector("#open-agents").addEventListener("click", () => {
    renderAgentChoices(agentSearch.value);
    agentsDialog.showModal();
    agentSearch.focus();
});
document.querySelector("#close-agents").addEventListener("click", () => agentsDialog.close());
document.querySelector("#open-skills").addEventListener("click", openSkillsDialog);
document.querySelector("#close-skills").addEventListener("click", () => skillsDialog.close());
document.querySelector("#open-settings").addEventListener("click", openSettingsDialog);
document.querySelector("#close-settings").addEventListener("click", () => {
    if (settingsRequired) {
        showToast("Complete the required settings before continuing.", true);
        return;
    }
    settingsDialog.close();
});
settingsDialog.addEventListener("cancel", (event) => {
    if (settingsRequired) event.preventDefault();
});
settingsDialog.addEventListener("click", (event) => {
    if (event.target === settingsDialog && settingsRequired) {
        event.preventDefault();
    } else if (event.target === settingsDialog) {
        settingsDialog.close();
    }
});
settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    settingsValidationAttempted = true;
    if (!validateSettingsForm()) {
        settingsStatus.textContent = "Correct the highlighted settings before saving.";
        showToast("Complete the required settings with valid values.", true);
        settingsForm.querySelector(".is-invalid")?.focus();
        return;
    }
    const settings = Object.fromEntries(
        Array.from(settingsForm.querySelectorAll("[data-setting-name]"))
            .map((input) => [input.dataset.settingName, input.value.trim()])
            .filter(([, value]) => value),
    );
    if (!Object.keys(settings).length) {
        showToast("Enter at least one setting to save.", true);
        return;
    }
    const submitButton = settingsForm.querySelector('[type="submit"]');
    submitButton.disabled = true;
    try {
        const status = await api("/api/settings/environment", {
            method: "POST",
            body: JSON.stringify({ settings }),
        });
        for (const input of settingsForm.querySelectorAll("[data-setting-name]")) {
            input.value = "";
        }
        updateEnvironmentSettingsStatus(status);
        settingsStatus.textContent = "Settings saved to /data/env.txt.";
        showToast("Settings saved on the server.");
        window.location.reload();
    } catch (error) {
        for (const [name, message] of Object.entries(error.fieldErrors || {})) {
            const input = settingsForm.querySelector(`[data-setting-name="${name}"]`);
            if (!input) continue;
            input.classList.add("is-invalid");
            input.setAttribute("aria-invalid", "true");
            const row = input.closest("[data-setting-row]");
            row.classList.add("has-error");
            row.querySelector("[data-setting-status]").textContent = message;
        }
        showToast(error.message, true);
    } finally {
        submitButton.disabled = false;
    }
});
settingsForm.querySelectorAll("[data-clear-setting]").forEach((clearButton) => {
    clearButton.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        const row = button.closest("[data-setting-row]");
        const name = row.dataset.settingRow;
        button.disabled = true;
        try {
            const status = await api(`/api/settings/environment/${encodeURIComponent(name)}`, {
                method: "DELETE",
            });
            row.querySelector("[data-setting-name]").value = "";
            updateEnvironmentSettingsStatus(status);
            settingsStatus.textContent = `${name} removed from /data/env.txt.`;
        } catch (error) {
            showToast(error.message, true);
            button.disabled = false;
        }
    });
});
settingsForm.querySelectorAll("[data-setting-name]").forEach((input) => {
    input.addEventListener("input", () => {
        if (settingsValidationAttempted) validateSettingsForm();
    });
});
document.querySelector("#new-skill").addEventListener("click", () => {
    skillBrowser.hidden = true;
    skillCreateForm.hidden = false;
    skillTopic.focus();
});
document.querySelector("#cancel-skill").addEventListener("click", () => {
    skillCreateForm.hidden = true;
    skillBrowser.hidden = false;
});
skillTopic.addEventListener("input", () => {
    document.querySelector("#generate-skill").disabled = skillGenerating || !skillTopic.value.trim();
});
skillCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const topic = skillTopic.value.trim();
    if (!topic || skillGenerating) return;

    skillGenerating = true;
    const submit = document.querySelector("#generate-skill");
    submit.disabled = true;
    document.querySelector("#generate-skill-label").textContent = "Generating…";
    try {
        const skill = await api("http://localhost:8000/api/skills", {
            method: "POST",
            body: JSON.stringify({ topic }),
        });
        skills.unshift(skill);
        selectedSkill = "";
        skillTopic.value = "";
        skillCreateForm.hidden = true;
        skillBrowser.hidden = false;
        document.querySelector("#skill-count").textContent = String(skills.length);
        renderSkillChoices();
        selectSkill(skill);
        showToast(`“${skill.title}” added to your skill library.`);
    } catch (error) {
        showToast(error.message, true);
    } finally {
        skillGenerating = false;
        document.querySelector("#generate-skill-label").textContent = "Generate skill";
        submit.disabled = !skillTopic.value.trim();
    }
});
skillsDialog.addEventListener("click", (event) => {
    if (event.target === skillsDialog) skillsDialog.close();
});
document.querySelector("#use-auto-agent").addEventListener("click", () => {
    agentSelect.value = "";
    modeSelect.value = "individual";
    updateSubmitState();
    agentsDialog.close();
    showToast("Dev Agent will choose an agent for this task.");
});
agentSearch.addEventListener("input", () => renderAgentChoices(agentSearch.value));
agentsDialog.addEventListener("click", (event) => {
    if (event.target === agentsDialog) agentsDialog.close();
});
document.querySelector("#refresh-apps").addEventListener("click", () => loadApps());

addChatSessionButton.addEventListener("click", addChatSession);
renderChatSessions();
renderActiveChatSession();
saveChatSessions();
for (const session of chatSessions) connectTaskLogStream(session);
loadAgents();
loadApps();
loadSkills();
updateSubmitState();
if (new URLSearchParams(window.location.search).get("settings") === "google-api-key") {
    openSettingsDialog();
    window.history.replaceState({}, "", window.location.pathname);
} else {
    requireEnvironmentSettings();
}
