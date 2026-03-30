const API_BASE = "http://127.0.0.1:8000";
const STORAGE_KEY = "gateprep-session";

const state = {
    token: "",
    userId: "",
    documents: [],
    sources: [],
    flashcards: [],
    currentFlashcardIndex: 0,
    isFlipped: false,
};

const elements = {
    userId: document.getElementById("userId"),
    loginBtn: document.getElementById("loginBtn"),
    statusDot: document.getElementById("statusDot"),
    sessionLabel: document.getElementById("sessionLabel"),
    statusMessage: document.getElementById("statusMessage"),
    documentCount: document.getElementById("documentCount"),
    documentLibrary: document.getElementById("documentLibrary"),
    fileInput: document.getElementById("fileInput"),
    fileLabel: document.getElementById("fileLabel"),
    fileMeta: document.getElementById("fileMeta"),
    uploadBtn: document.getElementById("uploadBtn"),
    uploadBox: document.getElementById("uploadBox"),
    uploadSuccess: document.getElementById("uploadSuccess"),
    documentSelect: document.getElementById("documentSelect"),
    queryInput: document.getElementById("queryInput"),
    askBtn: document.getElementById("askBtn"),
    answerOutput: document.getElementById("answerOutput"),
    toggleSourcesBtn: document.getElementById("toggleSourcesBtn"),
    sourcesPanel: document.getElementById("sourcesPanel"),
    sourcesList: document.getElementById("sourcesList"),
    flashcardDocumentSelect: document.getElementById("flashcardDocumentSelect"),
    topicInput: document.getElementById("topicInput"),
    flashcardsBtn: document.getElementById("flashcardsBtn"),
    flashcardCard: document.getElementById("flashcardCard"),
    flashcardQuestion: document.getElementById("flashcardQuestion"),
    flashcardAnswer: document.getElementById("flashcardAnswer"),
    flashcardCounter: document.getElementById("flashcardCounter"),
    prevCardBtn: document.getElementById("prevCardBtn"),
    nextCardBtn: document.getElementById("nextCardBtn"),
};

function saveSession() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
            token: state.token,
            userId: state.userId,
        }),
    );
}

function loadSession() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
        updateSessionUI();
        return;
    }

    try {
        const parsed = JSON.parse(saved);
        state.token = parsed.token || "";
        state.userId = parsed.userId || "";
        elements.userId.value = state.userId;
    } catch {
        localStorage.removeItem(STORAGE_KEY);
    }

    updateSessionUI();
}

function setStatus(message) {
    elements.statusMessage.textContent = message;
}

function updateSessionUI() {
    const active = Boolean(state.token);
    elements.statusDot.classList.toggle("active", active);
    elements.sessionLabel.textContent = active
        ? `Active session for ${state.userId}`
        : "No active session";
    elements.documentCount.textContent = String(state.documents.length);

    if (!active) {
        setStatus("Enter your user ID to begin a secure study session.");
        return;
    }

    if (state.documents.length === 0) {
        setStatus("Session started. Upload your first PDF to begin.");
        return;
    }

    setStatus(`${state.documents.length} document${state.documents.length === 1 ? "" : "s"} ready for questions and flashcards.`);
}

function setButtonLoading(button, label) {
    const previousText = button.textContent;
    button.disabled = true;
    button.textContent = label;

    return () => {
        button.disabled = false;
        button.textContent = previousText;
    };
}

async function parseJsonResponse(response) {
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const detail = data.detail || data.error || "Request failed";
        throw new Error(Array.isArray(detail) ? detail.join(", ") : detail);
    }

    return data;
}

function requireSession() {
    if (state.token) {
        return true;
    }

    setStatus("Please start a session with your user ID first.");
    elements.userId.focus();
    return false;
}

function renderDocumentLibrary() {
    elements.documentLibrary.innerHTML = "";

    if (state.documents.length === 0) {
        elements.documentLibrary.classList.add("empty");
        elements.documentLibrary.innerHTML = "<p>No PDFs uploaded yet.</p>";
        return;
    }

    elements.documentLibrary.classList.remove("empty");
    const activeDocument = elements.documentSelect.value || elements.flashcardDocumentSelect.value;

    state.documents.forEach((documentName) => {
        const item = document.createElement("div");
        item.className = "document-item";
        if (documentName === activeDocument) {
            item.classList.add("active");
        }

        const title = document.createElement("span");
        title.className = "document-name";
        title.textContent = documentName;

        const meta = document.createElement("span");
        meta.className = "document-meta";
        meta.textContent = "Available for answers and flashcards";

        item.appendChild(title);
        item.appendChild(meta);
        elements.documentLibrary.appendChild(item);
    });
}

function renderDocumentSelectors() {
    const selects = [elements.documentSelect, elements.flashcardDocumentSelect];

    selects.forEach((select) => {
        const currentValue = select.value;
        select.innerHTML = '<option value="">All uploaded documents</option>';

        state.documents.forEach((documentName) => {
            const option = document.createElement("option");
            option.value = documentName;
            option.textContent = documentName;
            select.appendChild(option);
        });

        if (state.documents.includes(currentValue)) {
            select.value = currentValue;
        }
    });

    renderDocumentLibrary();
    updateSessionUI();
}

async function fetchDocuments() {
    if (!state.token) {
        return;
    }

    const response = await fetch(`${API_BASE}/documents`, {
        headers: {
            Authorization: `Bearer ${state.token}`,
        },
    });
    const data = await parseJsonResponse(response);
    state.documents = Array.isArray(data.documents) ? data.documents : [];
    renderDocumentSelectors();
}

async function login() {
    const userId = elements.userId.value.trim();
    if (!userId) {
        setStatus("Please enter your user ID.");
        elements.userId.focus();
        return;
    }

    const stopLoading = setButtonLoading(elements.loginBtn, "Starting...");

    try {
        const response = await fetch(`${API_BASE}/login?user_id=${encodeURIComponent(userId)}`, {
            method: "POST",
        });
        const data = await parseJsonResponse(response);
        state.userId = userId;
        state.token = data.access_token || "";
        saveSession();
        await fetchDocuments();
        setStatus("Session started successfully. Your token is managed internally.");
    } catch (error) {
        setStatus(error.message);
    } finally {
        stopLoading();
        updateSessionUI();
    }
}

function updateSelectedFile() {
    const file = elements.fileInput.files[0];
    elements.uploadSuccess.textContent = "";

    if (!file) {
        elements.fileLabel.textContent = "Drop your document here or click to browse";
        elements.fileMeta.textContent = "After upload, it will appear instantly in your document library and selectors.";
        return;
    }

    elements.fileLabel.textContent = file.name;
    elements.fileMeta.textContent = `${Math.max(1, Math.round(file.size / 1024))} KB selected`;
}

async function uploadDocument() {
    if (!requireSession()) {
        return;
    }

    const file = elements.fileInput.files[0];
    if (!file) {
        setStatus("Please select a PDF before uploading.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const stopLoading = setButtonLoading(elements.uploadBtn, "Uploading...");

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${state.token}`,
            },
            body: formData,
        });
        const data = await parseJsonResponse(response);
        state.documents = Array.isArray(data.documents) ? data.documents : state.documents;
        renderDocumentSelectors();

        if (data.document_name) {
            elements.documentSelect.value = data.document_name;
            elements.flashcardDocumentSelect.value = data.document_name;
            renderDocumentLibrary();
        }

        elements.uploadSuccess.textContent = "Document uploaded successfully.";
        setStatus(`${data.document_name} is ready. Ask questions from it or generate flashcards.`);
        elements.fileInput.value = "";
        updateSelectedFile();
    } catch (error) {
        setStatus(error.message);
    } finally {
        stopLoading();
    }
}

function sanitizeInlineText(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/`(.*?)`/g, "$1")
        .trim();
}

function renderAnswer(answer) {
    const normalized = String(answer || "").trim();
    elements.answerOutput.innerHTML = "";

    if (!normalized) {
        elements.answerOutput.textContent = "No answer returned.";
        return;
    }

    const lines = normalized.split("\n").map((line) => line.trim()).filter(Boolean);
    const numberedLines = lines.filter((line) => /^\d+\./.test(line));
    const bulletLines = lines.filter((line) => /^[-*]\s+/.test(line));

    if (numberedLines.length >= 2 && numberedLines.length === lines.length) {
        const list = document.createElement("ol");
        numberedLines.forEach((line) => {
            const item = document.createElement("li");
            item.textContent = sanitizeInlineText(line.replace(/^\d+\.\s*/, ""));
            list.appendChild(item);
        });
        elements.answerOutput.appendChild(list);
        return;
    }

    if (bulletLines.length >= 2 && bulletLines.length === lines.length) {
        const list = document.createElement("ul");
        bulletLines.forEach((line) => {
            const item = document.createElement("li");
            item.textContent = sanitizeInlineText(line.replace(/^[-*]\s+/, ""));
            list.appendChild(item);
        });
        elements.answerOutput.appendChild(list);
        return;
    }

    normalized
        .split(/\n\s*\n/)
        .map((part) => sanitizeInlineText(part))
        .filter(Boolean)
        .forEach((part) => {
            const paragraph = document.createElement("p");
            paragraph.textContent = part;
            elements.answerOutput.appendChild(paragraph);
        });
}

function renderSources() {
    elements.sourcesList.innerHTML = "";

    if (state.sources.length === 0) {
        elements.toggleSourcesBtn.hidden = true;
        elements.sourcesPanel.hidden = true;
        return;
    }

    elements.toggleSourcesBtn.hidden = false;

    state.sources.forEach((source) => {
        const item = document.createElement("article");
        item.className = "source-item";

        const title = document.createElement("strong");
        title.textContent = source.document_name || "Document";

        const preview = document.createElement("p");
        preview.textContent = source.preview || "";

        item.appendChild(title);
        item.appendChild(preview);
        elements.sourcesList.appendChild(item);
    });
}

async function askQuestion() {
    if (!requireSession()) {
        return;
    }

    const question = elements.queryInput.value.trim();
    if (!question) {
        setStatus("Please enter a question.");
        elements.queryInput.focus();
        return;
    }

    const documentName = elements.documentSelect.value;
    const params = new URLSearchParams({ q: question });
    if (documentName) {
        params.set("document_name", documentName);
    }

    const stopLoading = setButtonLoading(elements.askBtn, "Thinking...");
    elements.answerOutput.textContent = "Generating answer...";
    state.sources = [];
    renderSources();

    try {
        const response = await fetch(`${API_BASE}/query?${params.toString()}`, {
            headers: {
                Authorization: `Bearer ${state.token}`,
            },
        });
        const data = await parseJsonResponse(response);
        renderAnswer(data.answer);
        state.sources = Array.isArray(data.sources) ? data.sources : [];
        renderSources();
        elements.sourcesPanel.hidden = true;
        elements.toggleSourcesBtn.textContent = "Show sources";
        setStatus(documentName ? `Answer generated from ${documentName}.` : "Answer generated from your uploaded library.");
    } catch (error) {
        renderAnswer("Unable to generate an answer right now.");
        setStatus(error.message);
    } finally {
        stopLoading();
    }
}

function updateFlashcardView() {
    const total = state.flashcards.length;

    if (total === 0) {
        elements.flashcardQuestion.textContent = "Generate flashcards to begin your revision stack.";
        elements.flashcardAnswer.textContent = "Click the card to flip it and reveal the answer.";
        elements.flashcardCounter.textContent = "Card 0 of 0";
        elements.flashcardCard.classList.remove("flipped");
        return;
    }

    const current = state.flashcards[state.currentFlashcardIndex];
    elements.flashcardQuestion.textContent = current.question;
    elements.flashcardAnswer.textContent = current.answer;
    elements.flashcardCounter.textContent = `Card ${state.currentFlashcardIndex + 1} of ${total}`;
    elements.flashcardCard.classList.toggle("flipped", state.isFlipped);
}

function setFlashcards(cards) {
    state.flashcards = cards;
    state.currentFlashcardIndex = 0;
    state.isFlipped = false;
    updateFlashcardView();
}

async function generateFlashcards() {
    if (!requireSession()) {
        return;
    }

    const documentName = elements.flashcardDocumentSelect.value;
    const topic = elements.topicInput.value.trim();
    const params = new URLSearchParams();

    if (documentName) {
        params.set("document_name", documentName);
    }

    let url = `${API_BASE}/flashcards`;
    if (topic) {
        params.set("topic", topic);
        url = `${API_BASE}/flashcards/topic`;
    }

    const stopLoading = setButtonLoading(elements.flashcardsBtn, "Creating...");

    try {
        const response = await fetch(`${url}?${params.toString()}`, {
            headers: {
                Authorization: `Bearer ${state.token}`,
            },
        });
        const data = await parseJsonResponse(response);
        const cards = Array.isArray(data.flashcards) ? data.flashcards : [];

        if (cards.length === 0) {
            setFlashcards([]);
            setStatus("No flashcards were generated.");
            return;
        }

        setFlashcards(cards);
        setStatus(topic ? `Flashcards generated for "${topic}".` : "Flashcards generated successfully.");
    } catch (error) {
        setFlashcards([]);
        setStatus(error.message);
    } finally {
        stopLoading();
    }
}

function toggleSources() {
    const shouldShow = elements.sourcesPanel.hidden;
    elements.sourcesPanel.hidden = !shouldShow;
    elements.toggleSourcesBtn.textContent = shouldShow ? "Hide sources" : "Show sources";
}

function toggleFlashcard() {
    if (state.flashcards.length === 0) {
        return;
    }

    state.isFlipped = !state.isFlipped;
    updateFlashcardView();
}

function goToNextCard() {
    if (state.flashcards.length === 0) {
        return;
    }

    state.currentFlashcardIndex = (state.currentFlashcardIndex + 1) % state.flashcards.length;
    state.isFlipped = false;
    updateFlashcardView();
}

function goToPreviousCard() {
    if (state.flashcards.length === 0) {
        return;
    }

    state.currentFlashcardIndex = (state.currentFlashcardIndex - 1 + state.flashcards.length) % state.flashcards.length;
    state.isFlipped = false;
    updateFlashcardView();
}

function setupUploadDragAndDrop() {
    ["dragenter", "dragover"].forEach((eventName) => {
        elements.uploadBox.addEventListener(eventName, (event) => {
            event.preventDefault();
            elements.uploadBox.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        elements.uploadBox.addEventListener(eventName, (event) => {
            event.preventDefault();
            elements.uploadBox.classList.remove("dragover");
        });
    });

    elements.uploadBox.addEventListener("drop", (event) => {
        const [file] = event.dataTransfer.files;
        if (!file) {
            return;
        }

        const transfer = new DataTransfer();
        transfer.items.add(file);
        elements.fileInput.files = transfer.files;
        updateSelectedFile();
    });
}

elements.loginBtn.addEventListener("click", login);
elements.fileInput.addEventListener("change", updateSelectedFile);
elements.uploadBtn.addEventListener("click", uploadDocument);
elements.askBtn.addEventListener("click", askQuestion);
elements.documentSelect.addEventListener("change", renderDocumentLibrary);
elements.flashcardDocumentSelect.addEventListener("change", renderDocumentLibrary);
elements.toggleSourcesBtn.addEventListener("click", toggleSources);
elements.flashcardsBtn.addEventListener("click", generateFlashcards);
elements.flashcardCard.addEventListener("click", toggleFlashcard);
elements.prevCardBtn.addEventListener("click", goToPreviousCard);
elements.nextCardBtn.addEventListener("click", goToNextCard);

setupUploadDragAndDrop();
loadSession();
renderDocumentSelectors();
updateSelectedFile();
updateFlashcardView();

if (state.token) {
    fetchDocuments().catch(() => {
        setStatus("Session restored, but document sync failed. Log in again if needed.");
    });
}
