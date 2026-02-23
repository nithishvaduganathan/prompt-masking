/* ==========================================================================
   PromptShield — Frontend Application Logic
   ========================================================================== */

; (function () {
    'use strict';

    // ---- DOM References ----
    const sidebar = document.getElementById('sidebar');
    const conversationList = document.getElementById('conversationList');
    const btnNewChat = document.getElementById('btnNewChat');
    const btnToggleSidebar = document.getElementById('btnToggleSidebar');
    const welcome = document.getElementById('welcome');
    const chatContainer = document.getElementById('chatContainer');
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const btnSend = document.getElementById('btnSend');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const maskingToggle = document.getElementById('maskingToggle');
    const maskingHint = document.getElementById('maskingHint');

    // ---- State ----
    let currentConversationId = null;
    let isProcessing = false;
    let maskingEnabled = true;

    // ---- Masking Toggle ----
    maskingToggle.addEventListener('change', () => {
        maskingEnabled = maskingToggle.checked;
        if (maskingEnabled) {
            maskingHint.innerHTML = 'PII masking is <strong>ON</strong>';
            maskingHint.classList.remove('off');
            messageInput.placeholder = 'Type your message… your PII will be masked automatically';
        } else {
            maskingHint.innerHTML = 'PII masking is <strong>OFF</strong> — direct to Gemini';
            maskingHint.classList.add('off');
            messageInput.placeholder = 'Type your message… sending directly to Gemini (no masking)';
        }
    });

    // ---- Helpers ----
    const API = (path, opts = {}) =>
        fetch(path, {
            headers: { 'Content-Type': 'application/json', ...opts.headers },
            ...opts,
        }).then(r => r.json());

    // Simple markdown → HTML (handles **bold**, *italic*, `code`, ```blocks```, links, lists, headers)
    function renderMarkdown(text) {
        if (!text) return '';
        let html = text;

        // Code blocks (``` ... ```)
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
            const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return `<pre><code class="language-${lang}">${escaped}</code></pre>`;
        });

        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headers
        html = html.replace(/^######\s+(.*)$/gm, '<h6>$1</h6>');
        html = html.replace(/^#####\s+(.*)$/gm, '<h5>$1</h5>');
        html = html.replace(/^####\s+(.*)$/gm, '<h4>$1</h4>');
        html = html.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
        html = html.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
        html = html.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');

        // Bold and italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Blockquotes
        html = html.replace(/^>\s+(.*)$/gm, '<blockquote>$1</blockquote>');

        // Horizontal rules
        html = html.replace(/^---$/gm, '<hr>');

        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

        // Unordered lists
        html = html.replace(/(?:^|\n)((?:[-*]\s+.*\n?)+)/g, (_, block) => {
            const items = block.trim().split('\n').map(line =>
                `<li>${line.replace(/^[-*]\s+/, '')}</li>`
            ).join('');
            return `<ul>${items}</ul>`;
        });

        // Ordered lists
        html = html.replace(/(?:^|\n)((?:\d+\.\s+.*\n?)+)/g, (_, block) => {
            const items = block.trim().split('\n').map(line =>
                `<li>${line.replace(/^\d+\.\s+/, '')}</li>`
            ).join('');
            return `<ol>${items}</ol>`;
        });

        // Tables
        html = html.replace(/(?:^|\n)(\|.+\|(?:\n\|[-:| ]+\|)?(?:\n\|.+\|)*)/g, (_, table) => {
            const rows = table.trim().split('\n').filter(r => !/^[-:| ]+$/.test(r.replace(/\|/g, '').trim()) || r.includes('-'));
            const dataRows = rows.filter(r => !/^\|[\s:-]+\|$/.test(r));
            if (dataRows.length < 1) return table;

            let tableHtml = '<table>';
            dataRows.forEach((row, i) => {
                const cells = row.split('|').filter(c => c.trim() !== '');
                const tag = i === 0 ? 'th' : 'td';
                const rowTag = i === 0 ? 'thead' : (i === 1 ? 'tbody>' : '');
                if (i === 0) tableHtml += '<thead>';
                if (i === 1) tableHtml += '<tbody>';
                tableHtml += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
                if (i === 0) tableHtml += '</thead>';
            });
            tableHtml += '</tbody></table>';
            return tableHtml;
        });

        // Paragraphs — wrap remaining loose text
        html = html.replace(/^(?!<[a-z])(.*\S.*)$/gm, '<p>$1</p>');

        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');

        return html;
    }

    // ---- Textarea auto-resize ----
    function autoResizeInput() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
        btnSend.disabled = !messageInput.value.trim() || isProcessing;
    }

    messageInput.addEventListener('input', autoResizeInput);

    // ---- Keyboard shortcut ----
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!btnSend.disabled) sendMessage();
        }
    });

    // ---- Send button ----
    btnSend.addEventListener('click', () => {
        if (!btnSend.disabled) sendMessage();
    });

    // ---- New chat ----
    btnNewChat.addEventListener('click', () => {
        currentConversationId = null;
        showWelcome();
        closeSidebarMobile();
    });

    // ---- Sidebar toggle (mobile) ----
    btnToggleSidebar.addEventListener('click', toggleSidebar);

    // ========================================================================
    // Core Functions
    // ========================================================================

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || isProcessing) return;

        isProcessing = true;
        btnSend.disabled = true;
        messageInput.value = '';
        autoResizeInput();

        // Show chat area
        showChat();

        // Add user message to UI
        appendMessage('user', message);

        // Show typing indicator
        const typingEl = showTyping();

        try {
            const result = await API('/api/chat', {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    conversation_id: currentConversationId,
                    masking_enabled: maskingEnabled,
                }),
            });

            // Remove typing indicator
            typingEl.remove();

            if (result.error) {
                appendMessage('assistant', `⚠️ ${result.error}`);
            } else {
                currentConversationId = result.conversation_id;
                appendMessage('assistant', result.response, result.masking_info);
            }

            // Refresh sidebar
            loadConversations();
        } catch (err) {
            typingEl.remove();
            appendMessage('assistant', `⚠️ Network error — please check if the server is running.\n\n\`${err.message}\``);
        }

        isProcessing = false;
        btnSend.disabled = !messageInput.value.trim();
        messageInput.focus();
    }

    function appendMessage(role, content, maskingInfo = null) {
        const div = document.createElement('div');
        div.className = 'message';

        const avatarLabel = role === 'user' ? 'Y' : 'S';
        const roleLabel = role === 'user' ? 'You' : 'PromptShield';

        let maskingHtml = '';
        if (maskingInfo && maskingInfo.items_masked > 0) {
            const detailsId = 'mask-' + Date.now();
            const items = maskingInfo.placeholders.map(p =>
                `<div class="masked-item"><span class="placeholder">${escHtml(p)}</span> <span class="arrow">→</span> <span class="original">***</span></div>`
            ).join('');

            maskingHtml = `
                <div class="masking-badge" onclick="document.getElementById('${detailsId}').classList.toggle('show')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                    ${maskingInfo.items_masked} item${maskingInfo.items_masked > 1 ? 's' : ''} masked
                </div>
                <div class="masking-details" id="${detailsId}">${items}</div>
            `;
        }

        div.innerHTML = `
            <div class="message-avatar ${role}">${avatarLabel}</div>
            <div class="message-body">
                <div class="message-role">${roleLabel}</div>
                <div class="message-content">${renderMarkdown(content)}</div>
                ${maskingHtml}
            </div>
        `;

        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.innerHTML = `
            <div class="message-avatar assistant">S</div>
            <div class="message-body">
                <div class="message-role">PromptShield</div>
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(div);
        scrollToBottom();
        return div;
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    // ========================================================================
    // View Switching
    // ========================================================================

    function showWelcome() {
        welcome.style.display = '';
        chatContainer.style.display = 'none';
        chatMessages.innerHTML = '';
        highlightActiveConversation();
    }

    function showChat() {
        welcome.style.display = 'none';
        chatContainer.style.display = '';
    }

    // ========================================================================
    // Conversations
    // ========================================================================

    async function loadConversations() {
        try {
            const convs = await API('/api/conversations');
            renderConversationList(convs);
        } catch {
            // Silently fail on load
        }
    }

    function renderConversationList(convs) {
        conversationList.innerHTML = '';
        convs.forEach(c => {
            const el = document.createElement('div');
            el.className = 'conv-item' + (c.id === currentConversationId ? ' active' : '');
            el.innerHTML = `
                <span class="conv-item-title">${escHtml(c.title)}</span>
                <button class="conv-item-delete" title="Delete" data-id="${c.id}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
            `;

            // Click to open conversation
            el.addEventListener('click', (e) => {
                if (e.target.closest('.conv-item-delete')) return;
                openConversation(c.id);
                closeSidebarMobile();
            });

            // Delete button
            el.querySelector('.conv-item-delete').addEventListener('click', async (e) => {
                e.stopPropagation();
                await API(`/api/conversations/${c.id}`, { method: 'DELETE' });
                if (c.id === currentConversationId) {
                    currentConversationId = null;
                    showWelcome();
                }
                loadConversations();
            });

            conversationList.appendChild(el);
        });
    }

    function highlightActiveConversation() {
        document.querySelectorAll('.conv-item').forEach(el => {
            el.classList.toggle('active', false);
        });
    }

    async function openConversation(id) {
        try {
            const data = await API(`/api/conversations/${id}`);
            if (!data || data.error) return;
            currentConversationId = id;
            chatMessages.innerHTML = '';
            showChat();

            (data.messages || []).forEach(msg => {
                appendMessage(msg.role, msg.content);
            });

            highlightActiveConversation();
            document.querySelectorAll('.conv-item').forEach(el => {
                const btn = el.querySelector('[data-id]');
                if (btn && btn.dataset.id === id) el.classList.add('active');
            });
        } catch {
            // Fail silently
        }
    }

    // ========================================================================
    // Sidebar (mobile)
    // ========================================================================

    let overlay = null;

    function toggleSidebar() {
        const isOpen = sidebar.classList.toggle('open');
        if (isOpen) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay show';
                overlay.addEventListener('click', closeSidebarMobile);
                document.body.appendChild(overlay);
            } else {
                overlay.classList.add('show');
            }
        } else {
            closeSidebarMobile();
        }
    }

    function closeSidebarMobile() {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('show');
    }

    // ========================================================================
    // Health Check
    // ========================================================================

    async function checkHealth() {
        try {
            const data = await API('/api/health');
            const ok = data.status === 'ok';
            statusDot.className = 'status-dot ' + (ok ? 'ok' : 'error');
            const parts = [];
            parts.push(`Ollama: ${data.ollama}`);
            parts.push(`Gemini: ${data.gemini}`);
            statusText.textContent = parts.join(' · ');
        } catch {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Server unreachable';
        }
    }

    // ========================================================================
    // Init
    // ========================================================================

    loadConversations();
    checkHealth();
    setInterval(checkHealth, 30000); // Re-check every 30s
    messageInput.focus();

})();
