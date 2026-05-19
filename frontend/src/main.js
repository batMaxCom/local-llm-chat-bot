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
let isLoadingMessages = false;
let hasMoreMessages = true;
let oldestMessageId = null;
let pageSize = 10;

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

function calcPageSize() {
  const h = chat.clientHeight || 600;
  return Math.max(10, Math.ceil(h / 60) + 5);
}

function createMessageEl(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const contentDiv = document.createElement('div');
  contentDiv.className = 'content';
  if (role === 'assistant' && content) {
    contentDiv.innerHTML = renderMarkdown(content);
  } else {
    contentDiv.textContent = content;
  }
  div.appendChild(contentDiv);
  return div;
}

async function loadMessages(chatId, beforeId) {
  const params = new URLSearchParams({ session_id: chatId, limit: pageSize });
  if (beforeId) params.set('before_id', beforeId);
  const response = await fetch(`/message?${params}`);
  return await response.json();
}

const BATCHES_TO_LOAD = 3;

async function loadBatches(count) {
  if (!currentChatId) return false;
  let loadedAny = false;
  let currentBeforeId = oldestMessageId;
  let allMessages = [];

  for (let i = 0; i < count && hasMoreMessages; i++) {
    const data = await loadMessages(currentChatId, currentBeforeId);
    if (!data || data.length === 0) {
      hasMoreMessages = false;
      break;
    }
    loadedAny = true;
    currentBeforeId = data[0].id;
    if (data.length < pageSize) hasMoreMessages = false;
    allMessages = [...data, ...allMessages];
  }

  if (!loadedAny) return false;
  oldestMessageId = currentBeforeId;

  const frag = document.createDocumentFragment();
  for (const m of allMessages) {
    frag.appendChild(createMessageEl(m.role, m.content));
  }

  const prevHeight = chat.scrollHeight;
  chat.insertBefore(frag, chat.firstChild);
  chat.scrollTop = chat.scrollHeight - prevHeight;
  return true;
}

async function selectChat(chatId) {
  if (ws) {
    ws.close();
    ws = null;
  }
  currentChatId = chatId;
  isStreaming = false;
  currentMessageEl = null;
  isLoadingMessages = false;
  hasMoreMessages = true;
  oldestMessageId = null;
  pageSize = calcPageSize();

  chat.innerHTML = '';
  chat.scrollTop = 0;

  try {
    const data = await loadMessages(chatId);

    if (data && data.length > 0) {
      oldestMessageId = data[0].id;
      if (data.length < pageSize) hasMoreMessages = false;
      const frag = document.createDocumentFragment();
      for (const m of data) {
        frag.appendChild(createMessageEl(m.role, m.content));
      }
      chat.appendChild(frag);
    } else {
      chat.innerHTML = `
        <div class="welcome-message">
          <div class="welcome-icon">✦</div>
          <p>Я — ваш AI-ассистент. Задайте мне любой вопрос.</p>
        </div>
      `;
    }
  } catch {
    chat.innerHTML = `
      <div class="welcome-message">
        <div class="welcome-icon">✦</div>
        <p>Не удалось загрузить сообщения.</p>
      </div>
    `;
  }

  chat.scrollTop = chat.scrollHeight;
  setupScrollObserver();
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

let scrollObserver = null;
let observerReady = false;

function setupScrollObserver() {
  if (scrollObserver) scrollObserver.disconnect();
  const sentinel = document.createElement('div');
  sentinel.className = 'scroll-sentinel';
  chat.insertBefore(sentinel, chat.firstChild);
  const observer = new IntersectionObserver(async ([entry]) => {
    if (entry.isIntersecting && observerReady && !isLoadingMessages && currentChatId && hasMoreMessages) {
      isLoadingMessages = true;
      try {
        await loadBatches(BATCHES_TO_LOAD);
        chat.insertBefore(sentinel, chat.firstChild);
      } catch {}
      isLoadingMessages = false;
    }
  }, { root: chat, threshold: 0 });
  observer.observe(sentinel);
  scrollObserver = observer;
  observerReady = false;
  setTimeout(() => { observerReady = true; }, 200);
}

newChatBtn.addEventListener('click', () => {
  if (scrollObserver) scrollObserver.disconnect();
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
