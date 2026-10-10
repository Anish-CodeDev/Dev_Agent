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
const skillsDialog = document.querySelector("#skills-dialog");
const skillChoiceList = document.querySelector("#skill-choice-list");
const skillBrowser = document.querySelector("#skills-browser");
const skillCreateForm = document.querySelector("#skill-create-form");
const skillTopic = document.querySelector("#skill-topic");
const skillPreviewTitle = document.querySelector("#skill-preview-title");
const skillPreviewDescription = document.querySelector("#skill-preview-description");
const skillContent = document.querySelector("#skill-content code");

let apps = [];
let agents = [];
let skills = [];
let toastTimer;
let taskRunning = false;
let skillGenerating = false;

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
document.querySelector("#open-skills").addEventListener("click", openSkillsDialog);
document.querySelector("#close-skills").addEventListener("click", () => skillsDialog.close());
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
        const skill = await api("/api/skills", {
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

loadAgents();
loadApps();
loadSkills();
updateSubmitState();
