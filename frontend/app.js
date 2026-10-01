// AI Software Engineer Agent - Client Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // State management
    const state = {
        activeRepoPath: null,
        activeRepoName: null,
        selectedFilePath: null,
        selectedFileContent: "",
        graphNetwork: null,
        apiKeys: {
            openai: localStorage.getItem("ai_agent_openai_key") || "",
            anthropic: localStorage.getItem("ai_agent_anthropic_key") || "",
            gemini: localStorage.getItem("ai_agent_gemini_key") || "",
            githubToken: localStorage.getItem("ai_agent_github_token") || ""
        }
    };

    // DOM Elements
    const elements = {
        providerSelect: document.getElementById("provider-select"),
        settingsBtn: document.getElementById("settings-btn"),
        settingsModal: document.getElementById("settings-modal"),
        closeModalBtn: document.getElementById("close-modal-btn"),
        saveSettingsBtn: document.getElementById("save-settings-btn"),
        modalOpenaiKey: document.getElementById("modal-openai-key"),
        modalAnthropicKey: document.getElementById("modal-anthropic-key"),
        modalGeminiKey: document.getElementById("modal-gemini-key"),
        modalGithubToken: document.getElementById("modal-github-token"),
        
        repoUrlInput: document.getElementById("repo-url-input"),
        cloneBtn: document.getElementById("clone-btn"),
        activeRepoBadge: document.getElementById("active-repo-badge"),
        activeRepoName: document.getElementById("active-repo-name"),
        fileTreeContainer: document.getElementById("file-tree-container"),
        fileSearchInput: document.getElementById("file-search-input"),
        
        tabBtns: document.querySelectorAll(".tab-btn"),
        tabContents: document.querySelectorAll(".tab-content"),
        
        analyzeArchBtn: document.getElementById("analyze-arch-btn"),
        graphContainer: document.getElementById("graph-container"),
        graphStats: document.getElementById("graph-stats"),
        archOutput: document.getElementById("arch-output"),
        
        currentFileName: document.getElementById("current-file-name"),
        codeViewer: document.getElementById("code-viewer"),
        explainCodeBtn: document.getElementById("explain-code-btn"),
        codeExplainOutput: document.getElementById("code-explain-output"),
        
        bugIssueInput: document.getElementById("bug-issue-input"),
        bugTargetFile: document.getElementById("bug-target-file"),
        fixBugBtn: document.getElementById("fix-bug-btn"),
        bugFixStatus: document.getElementById("bug-fix-status"),
        bugFixExplanation: document.getElementById("bug-fix-explanation"),
        diffOriginal: document.getElementById("diff-original"),
        diffFixed: document.getElementById("diff-fixed"),
        
        generateTestsBtn: document.getElementById("generate-tests-btn"),
        testFileTitle: document.getElementById("test-file-title"),
        testCodeViewer: document.getElementById("test-code-viewer"),
        copyTestBtn: document.getElementById("copy-test-btn"),
        
        prDiffInput: document.getElementById("pr-diff-input"),
        reviewPrBtn: document.getElementById("review-pr-btn"),
        prReviewOutput: document.getElementById("pr-review-output"),
        createPrForm: document.getElementById("create-pr-form"),
        prOwnerRepo: document.getElementById("pr-owner-repo"),
        prBranchName: document.getElementById("pr-branch-name"),
        prTitle: document.getElementById("pr-title"),
        prBody: document.getElementById("pr-body"),
        prCreateStatus: document.getElementById("pr-create-status")
    };

    // Initialize UI settings values
    elements.modalOpenaiKey.value = state.apiKeys.openai;
    elements.modalAnthropicKey.value = state.apiKeys.anthropic;
    elements.modalGeminiKey.value = state.apiKeys.gemini;
    elements.modalGithubToken.value = state.apiKeys.githubToken;

    // Helper: Active Key for selected Provider
    function getActiveApiKey() {
        const provider = elements.providerSelect.value;
        if (provider === "openai") return state.apiKeys.openai;
        if (provider === "anthropic") return state.apiKeys.anthropic;
        if (provider === "gemini") return state.apiKeys.gemini;
        return "";
    }

    // Modal Events
    elements.settingsBtn.addEventListener("click", () => elements.settingsModal.classList.remove("hidden"));
    elements.closeModalBtn.addEventListener("click", () => elements.settingsModal.classList.add("hidden"));
    elements.saveSettingsBtn.addEventListener("click", () => {
        state.apiKeys.openai = elements.modalOpenaiKey.value.trim();
        state.apiKeys.anthropic = elements.modalAnthropicKey.value.trim();
        state.apiKeys.gemini = elements.modalGeminiKey.value.trim();
        state.apiKeys.githubToken = elements.modalGithubToken.value.trim();

        localStorage.setItem("ai_agent_openai_key", state.apiKeys.openai);
        localStorage.setItem("ai_agent_anthropic_key", state.apiKeys.anthropic);
        localStorage.setItem("ai_agent_gemini_key", state.apiKeys.gemini);
        localStorage.setItem("ai_agent_github_token", state.apiKeys.githubToken);

        elements.settingsModal.classList.add("hidden");
        alert("Settings & API Keys saved successfully!");
    });

    // Tab Switching Logic
    elements.tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            elements.tabBtns.forEach(b => b.classList.remove("active"));
            elements.tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const tabId = `tab-${btn.dataset.tab}`;
            document.getElementById(tabId).classList.add("active");
        });
    });

    // Repository Ingestion / Clone
    elements.cloneBtn.addEventListener("click", async () => {
        const repoInput = elements.repoUrlInput.value.trim();
        if (!repoInput) {
            alert("Please enter a GitHub URL or local repository path!");
            return;
        }

        elements.cloneBtn.disabled = true;
        elements.cloneBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...`;

        try {
            const resp = await fetch("/api/repo/clone", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_url_or_path: repoInput })
            });

            const data = await resp.json();
            if (resp.ok && data.status === "success") {
                state.activeRepoPath = data.repo_path;
                state.activeRepoName = data.repo_name;
                elements.activeRepoName.textContent = data.repo_name;
                elements.activeRepoBadge.classList.remove("hidden");

                await loadFileTree();
            } else {
                alert(`Error: ${data.detail || data.message || "Failed to clone repository"}`);
            }
        } catch (err) {
            alert(`Connection Error: ${err.message}`);
        } finally {
            elements.cloneBtn.disabled = false;
            elements.cloneBtn.innerHTML = `<i class="fa-solid fa-download"></i> Ingest`;
        }
    });

    // Load Workspace File Tree
    async function loadFileTree() {
        if (!state.activeRepoPath) return;

        try {
            const resp = await fetch(`/api/repo/tree?repo_path=${encodeURIComponent(state.activeRepoPath)}`);
            const data = await resp.json();

            if (data.files && data.files.length > 0) {
                renderFileTree(data.files);
            } else {
                elements.fileTreeContainer.innerHTML = `<div class="empty-state">No readable code files found.</div>`;
            }
        } catch (err) {
            console.error("Failed to load file tree:", err);
        }
    }

    function renderFileTree(files) {
        elements.fileTreeContainer.innerHTML = "";
        
        files.forEach(file => {
            const item = document.createElement("div");
            item.className = "tree-item";
            item.dataset.path = file.path;

            const iconClass = file.extension === ".py" ? "fa-python" :
                              (file.extension === ".js" || file.extension === ".ts" ? "fa-js" : "fa-file-code");

            item.innerHTML = `<i class="fa-brands ${iconClass}"></i> <span>${file.path}</span>`;
            
            item.addEventListener("click", () => {
                document.querySelectorAll(".tree-item").forEach(i => i.classList.remove("selected"));
                item.classList.add("selected");
                selectFile(file.path);
            });

            elements.fileTreeContainer.appendChild(item);
        });
    }

    // Filter File Tree
    elements.fileSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase();
        document.querySelectorAll(".tree-item").forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(query) ? "flex" : "none";
        });
    });

    // Select File & Read Content
    async function selectFile(relPath) {
        state.selectedFilePath = relPath;
        elements.currentFileName.innerHTML = `<i class="fa-regular fa-file-code"></i> ${relPath}`;
        elements.bugTargetFile.value = relPath;

        try {
            const resp = await fetch("/api/repo/read-file", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_path: state.activeRepoPath, rel_path: relPath })
            });
            const data = await resp.json();
            state.selectedFileContent = data.content || "";
            elements.codeViewer.textContent = state.selectedFileContent;
            Prism.highlightElement(elements.codeViewer);
        } catch (err) {
            elements.codeViewer.textContent = `// Error loading file: ${err.message}`;
        }
    }

    // TAB 1: Architecture Knowledge Graph & Analysis
    elements.analyzeArchBtn.addEventListener("click", async () => {
        if (!state.activeRepoPath) {
            alert("Please ingest a repository first!");
            return;
        }

        elements.analyzeArchBtn.disabled = true;
        elements.analyzeArchBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Building Graph...`;

        try {
            // 1. Fetch Dependency Graph
            const graphResp = await fetch(`/api/repo/graph?repo_path=${encodeURIComponent(state.activeRepoPath)}`, { method: "POST" });
            const graphResult = await graphResp.json();
            
            if (graphResult.graph) {
                renderVisGraph(graphResult.graph);
                elements.graphStats.textContent = `Nodes: ${graphResult.graph.total_nodes} | Edges: ${graphResult.graph.total_edges}`;
            }

            // 2. Fetch LLM Architectural Breakdown Report
            elements.archOutput.innerHTML = `<p class="placeholder-text"><i class="fa-solid fa-spinner fa-spin"></i> Generating architectural report via LLM...</p>`;
            
            const archResp = await fetch("/api/agent/explain-arch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repo_path: state.activeRepoPath,
                    provider: elements.providerSelect.value,
                    api_key: getActiveApiKey()
                })
            });

            const archData = await archResp.json();
            if (archData.architecture_markdown) {
                elements.archOutput.innerHTML = marked.parse(archData.architecture_markdown);
            } else {
                elements.archOutput.innerHTML = `<p style="color: var(--accent-rose)">${archData.detail || "Error generating architecture report."}</p>`;
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            elements.analyzeArchBtn.disabled = false;
            elements.analyzeArchBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Analyze Architecture`;
        }
    });

    function renderVisGraph(graphData) {
        const container = elements.graphContainer;
        container.innerHTML = "";
        container.style.height = "420px";  // vis.js needs explicit height

        const nodes = new vis.DataSet(graphData.nodes.map(n => ({
            id: n.id,
            label: n.label,
            color: n.group === "file" ? "#38bdf8" : (n.group === "class" ? "#a855f7" : "#34d399"),
            shape: n.group === "file" ? "box" : "ellipse",
            font: { color: "#ffffff", face: "Inter" },
            size: n.group === "file" ? 20 : 12
        })));

        const edges = new vis.DataSet(graphData.edges.map(e => ({
            from: e.from,
            to: e.to,
            arrows: "to",
            color: { color: "#475569" }
        })));

        const data = { nodes, edges };
        const options = {
            physics: {
                solver: "forceAtlas2Based",
                forceAtlas2Based: { gravitationalConstant: -30, centralGravity: 0.005, springLength: 100 },
                stabilization: { iterations: 150 }
            },
            interaction: { hover: true, zoomView: true, dragView: true }
        };

        state.graphNetwork = new vis.Network(container, data, options);
        state.graphNetwork.once("stabilized", () => state.graphNetwork.fit());
    }

    // TAB 2: Code Explainer
    elements.explainCodeBtn.addEventListener("click", async () => {
        if (!state.selectedFilePath) {
            alert("Please select a file from the workspace explorer first!");
            return;
        }

        elements.explainCodeBtn.disabled = true;
        elements.explainCodeBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Explaining...`;
        elements.codeExplainOutput.innerHTML = `<p class="placeholder-text">Analyzing file code...</p>`;

        try {
            const resp = await fetch("/api/agent/explain-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repo_path: state.activeRepoPath,
                    target_file: state.selectedFilePath,
                    provider: elements.providerSelect.value,
                    api_key: getActiveApiKey()
                })
            });

            const data = await resp.json();
            if (data.explanation_markdown) {
                elements.codeExplainOutput.innerHTML = marked.parse(data.explanation_markdown);
                document.getElementById("explain-output-card")?.scrollIntoView({ behavior: "smooth" });
            } else {
                elements.codeExplainOutput.innerHTML = `<p style="color: var(--accent-rose)">${data.detail || "Error generating code explanation."}</p>`;
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            elements.explainCodeBtn.disabled = false;
            elements.explainCodeBtn.innerHTML = `<i class="fa-solid fa-lightbulb"></i> Explain Selected File`;
        }
    });

    // TAB 3: Bug Hunter & Fixer
    elements.fixBugBtn.addEventListener("click", async () => {
        const issue = elements.bugIssueInput.value.trim();
        if (!issue) {
            alert("Please describe the bug or paste an error traceback!");
            return;
        }

        elements.fixBugBtn.disabled = true;
        elements.fixBugBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Fixing Bug...`;
        elements.bugFixStatus.textContent = "Analyzing Code & Generating Patch...";

        try {
            const resp = await fetch("/api/agent/fix-bug", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repo_path: state.activeRepoPath,
                    issue_description: issue,
                    target_file: elements.bugTargetFile.value.trim() || state.selectedFilePath,
                    provider: elements.providerSelect.value,
                    api_key: getActiveApiKey()
                })
            });

            const data = await resp.json();
            if (resp.ok && data.status === "success") {
                elements.bugFixStatus.textContent = data.applied_to_file ? "Fix Applied to Workspace File!" : "Patch Generated";
                elements.bugFixExplanation.innerHTML = `<p><strong>File Affected:</strong> <code>${data.target_file}</code></p><p>${data.explanation}</p>`;
                
                elements.diffOriginal.textContent = data.original_snippet || "// Original snippet";
                elements.diffFixed.textContent = data.fixed_snippet || "// Fixed snippet";
                
                Prism.highlightElement(elements.diffOriginal);
                Prism.highlightElement(elements.diffFixed);

                // Reload file tree & content if file changed
                await loadFileTree();
            } else {
                elements.bugFixStatus.textContent = "Error";
                elements.bugFixExplanation.innerHTML = `<p style="color: var(--accent-rose)">${data.detail || data.message || "Failed to fix bug."}</p>`;
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            elements.fixBugBtn.disabled = false;
            elements.fixBugBtn.innerHTML = `<i class="fa-solid fa-wrench"></i> Generate & Apply Bug Fix`;
        }
    });

    // TAB 4: Unit Test Generator
    elements.generateTestsBtn.addEventListener("click", async () => {
        if (!state.selectedFilePath) {
            alert("Please select a target code file from the left workspace explorer!");
            return;
        }

        elements.generateTestsBtn.disabled = true;
        elements.generateTestsBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating Unit Tests...`;

        try {
            const resp = await fetch("/api/agent/generate-tests", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repo_path: state.activeRepoPath,
                    target_file: state.selectedFilePath,
                    provider: elements.providerSelect.value,
                    api_key: getActiveApiKey()
                })
            });

            const data = await resp.json();
            if (data.test_code) {
                elements.testFileTitle.textContent = `Generated Test Suite: ${data.test_file_path}`;
                elements.testCodeViewer.textContent = data.test_code;
                Prism.highlightElement(elements.testCodeViewer);
                
                // Refresh workspace tree to show new test file
                await loadFileTree();
            } else {
                alert(`Error: ${data.detail || "Could not generate unit tests."}`);
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            elements.generateTestsBtn.disabled = false;
            elements.generateTestsBtn.innerHTML = `<i class="fa-solid fa-vial-circle-check"></i> Generate Tests`;
        }
    });

    elements.copyTestBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(elements.testCodeViewer.textContent);
        alert("Test code copied to clipboard!");
    });

    // TAB 5: PR Reviewer & Creator
    elements.reviewPrBtn.addEventListener("click", async () => {
        const diffText = elements.prDiffInput.value.trim();
        if (!diffText) {
            alert("Please paste a git diff or code snippet to review!");
            return;
        }

        elements.reviewPrBtn.disabled = true;
        elements.reviewPrBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Reviewing...`;
        elements.prReviewOutput.innerHTML = `<p class="placeholder-text">Reviewing Pull Request diff...</p>`;

        try {
            const resp = await fetch("/api/agent/review-pr", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    git_diff_or_code: diffText,
                    provider: elements.providerSelect.value,
                    api_key: getActiveApiKey()
                })
            });

            const data = await resp.json();
            if (data.review_markdown) {
                elements.prReviewOutput.innerHTML = marked.parse(data.review_markdown);
            } else {
                elements.prReviewOutput.innerHTML = `<p style="color: var(--accent-rose)">${data.detail || "Failed to review PR."}</p>`;
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            elements.reviewPrBtn.disabled = false;
            elements.reviewPrBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Review Diff`;
        }
    });

    // Create GitHub PR Form Submit
    elements.createPrForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const ownerRepo = elements.prOwnerRepo.value.trim();
        const branch = elements.prBranchName.value.trim();
        const title = elements.prTitle.value.trim();
        const body = elements.prBody.value.trim();

        if (!ownerRepo || !branch || !title) {
            alert("Please fill in repository, branch name, and PR title!");
            return;
        }

        const ghToken = state.apiKeys.githubToken;
        if (!ghToken) {
            alert("GitHub Personal Access Token is required to open PRs. Click 'API Keys & Settings' to enter your token.");
            return;
        }

        elements.prCreateStatus.classList.remove("hidden");
        elements.prCreateStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Opening Pull Request on GitHub...`;

        try {
            // Get current selected file modification if present
            const modifiedFiles = {};
            if (state.selectedFilePath && state.selectedFileContent) {
                modifiedFiles[state.selectedFilePath] = state.selectedFileContent;
            }

            const resp = await fetch("/api/agent/create-pr", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    repo_owner_repo: ownerRepo,
                    branch_name: branch,
                    commit_message: title,
                    pr_title: title,
                    pr_body: body,
                    modified_files: modifiedFiles,
                    github_token: ghToken
                })
            });

            const data = await resp.json();
            if (resp.ok && data.status === "success") {
                elements.prCreateStatus.innerHTML = `
                    <div style="color: var(--accent-emerald)">
                        <i class="fa-solid fa-circle-check"></i> Pull Request Created Successfully!
                        <p><a href="${data.pr_url}" target="_blank" style="color: var(--accent-blue)">View PR #${data.pr_number} on GitHub</a></p>
                    </div>
                `;
            } else {
                elements.prCreateStatus.innerHTML = `<div style="color: var(--accent-rose)"><i class="fa-solid fa-circle-xmark"></i> ${data.detail || data.message || "Failed to create PR."}</div>`;
            }
        } catch (err) {
            elements.prCreateStatus.innerHTML = `<div style="color: var(--accent-rose)">Error: ${err.message}</div>`;
        }
    });
});
