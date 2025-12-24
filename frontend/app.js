// API URL - always use localhost:8000 for now (can be configured for production later)
const API_URL = 'http://localhost:8000';

// Conversation history
let messages = [];

// Current user
let currentUser = null;

// Prevent double-send
let isSending = false;

// DOM elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const userSelectionScreen = document.getElementById('userSelectionScreen');
const mainContainer = document.getElementById('mainContainer');
const usersGrid = document.getElementById('usersGrid');
const currentUserName = document.getElementById('currentUserName');
const changeUserBtn = document.getElementById('changeUserBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Use keydown + preventDefault to avoid duplicate sends
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  });

  sendButton.addEventListener('click', sendMessage);
  changeUserBtn.addEventListener('click', showUserSelection);

  // Load users on startup
  loadUsers();
});

// User Selection Functions
async function loadUsers() {
  try {
    const response = await fetch(`${API_URL}/users`);
    const data = await response.json();

    if (data.success && data.users) {
      displayUsers(data.users);
    } else {
      usersGrid.innerHTML = '<div class="loading">Error loading users</div>';
    }
  } catch (error) {
    console.error('Error loading users:', error);
    usersGrid.innerHTML = '<div class="loading">Error loading users</div>';
  }
}

function displayUsers(users) {
  usersGrid.innerHTML = '';

  users.forEach(user => {
    const userCard = document.createElement('div');
    userCard.className = 'user-card';
    userCard.onclick = () => selectUser(user);

    userCard.innerHTML = `
      <div class="user-card-icon">👤</div>
      <div class="user-card-name">${user.name}</div>
      <div class="user-card-email">${user.email}</div>
    `;

    usersGrid.appendChild(userCard);
  });
}

function selectUser(user) {
  currentUser = user;
  currentUserName.textContent = user.name;

  // Hide user selection, show main chat
  userSelectionScreen.style.display = 'none';
  mainContainer.style.display = 'block';

  // Reset conversation
  messages = [];
  messagesContainer.innerHTML = '';

  // Add welcome message
  addWelcomeMessage(user.name);
}

function showUserSelection() {
  // Show user selection screen
  userSelectionScreen.style.display = 'flex';
  mainContainer.style.display = 'none';

  // Reset current user
  currentUser = null;
  currentUserName.textContent = '';
}

function addWelcomeMessage(userName) {
  const welcomeMessage = `Hello ${userName}! 👋

Welcome to the Pharmacy AI Assistant. I'm here to help you with questions about medications, prescriptions, and inventory.

You can ask me in English or Hebrew.

How can I help you today?`;

  addMessage('assistant', welcomeMessage);
}

async function sendMessage() {
  if (isSending) return;

  const message = userInput.value.trim();
  if (!message) return;

  isSending = true;

  // Disable input
  userInput.disabled = true;
  sendButton.disabled = true;

  // Add user message to UI
  addMessage('user', message);

  // If this is the first message, add user context
  if (messages.length === 0 && currentUser) {
    messages.push({
      role: 'user',
      content: `[User Context: I am ${currentUser.name}, user_id: ${currentUser.id}]`
    });
  }

  // Add to conversation history
  messages.push({
    role: 'user',
    content: message
  });

  // Clear input
  userInput.value = '';

  // Show typing indicator
  const typingEl = addTypingIndicator();

  try {
    await streamChat(typingEl);
  } catch (error) {
    console.error('Error:', error);
    removeTypingIndicator(typingEl);
    addMessage('assistant', 'Sorry, an error occurred. Please try again.');
  } finally {
    // Re-enable input
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
    isSending = false;
  }
}

async function streamChat(typingEl) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, model: 'gpt-5' })
  });

  if (!response.ok) throw new Error('Network response was not ok');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let sseBuffer = '';
  let assistantMessage = '';
  let currentMessageElement = null;

  let toolCalls = [];
  let toolResults = [];

  let hasStartedContent = false;
  let finalized = false;
  let typingRemoved = false;

  const removeTypingOnce = () => {
    if (typingRemoved) return;
    removeTypingIndicator(typingEl);
    // Safety: remove any leftover typing indicators
    document.querySelectorAll('[data-typing="true"]').forEach(el => el.remove());
    typingRemoved = true;
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    sseBuffer += decoder.decode(value, { stream: true });

    // SSE events are separated by blank line
    const events = sseBuffer.split('\n\n');
    sseBuffer = events.pop(); // incomplete remainder

    for (const evt of events) {
      const dataLines = evt
        .split('\n')
        .filter(l => l.startsWith('data:'))
        .map(l => l.slice(5).trim());

      const dataStr = dataLines.join('\n');
      if (!dataStr) continue;

      let parsed;
      try {
        parsed = JSON.parse(dataStr);
      } catch {
        // Incomplete JSON: push back
        sseBuffer = dataStr + '\n\n' + sseBuffer;
        continue;
      }

      if (parsed.type === 'content') {
        if (!hasStartedContent) {
          removeTypingOnce();
          currentMessageElement = createAssistantMessage();
          hasStartedContent = true;
        }

        assistantMessage += parsed.content;
        updateMessageContent(currentMessageElement, assistantMessage);

      } else if (parsed.type === 'tool_call') {
        const tc = parsed.tool_call;
        if (tc?.id && tc?.function?.name) {
          if (!toolCalls.find(x => x.id === tc.id)) toolCalls.push(tc);
        }

      } else if (parsed.type === 'tool_result') {
        toolResults.push(parsed);

      } else if (parsed.type === 'done' || parsed.type === 'complete') {
        if (finalized) continue;
        finalized = true;

        // If no content ever arrived, still remove typing and show an empty assistant bubble
        if (!hasStartedContent) {
          removeTypingOnce();
          currentMessageElement = createAssistantMessage();
          hasStartedContent = true;
        }

        if (assistantMessage) {
          messages.push({ role: 'assistant', content: assistantMessage });
        }

        if (currentMessageElement && toolCalls.length > 0) {
          displayDevModeAfterResponse(currentMessageElement, toolCalls, toolResults);
        }

      } else if (parsed.type === 'error') {
        if (!hasStartedContent) {
          removeTypingOnce();
          currentMessageElement = createAssistantMessage();
          hasStartedContent = true;
        }
        addErrorToMessage(currentMessageElement, parsed.error);
      }
    }
  }

  scrollToBottom();
}

function addMessage(role, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.innerHTML = formatMessage(content);

  // Apply RTL if content is in Hebrew
  applyRTLIfNeeded(contentDiv, content);

  messageDiv.appendChild(contentDiv);
  messagesContainer.appendChild(messageDiv);

  scrollToBottom();
  return messageDiv;
}

function createAssistantMessage() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  // Fixed container for assistant text (always first)
  const textDiv = document.createElement('div');
  textDiv.className = 'assistant-text';
  contentDiv.appendChild(textDiv);

  messageDiv.appendChild(contentDiv);
  messagesContainer.appendChild(messageDiv);

  scrollToBottom();
  return messageDiv;
}

function updateMessageContent(messageElement, content) {
  const contentDiv = messageElement.querySelector('.message-content');
  const textDiv = contentDiv.querySelector('.assistant-text');

  textDiv.innerHTML = formatMessage(content);
  applyRTLIfNeeded(textDiv, content);

  scrollToBottom();
}

function addTypingIndicator() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  messageDiv.dataset.typing = 'true';

  const typingDiv = document.createElement('div');
  typingDiv.className = 'typing-indicator';
  typingDiv.innerHTML = '<span></span><span></span><span></span>';

  messageDiv.appendChild(typingDiv);
  messagesContainer.appendChild(messageDiv);

  scrollToBottom();
  return messageDiv;
}

function removeTypingIndicator(typingEl) {
  if (typingEl && typingEl.parentNode) {
    typingEl.parentNode.removeChild(typingEl);
  }
}

function addErrorToMessage(messageElement, error) {
  const contentDiv = messageElement.querySelector('.message-content');
  const textDiv = contentDiv.querySelector('.assistant-text');
  textDiv.innerHTML = `<p style="color: red;">Error: ${error}</p>`;
}

function formatMessage(text) {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

function isHebrewText(text) {
  return /[\u0590-\u05FF]/.test(text);
}

function applyRTLIfNeeded(element, text) {
  if (isHebrewText(text)) element.classList.add('rtl');
  else element.classList.remove('rtl');
}

function displayDevModeAfterResponse(messageElement, toolCalls, toolResults) {
  const toolsContainer = document.createElement('div');
  toolsContainer.className = 'tools-container';
  toolsContainer.style.cssText = 'margin-top: 20px;';

  const header = document.createElement('div');
  header.className = 'tools-container-header';
  header.innerHTML = '⚙️ Developer Mode';
  toolsContainer.appendChild(header);

  toolCalls.forEach(toolCall => {
    const toolDiv = document.createElement('div');
    toolDiv.className = 'tool-call';

    const functionName = toolCall.function.name;
    let args = {};
    try {
      if (toolCall.function.arguments) {
        args = JSON.parse(toolCall.function.arguments);
      }
    } catch {}

    toolDiv.innerHTML = `
      <div class="tool-call-header">🔧 ${functionName}</div>
      <div class="tool-call-args">${JSON.stringify(args, null, 2)}</div>
    `;

    toolsContainer.appendChild(toolDiv);

    const result = toolResults.find(r => r.tool_call_id === toolCall.id);
    if (result) {
      const resultDiv = document.createElement('div');
      resultDiv.className = 'tool-result';

      resultDiv.innerHTML = `
        <div class="tool-result-header">✅ Result</div>
        <div class="tool-result-content">${JSON.stringify(result.result, null, 2)}</div>
      `;

      toolsContainer.appendChild(resultDiv);
    }
  });

  messageElement.querySelector('.message-content').appendChild(toolsContainer);
  scrollToBottom();
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
