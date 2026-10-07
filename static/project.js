const projectName = document.body.dataset.project;
const fileTree = document.querySelector("#project-file-tree");
const previewTitle = document.querySelector("#project-preview-title");
const previewLanguage = document.querySelector("#project-preview-language");
const codePreview = document.querySelector("#project-code");
const projectList = document.querySelector("#project-list");
const chatMessages = document.querySelector("#chat-messages");
const chatInput = document.querySelector("#project-chat-input");
const sendButton = document.querySelector("#send-project-chat");
const toast = document.querySelector("#toast");
const historyKey = `dev-agent-project-chat:${projectName}`;

let selectedFileButton = null;
let chatHistory = loadHistory();
let toastTimer;
let chatBusy = false;

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
    return data;
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function loadHistory() {
    try {
        const saved = JSON.parse(sessionStorage.getItem(historyKey) || "[]");
        if (!Array.isArray(saved)) return [];
        return saved.filter((item) => (
            item && ["user", "assistant"].includes(item.role) && typeof item.content === "string"
        )).slice(-20);
    } catch {
        return [];
    }
}

function saveHistory() {
    sessionStorage.setItem(historyKey, JSON.stringify(chatHistory.slice(-20)));
}

function renderChatHistory() {
    if (!chatHistory.length) return;
    chatMessages.replaceChildren();
    for (const message of chatHistory) appendChatMessage(message.role, message.content);
}

function appendChatMessage(role, content, className = "") {
    const message = document.createElement("article");
    message.className = `chat-message ${role === "user" ? "user-message" : "assistant-message"} ${className}`.trim();
    const label = document.createElement("span");
    label.className = "chat-message-label";
    label.textContent = role === "user" ? "YOU" : "PROJECT ASSISTANT";
    const body = document.createElement("p");
    body.textContent = content;
    message.append(label, body);
    chatMessages.append(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return message;
}

function renderProjects(apps) {
    projectList.replaceChildren();
    for (const app of apps) {
        const link = document.createElement("a");
        link.className = `project-link${app.name === projectName ? " selected" : ""}`;
        link.href = `/projects/${encodeURIComponent(app.name)}`;
        const glyph = document.createElement("span");
        glyph.className = "project-glyph";
        glyph.setAttribute("aria-hidden", "true");
        glyph.textContent = "◧";
        const name = document.createElement("span");
        name.className = "project-title";
        name.textContent = app.name;
        link.append(glyph, name);
        projectList.append(link);
    }
}

function makeTreeList(nodes, depth = 0) {
    const list = document.createElement("ul");
    list.className = depth ? "tree-list nested" : "tree-list";
    list.setAttribute("role", "group");
    for (const node of nodes) {
        const entry = document.createElement("li");
        entry.className = "tree-entry";
        entry.setAttribute("role", "treeitem");
        const button = document.createElement("button");
        button.className = "tree-item";
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
            const children = makeTreeList(node.children || [], depth + 1);
            entry.append(children);
            button.setAttribute("aria-expanded", "true");
            button.addEventListener("click", () => {
                const expanded = button.getAttribute("aria-expanded") === "true";
                button.setAttribute("aria-expanded", String(!expanded));
                children.hidden = expanded;
                caret.textContent = expanded ? "▸" : "▾";
            });
        } else {
            button.addEventListener("click", () => {
                if (selectedFileButton) selectedFileButton.classList.remove("selected");
                button.classList.add("selected");
                selectedFileButton = button;
                loadFile(node.path);
            });
        }
        list.append(entry);
    }
    return list;
}

async function loadProjectTree() {
    fileTree.replaceChildren();
    const loading = document.createElement("div");
    loading.className = "tree-empty";
    loading.textContent = "Loading project files…";
    fileTree.append(loading);
    try {
        const [data, apps] = await Promise.all([
            api(`/api/apps/${encodeURIComponent(projectName)}/files`),
            api("/api/apps"),
        ]);
        document.querySelector("#project-file-count").textContent = `${data.file_count} files`;
        fileTree.replaceChildren();
        if (!data.tree.length) {
            const empty = document.createElement("div");
            empty.className = "tree-empty";
            empty.textContent = "No files are recorded for this project yet.";
            fileTree.append(empty);
        } else {
            fileTree.append(makeTreeList(data.tree));
        }
        renderProjects(apps);
    } catch (error) {
        fileTree.replaceChildren();
        const failure = document.createElement("div");
        failure.className = "tree-empty";
        failure.textContent = error.message;
        fileTree.append(failure);
        showToast(error.message, true);
    }
}

function languageFor(path) {
    const extension = path.split(".").pop().toLowerCase();
    const names = {
        css: "css", html: "html", js: "javascript", jsx: "jsx", json: "json",
        md: "markdown", py: "python", ts: "typescript", tsx: "tsx", txt: "text",
        yml: "yaml", yaml: "yaml",
    };
    return names[extension] || extension || "text";
}

async function loadFile(path) {
    previewTitle.textContent = path;
    previewLanguage.textContent = languageFor(path);
    codePreview.textContent = "Loading file…";
    const encodedPath = path.split("/").map(encodeURIComponent).join("/");
    try {
        const file = await api(`/api/apps/${encodeURIComponent(projectName)}/file/${encodedPath}`);
        codePreview.textContent = file.content;
    } catch (error) {
        codePreview.textContent = error.message;
        showToast(error.message, true);
    }
}

function updateChatSubmit() {
    sendButton.disabled = chatBusy || !chatInput.value.trim();
}

document.querySelector("#project-chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatBusy) return;

    chatBusy = true;
    updateChatSubmit();
    chatHistory.push({ role: "user", content: message });
    appendChatMessage("user", message);
    chatInput.value = "";
    const pending = appendChatMessage("assistant", "Thinking…", "pending-message");

    try {
        const response = await api(`/api/apps/${encodeURIComponent(projectName)}/chat`, {
            method: "POST",
            body: JSON.stringify({
                message,
                history: chatHistory.slice(0, -1).slice(-20),
            }),
        });
        pending.remove();
        const reply = typeof response.reply === "string"
            ? response.reply
            : JSON.stringify(response.reply);
        chatHistory.push({ role: "assistant", content: reply });
        chatHistory = chatHistory.slice(-20);
        saveHistory();
        appendChatMessage("assistant", reply);
    } catch (error) {
        pending.remove();
        appendChatMessage("assistant", error.message, "chat-error");
        showToast(error.message, true);
    } finally {
        chatBusy = false;
        updateChatSubmit();
        chatInput.focus();
    }
});

chatInput.addEventListener("input", updateChatSubmit);
chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.querySelector("#project-chat-form").requestSubmit();
    }
});
document.querySelector("#refresh-project-files").addEventListener("click", loadProjectTree);
renderChatHistory();
loadProjectTree();
updateChatSubmit();
