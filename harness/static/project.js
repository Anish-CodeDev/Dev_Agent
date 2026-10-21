const projectName = document.body.dataset.project;
const fileTree = document.querySelector("#project-file-tree");
const previewTitle = document.querySelector("#project-preview-title");
const previewLanguage = document.querySelector("#project-preview-language");
const codePreview = document.querySelector("#project-code");
const projectList = document.querySelector("#project-list");
const toast = document.querySelector("#toast");

let selectedFileButton = null;
let toastTimer;

try {
    localStorage.removeItem("dev-agent-google-api-key");
} catch (error) {
    showToast("Could not remove the old browser-stored Google API key.", true);
}

async function api(url, options = {}) {
    const { headers: suppliedHeaders = {}, ...requestOptions } = options;
    const headers = { "Content-Type": "application/json", ...suppliedHeaders };
    const response = await fetch(url, {
        ...requestOptions,
        headers,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || data.detail || `Request failed (${response.status}).`);
    return data;
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
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

document.querySelector("#refresh-project-files").addEventListener("click", loadProjectTree);
loadProjectTree();
