import { marked } from 'marked';

marked.setOptions({
  breaks: true,
  gfm: true,
});

const chat = document.getElementById('chat');
const form = document.getElementById('form');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const chatsList = document.getElementById('chats-list');
const newChatBtn = document.getElementById('new-chat-btn');

let ws = null;
let isStreaming = false;
let currentMessageEl = null;
let currentChatId = null;

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function renderMarkdown(text) {
  const escaped = escapeHtml(text);
  return marked.parse(escaped);
}

function getWsUrl() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${location.host}/ws/${currentChatId}`;
}

function connect() {
  ws = new WebSocket(getWsUrl());

  ws.onopen = () => {
    console.log('connected');
  };

  ws.onmessage = (event) => {
    const data = event.data;

    if (data === '[END]') {
      isStreaming = false;
      currentMessageEl = null;
      sendBtn.disabled = !input.value.trim();
      return;
    }

    if (!isStreaming) {
      isStreaming = true;
      currentMessageEl = addMessage('assistant', '', true);
    }

    appendChunk(currentMessageEl, data);
  };

  ws.onclose = () => {
    if (isStreaming) {
      isStreaming = false;
      currentMessageEl = null;
    }
  };

  ws.onerror = () => {
    ws.close();
  };
}

function addMessage(role, content, isStreaming_) {
  const welcome = chat.querySelector('.welcome-message');
  if (welcome) welcome.remove();

  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (isStreaming_) div.classList.add('typing');

  const contentDiv = document.createElement('div');
  contentDiv.className = 'content';

  if (role === 'assistant' && content) {
    contentDiv.innerHTML = renderMarkdown(content);
  } else {
    contentDiv.textContent = content;
  }

  div.appendChild(contentDiv);
  chat.appendChild(div);
  scrollToBottom();
  return div;
}

function appendChunk(messageEl, chunk) {
  if (!messageEl._raw) messageEl._raw = '';
  messageEl._raw += chunk;

  const contentDiv = messageEl.querySelector('.content');
  contentDiv.innerHTML = renderMarkdown(messageEl._raw);
  messageEl.classList.remove('typing');

  if (!isStreaming) {
    messageEl._raw = null;
  }

  scrollToBottom();
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    chat.scrollTop = chat.scrollHeight;
  });
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || isStreaming) return;

  addMessage('user', text);
  sendBtn.disabled = true;
  input.value = '';
  input.style.height = 'auto';

  if (!currentChatId) {
    const response = await fetch('/chats', { method: 'POST' });
    currentChatId = await response.json();
    await loadChats();
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connect();
    await new Promise((resolve) => {
      ws.onopen = () => {
        console.log('connected');
        resolve();
      };
    });
  }

  ws.send(text);
}

async function loadChats() {
  const response = await fetch('/chats');
  const chats = await response.json();
  renderChats(chats);
}

function renderChats(chats) {
  chatsList.innerHTML = '';
  for (const chat of chats) {
    const item = document.createElement('div');
    item.className = 'chat-item';
    if (chat.id === currentChatId) {
      item.classList.add('active');
    }
    item.innerHTML = `<span class="chat-item-icon">💬</span>${chat.title || chat.id}`;
    item.addEventListener('click', () => selectChat(chat.id));
    chatsList.appendChild(item);
  }
}

function selectChat(chatId) {
  if (ws) {
    ws.close();
    ws = null;
  }
  currentChatId = chatId;
  chat.innerHTML = `
    <div class="welcome-message">
      <div class="welcome-icon">✦</div>
      <p>Я — ваш AI-ассистент. Задайте мне любой вопрос.</p>
    </div>
  `;
  isStreaming = false;
  currentMessageEl = null;
  loadChats();
}

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  sendBtn.disabled = !input.value.trim() || isStreaming;
});

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

form.addEventListener('submit', (e) => {
  e.preventDefault();
  sendMessage();
});

newChatBtn.addEventListener('click', () => {
  if (ws) {
    ws.close();
    ws = null;
  }
  currentChatId = null;
  isStreaming = false;
  currentMessageEl = null;
  chat.innerHTML = `
    <div class="welcome-message">
      <div class="welcome-icon">✦</div>
      <p>Я — ваш AI-ассистент. Задайте мне любой вопрос.</p>
    </div>
  `;
  document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
});

loadChats();
