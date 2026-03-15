const stateUrl = "/api/state";
const chatUrl = "/api/chat";
const resetUrl = "/api/reset";
const parsedResumeUrl = "/api/parsed-resume";

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const inputMode = document.getElementById("input-mode");
const composerHint = document.getElementById("composer-hint");
const portfolioFrame = document.getElementById("portfolio-frame");
const htmlPath = document.getElementById("html-path");
const urlSummaries = document.getElementById("url-summaries");
const resumeOutput = document.getElementById("resume-output");
const resetButton = document.getElementById("reset-session");
const template = document.getElementById("message-template");

function modeLabel(mode) {
  if (mode === "rating") {
    return "Awaiting rating";
  }
  if (mode === "revision") {
    return "Awaiting revision feedback";
  }
  if (mode === "complete") {
    return "Session complete";
  }
  return "Chatting";
}

function modeHint(mode) {
  if (mode === "rating") {
    return "Submit only a number from 1 to 10.";
  }
  if (mode === "revision") {
    return "Explain the changes you want. You can include 1-3 inspiration URLs.";
  }
  if (mode === "complete") {
    return "The workflow ended. Reset the session to start another run.";
  }
  return "Ask for a portfolio, paste resume text, or refine the current direction.";
}

function renderMessages(messages) {
  chatLog.innerHTML = "";

  if (!messages.length) {
    const empty = document.createElement("article");
    empty.className = "message system";
    empty.innerHTML = `
      <p class="message-role">System</p>
      <p class="message-body">No conversation yet. Start with your resume or describe the portfolio you want.</p>
    `;
    chatLog.appendChild(empty);
    return;
  }

  messages.forEach((message) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.classList.add(message.role);
    node.querySelector(".message-role").textContent = message.role;

    const body = node.querySelector(".message-body");
    body.textContent = message.content;

    if (message.parsed_resume) {
      const marker = document.createElement("p");
      marker.className = "message-body";
      marker.textContent = "Structured resume data was saved for this step.";
      node.appendChild(marker);
    }

    chatLog.appendChild(node);
  });

  chatLog.scrollTop = chatLog.scrollHeight;
}

function renderSummaries(summaries) {
  if (!summaries.length) {
    urlSummaries.className = "summary-list empty-state";
    urlSummaries.textContent = "No inspiration URLs used yet.";
    return;
  }

  urlSummaries.className = "summary-list";
  urlSummaries.innerHTML = "";
  summaries.forEach((item) => {
    const wrapper = document.createElement("article");
    wrapper.className = "summary-item";
    wrapper.innerHTML = `<h3>${item.url}</h3><p>${item.summary}</p>`;
    urlSummaries.appendChild(wrapper);
  });
}

function renderPortfolio(artifacts) {
  if (artifacts.html_content) {
    portfolioFrame.srcdoc = artifacts.html_content;
    htmlPath.textContent = artifacts.html_path || "Generated HTML available";
    return;
  }

  portfolioFrame.srcdoc = `
    <html>
      <body style="font-family: sans-serif; display: grid; place-items: center; height: 100vh; color: #6c6259; background: #fcf8f1;">
        No portfolio HTML generated yet.
      </body>
    </html>
  `;
  htmlPath.textContent = "No saved HTML yet.";
}

async function renderParsedResume() {
  const response = await fetch(parsedResumeUrl);
  const data = await response.json();

  if (!data.exists) {
    resumeOutput.textContent = "No parsed resume saved yet.";
    resumeOutput.classList.add("empty-state");
    return;
  }

  resumeOutput.textContent = JSON.stringify(data.content, null, 2);
  resumeOutput.classList.remove("empty-state");
}

async function renderState(state) {
  renderMessages(state.messages);
  renderSummaries(state.artifacts.url_summaries || []);
  renderPortfolio(state.artifacts || {});
  await renderParsedResume();

  inputMode.textContent = modeLabel(state.input_mode);
  composerHint.textContent = modeHint(state.input_mode);
  messageInput.placeholder = state.placeholder;
  messageInput.disabled = state.completed;
  sendButton.disabled = state.completed;
}

async function refreshState() {
  const response = await fetch(stateUrl);
  const state = await response.json();
  await renderState(state);
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  messageInput.disabled = true;
  sendButton.disabled = true;
  composerHint.textContent = "Working...";

  const response = await fetch(chatUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  const payload = await response.json();
  messageInput.value = "";
  await renderState(payload.state);
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }

  event.preventDefault();
  chatForm.requestSubmit();
});

resetButton.addEventListener("click", async () => {
  const response = await fetch(resetUrl, { method: "POST" });
  const state = await response.json();
  messageInput.value = "";
  await renderState(state);
});

refreshState();
