const agentSelect = document.querySelector("#agent-select");
const modeSelect = document.querySelector("#mode-select");
const taskInput = document.querySelector("#task-input");
const submitButton = document.querySelector("#submit-task");
const projectList = document.querySelector("#project-list");
const projectCardList = document.querySelector("#project-card-list");
const activityBody = document.querySelector("#activity-body");
const activityTitle = document.querySelector("#activity-title");
const activityIndicator = document.querySelector("#activity-indicator");
const toast = document.querySelector("#toast");
const agentsDialog = document.querySelector("#agents-dialog");
const agentChoiceList = document.querySelector("#agent-choice-list");
const agentSearch = document.querySelector("#agent-search");

let apps = [];
let agents = [];
let toastTimer;
let taskRunning = false;

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || `Request failed (${response.status}).`);
    }
    return data;
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function updateSubmitState() {
    submitButton.disabled = taskRunning || !taskInput.value.trim();
    document.querySelector("#char-count").textContent = `${taskInput.value.length.toLocaleString()} / 10,000`;
    document.querySelector("#agent-picker").hidden = modeSelect.value !== "individual";
}

function openAgentDialogFromQuery() {
    if (new URLSearchParams(window.location.search).get("view") !== "agents") return;
    renderAgentChoices(agentSearch.value);
    agentsDialog.showModal();
    agentSearch.focus();
}

function selectApp(appName) {
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

function showBuildResult(task, message, isError = false) {
    activityBody.replaceChildren();
    const taskText = document.createElement("p");
    taskText.className = "activity-task";
    taskText.textContent = task;
    const result = document.createElement("div");
    result.className = "activity-message";
    result.textContent = message;
    if (isError) result.style.borderColor = "#754348";
    activityBody.append(taskText, result);
    activityTitle.textContent = isError ? "Build needs attention" : "Build complete";
    activityIndicator.className = `activity-indicator ${isError ? "" : "done"}`;
    activityIndicator.replaceChildren();
    const dot = document.createElement("span");
    activityIndicator.append(dot, document.createTextNode(isError ? "ERROR" : "COMPLETE"));
}

document.querySelector("#task-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const task = taskInput.value.trim();
    if (!task || taskRunning) return;

    taskRunning = true;
    updateSubmitState();
    document.querySelector("#submit-label").textContent = "Building…";
    activityTitle.textContent = "Your agent is at work";
    activityIndicator.className = "activity-indicator running";
    activityIndicator.replaceChildren();
    const dot = document.createElement("span");
    activityIndicator.append(dot, document.createTextNode("RUNNING"));
    activityBody.replaceChildren();
    const progress = document.createElement("div");
    progress.className = "activity-empty";
    progress.textContent = modeSelect.value === "plan"
        ? "Planning the build, coordinating agents, and preparing your app. This can take a little while…"
        : "Passing your request through the agent workflow and preparing your app. This can take a little while…";
    activityBody.append(progress);

    try {
        const result = await api("/api/tasks", {
            method: "POST",
            body: JSON.stringify({
                task,
                mode: modeSelect.value,
                agent: agentSelect.value || null,
            }),
        });
        showBuildResult(task, result.message);
        showToast("Build finished successfully.");
        await loadApps(result.app);
    } catch (error) {
        showBuildResult(task, error.message, true);
        showToast(error.message, true);
    } finally {
        taskRunning = false;
        document.querySelector("#submit-label").textContent = "Start building";
        updateSubmitState();
    }
});

taskInput.addEventListener("input", updateSubmitState);
agentSelect.addEventListener("change", updateSubmitState);
modeSelect.addEventListener("change", updateSubmitState);
document.querySelector("#open-agents").addEventListener("click", () => {
    renderAgentChoices(agentSearch.value);
    agentsDialog.showModal();
    agentSearch.focus();
});
document.querySelector("#close-agents").addEventListener("click", () => agentsDialog.close());
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

loadAgents();
loadApps();
updateSubmitState();
