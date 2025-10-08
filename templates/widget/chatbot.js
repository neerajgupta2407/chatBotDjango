// Client Configuration (injected by Django)
const WIDGET_CONFIG = {
    apiKey: '{{ api_key }}',
    apiBaseUrl: '{{ api_base_url }}',
    botName: '{{ bot_name|escapejs }}',
    botColor: '{{ bot_color }}',
    botMsgBgColor: '{{ bot_msg_bg_color }}',
    botIconUrl: '{{ bot_icon_url }}',
    poweredByText: '{{ powered_by_text|escapejs }}',
    userIdentifier: '{{ user_identifier|escapejs }}'
};

class ClaudeChatWidget {
    constructor() {
        this.sessionId = null;
        this.config = {};
        this.apiBaseUrl = WIDGET_CONFIG.apiBaseUrl;
        this.apiKey = WIDGET_CONFIG.apiKey;
        this.isMinimized = true;
        this.messageQueue = [];
        this.isProcessing = false;
        this.currentProvider = 'claude';
        this.currentProviderName = WIDGET_CONFIG.botName;
        this.userIdentifier = this.getUserIdentifier();
        this.botConfig = {
            botName: WIDGET_CONFIG.botName,
            botColor: WIDGET_CONFIG.botColor,
            botMsgBgColor: WIDGET_CONFIG.botMsgBgColor,
            botIcon: WIDGET_CONFIG.botIconUrl,
            poweredBy: WIDGET_CONFIG.poweredByText
        };

        // Apply client colors immediately to avoid flash
        this.applyClientBranding();

        this.initializeElements();

        // Verify critical elements exist before proceeding
        if (!this.elements.container || !this.elements.messageInput) {
            console.error('Critical DOM elements missing. Widget cannot initialize.');
            return;
        }

        this.attachEventListeners();
        this.setupCrossOriginCommunication();
        this.initializeSession();
        this.updateWelcomeTime();

        // Start minimized by default
        this.toggleMinimize(true);
    }

    applyClientBranding() {
        // Apply bot colors immediately
        if (this.botConfig.botColor) {
            this.applyBotColors(this.botConfig.botColor);
        }

        // Apply message background color
        if (this.botConfig.botMsgBgColor) {
            this.applyMessageBgColor(this.botConfig.botMsgBgColor);
        }
    }

    getApiKey() {
        // Return embedded API key
        return WIDGET_CONFIG.apiKey;
    }

    getApiBaseUrl() {
        // Return embedded API base URL
        return WIDGET_CONFIG.apiBaseUrl;
    }

    getUserIdentifier() {
        // Try to get user identifier from URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        let userIdentifier = urlParams.get('userIdentifier');

        if (userIdentifier) {
            // Store in localStorage for persistence
            try {
                localStorage.setItem('chatbot_user_identifier', userIdentifier);
            } catch (e) {
                console.warn('Failed to store user identifier in localStorage:', e);
            }
            return userIdentifier;
        }

        // Try to get from localStorage
        try {
            userIdentifier = localStorage.getItem('chatbot_user_identifier');
            if (userIdentifier) {
                return userIdentifier;
            }
        } catch (e) {
            console.warn('Failed to read user identifier from localStorage:', e);
        }

        // Generate a new UUID if not found
        userIdentifier = this.generateUUID();

        // Try to store it for future sessions
        try {
            localStorage.setItem('chatbot_user_identifier', userIdentifier);
        } catch (e) {
            console.warn('Failed to store generated user identifier:', e);
        }

        return userIdentifier;
    }

    generateUUID() {
        // Simple UUID v4 generator
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    loadConfigFromURL() {
        // Config is now embedded in the JavaScript, no need to parse from URL
        // This method is kept for backward compatibility but does nothing
    }

    darkenColor(color, percent) {
        // Convert hex to RGB, darken, and convert back
        const hex = color.replace('#', '').replace(/'/g, '');
        const r = Math.max(0, parseInt(hex.substr(0, 2), 16) * (1 - percent / 100));
        const g = Math.max(0, parseInt(hex.substr(2, 2), 16) * (1 - percent / 100));
        const b = Math.max(0, parseInt(hex.substr(4, 2), 16) * (1 - percent / 100));
        return `rgb(${Math.floor(r)}, ${Math.floor(g)}, ${Math.floor(b)})`;
    }

    lightenColor(color, percent) {
        // Convert hex to RGB, lighten, and convert back
        const hex = color.replace('#', '').replace(/'/g, '');
        const r = Math.min(255, parseInt(hex.substr(0, 2), 16) + (255 - parseInt(hex.substr(0, 2), 16)) * percent / 100);
        const g = Math.min(255, parseInt(hex.substr(2, 2), 16) + (255 - parseInt(hex.substr(2, 2), 16)) * percent / 100);
        const b = Math.min(255, parseInt(hex.substr(4, 2), 16) + (255 - parseInt(hex.substr(4, 2), 16)) * percent / 100);
        return `rgb(${Math.floor(r)}, ${Math.floor(g)}, ${Math.floor(b)})`;
    }

    initializeElements() {
        // DOM elements
        this.elements = {
            container: document.getElementById('chatbot-container'),
            messagesList: document.getElementById('messages-list'),
            messagesContainer: document.getElementById('messages-container'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            minimizeBtn: document.getElementById('minimize-btn'),
            botStatus: document.getElementById('bot-status'),
            botName: document.getElementById('bot-name'),
            botAvatar: document.querySelector('.bot-avatar'),
            typingIndicator: document.getElementById('typing-indicator'),
            typingText: document.getElementById('typing-text'),
            connectionStatus: document.getElementById('connection-status'),
            characterCount: document.querySelector('.character-count'),
            errorModal: document.getElementById('error-modal'),
            errorMessage: document.getElementById('error-message'),
            retryBtn: document.getElementById('retry-btn'),
            closeErrorBtn: document.getElementById('close-error-btn'),
            poweredBy: document.getElementById('powered-by'),

            // File upload elements - Temporarily disabled
            // fileUploadBtn: document.getElementById('file-upload-btn'),
            // fileUploadContainer: document.getElementById('file-upload-container'),
            // fileDropZone: document.getElementById('file-drop-zone'),
            // fileInput: document.getElementById('file-input'),
            // browseFilesBtn: document.getElementById('browse-files'),
            // closeFileUploadBtn: document.getElementById('close-file-upload'),
            // uploadProgress: document.getElementById('upload-progress'),
            // progressFill: document.getElementById('progress-fill'),
            // uploadStatus: document.getElementById('upload-status'),
            // fileInfoDisplay: document.getElementById('file-info-display'),
            // uploadedFileName: document.getElementById('uploaded-file-name'),
            // fileDetails: document.getElementById('file-details'),
            // removeFileBtn: document.getElementById('remove-file'),

            // Input container for minimize functionality
            inputContainer: document.getElementById('input-container'),

            // Floating icon for minimized state
            floatingIcon: document.getElementById('floating-icon'),
            chatBubbleIcon: document.querySelector('.chat-bubble-icon')
        };
    }

    attachEventListeners() {
        // Check if all required elements exist
        if (!this.elements.messageInput || !this.elements.sendBtn) {
            console.error('Required DOM elements not found');
            return;
        }

        // Message input events
        this.elements.messageInput.addEventListener('input', () => {
            this.handleInputChange();
        });

        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button
        this.elements.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Minimize button
        this.elements.minimizeBtn.addEventListener('click', () => {
            this.toggleMinimize();
        });

        // Error modal buttons
        this.elements.retryBtn.addEventListener('click', () => {
            this.hideErrorModal();
            this.initializeSession();
        });

        this.elements.closeErrorBtn.addEventListener('click', () => {
            this.hideErrorModal();
        });

        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });

        // File upload event listeners - Temporarily disabled
        // this.setupFileUploadListeners();

        // Click handler for floating icon (expand when clicking the floating icon)
        this.elements.floatingIcon.addEventListener('click', () => {
            this.toggleMinimize(false);
        });
    }

    setupCrossOriginCommunication() {
        // Listen for messages from parent window
        window.addEventListener('message', (event) => {
            this.handleParentMessage(event);
        });

        // Send ready message to parent
        this.sendToParent({
            type: 'widget_ready',
            sessionId: this.sessionId
        });
    }

    handleParentMessage(event) {
        const { type, data } = event.data;

        switch (type) {
            case 'configure':
                this.updateConfiguration(data);
                break;
            case 'page_data':
                this.handlePageData(data);
                break;
            case 'send_message':
                if (data.message) {
                    this.addUserMessage(data.message);
                    this.processUserMessage(data.message);
                }
                break;
            case 'clear_chat':
                this.clearChat();
                break;
            case 'minimize':
                this.toggleMinimize(true);
                break;
            case 'maximize':
                this.toggleMinimize(false);
                break;
        }
    }

    sendToParent(message) {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage(message, '*');
        }
    }

    async initializeSession() {
        try {
            this.showConnectionStatus('Connecting...');

            // Get configuration from URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const configParam = urlParams.get('config');

            if (configParam) {
                try {
                    this.config = JSON.parse(decodeURIComponent(configParam));
                } catch (e) {
                    console.warn('Invalid config parameter:', e);
                }
            }

            // Create session
            const headers = {
                'Content-Type': 'application/json',
            };
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            const response = await fetch(`${this.apiBaseUrl}/api/chat/sessions/create`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    config: this.config,
                    user_identifier: this.userIdentifier
                })
            });

            if (!response.ok) {
                throw new Error(`Session creation failed: ${response.status}`);
            }

            const data = await response.json();
            this.sessionId = data.sessionId;

            // Apply bot configuration if received
            if (data.config) {
                this.applyBotConfiguration(data.config);
            }

            this.updateBotStatus('Ready to help');
            this.hideConnectionStatus();

            // Send session created message to parent
            this.sendToParent({
                type: 'session_created',
                sessionId: this.sessionId
            });

        } catch (error) {
            console.error('Failed to initialize session:', error);
            this.showError('Failed to connect to chat service. Please try again.');
            this.updateBotStatus('Connection failed');
        }
    }

    updateConfiguration(newConfig) {
        this.config = { ...this.config, ...newConfig };

        // Update current provider if specified
        if (newConfig.aiProvider) {
            this.currentProvider = newConfig.aiProvider;
            this.currentProviderName = newConfig.aiProvider === 'openai' ? 'GPT Assistant' : 'Claude Assistant';
            this.updateProviderUI();
        }

        // Log the configuration for debugging
        console.log('Widget configuration updated:', this.config);

        // Update session configuration
        if (this.sessionId) {
            const headers = {
                'Content-Type': 'application/json',
            };
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            fetch(`${this.apiBaseUrl}/api/chat/sessions/${this.sessionId}/config`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ config: this.config })
            }).catch(error => {
                console.error('Failed to update session config:', error);
            });
        }
    }

    handlePageData(data) {
        // Store page data in config for context
        this.config.pageData = data.pageInfo;

        // Log for debugging
        console.log('Page data received:', data.pageInfo);

        // Update session with page data
        if (this.sessionId) {
            const headers = {
                'Content-Type': 'application/json',
            };
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            fetch(`${this.apiBaseUrl}/api/chat/sessions/${this.sessionId}/config`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ config: this.config })
            }).catch(error => {
                console.error('Failed to update session with page data:', error);
            });
        }
    }

    handleInputChange() {
        const message = this.elements.messageInput.value.trim();
        const length = this.elements.messageInput.value.length;

        // Update character count
        this.elements.characterCount.textContent = `${length}/1000`;

        // Enable/disable send button
        this.elements.sendBtn.disabled = !message || this.isProcessing;
    }

    autoResizeTextarea() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || this.isProcessing || !this.sessionId) return;

        this.addUserMessage(message);
        this.elements.messageInput.value = '';
        this.handleInputChange();
        this.autoResizeTextarea();

        await this.processUserMessage(message);
    }

    async processUserMessage(message) {
        if (this.isProcessing) {
            this.messageQueue.push(message);
            return;
        }

        this.isProcessing = true;
        this.showTypingIndicator();
        this.updateBotStatus('Thinking...');

        try {
            const headers = {
                'Content-Type': 'application/json',
            };
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            const response = await fetch(`${this.apiBaseUrl}/api/chat/messages/send`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    message: message,
                    config: this.config
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Request failed: ${response.status}`);
            }

            const data = await response.json();
            this.addBotMessage(data.response);

            // Update provider information
            if (data.provider) {
                this.currentProvider = data.provider;
                this.currentProviderName = data.providerName || (data.provider === 'openai' ? 'GPT Assistant' : 'Claude Assistant');

                // Update UI elements
                this.updateProviderUI();
            }

            // Send message to parent
            this.sendToParent({
                type: 'message_received',
                message: data.response,
                sessionId: this.sessionId,
                provider: data.provider
            });

        } catch (error) {
            console.error('Failed to send message:', error);
            this.addBotMessage('Sorry, I encountered an error. Please try again.');
            this.showError(error.message);
        } finally {
            this.hideTypingIndicator();
            this.updateBotStatus('Ready to help');
            this.isProcessing = false;

            // Process queued messages
            if (this.messageQueue.length > 0) {
                const nextMessage = this.messageQueue.shift();
                setTimeout(() => this.processUserMessage(nextMessage), 100);
            }
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement(message, 'user');
        this.elements.messagesList.appendChild(messageElement);
        this.scrollToBottom();
    }

    addBotMessage(message) {
        const messageElement = this.createMessageElement(message, 'bot');
        this.elements.messagesList.appendChild(messageElement);
        this.scrollToBottom();
    }

    createMessageElement(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Handle line breaks in messages
        const formattedContent = content.replace(/\n/g, '<br>');
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        return messageDiv;
    }

    showTypingIndicator() {
        this.elements.typingIndicator.classList.remove('hidden');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.elements.typingIndicator.classList.add('hidden');
    }

    updateBotStatus(status) {
        this.elements.botStatus.textContent = status;
    }

    showConnectionStatus(message) {
        this.elements.connectionStatus.querySelector('.status-text').textContent = message;
        this.elements.connectionStatus.classList.remove('hidden');
    }

    hideConnectionStatus() {
        this.elements.connectionStatus.classList.add('hidden');
    }

    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorModal.classList.remove('hidden');
    }

    hideErrorModal() {
        this.elements.errorModal.classList.add('hidden');
    }

    toggleMinimize(minimize = null) {
        this.isMinimized = minimize !== null ? minimize : !this.isMinimized;

        if (this.isMinimized) {
            // Hide the entire chat container
            this.elements.container.classList.add('chat-minimized');

            // Make body transparent to remove any background
            document.body.style.backgroundColor = 'transparent';

            // Show the floating icon
            this.elements.floatingIcon.classList.remove('hidden');
        } else {
            // Show the chat container
            this.elements.container.classList.remove('chat-minimized');

            // Restore body background
            document.body.style.backgroundColor = '';

            // Hide the floating icon
            this.elements.floatingIcon.classList.add('hidden');

            this.scrollToBottom();
        }

        // Notify parent about minimize state
        this.sendToParent({
            type: 'widget_minimized',
            minimized: this.isMinimized
        });
    }

    clearChat() {
        // Keep welcome message, remove others
        const messages = this.elements.messagesList.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(message => message.remove());

        // Clear chat history on server
        if (this.sessionId) {
            const headers = {};
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            fetch(`${this.apiBaseUrl}/api/chat/messages/clear/${this.sessionId}`, {
                method: 'DELETE',
                headers: headers
            }).catch(error => {
                console.error('Failed to clear chat history:', error);
            });
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
        }, 100);
    }

    formatTime(date) {
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    updateWelcomeTime() {
        const welcomeTimeElement = document.getElementById('welcome-time');
        if (welcomeTimeElement) {
            welcomeTimeElement.textContent = this.formatTime(new Date());
        }
    }

    setupFileUploadListeners() {
        // File upload button
        this.elements.fileUploadBtn.addEventListener('click', () => {
            this.showFileUpload();
        });

        // Browse files button
        this.elements.browseFilesBtn.addEventListener('click', () => {
            this.elements.fileInput.click();
        });

        // File input change
        this.elements.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // Close file upload
        this.elements.closeFileUploadBtn.addEventListener('click', () => {
            this.hideFileUpload();
        });

        // Remove file
        this.elements.removeFileBtn.addEventListener('click', () => {
            this.removeFile();
        });

        // Drag and drop events
        this.elements.fileDropZone.addEventListener('click', () => {
            this.elements.fileInput.click();
        });

        this.elements.fileDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.fileDropZone.classList.add('dragover');
        });

        this.elements.fileDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.elements.fileDropZone.classList.remove('dragover');
        });

        this.elements.fileDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.fileDropZone.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    }

    showFileUpload() {
        this.elements.fileUploadContainer.classList.remove('hidden');
    }

    hideFileUpload() {
        this.elements.fileUploadContainer.classList.add('hidden');
        this.elements.uploadProgress.classList.add('hidden');
        this.elements.fileInput.value = '';
    }

    handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['application/json', 'text/csv', 'application/csv'];
        const fileExt = file.name.split('.').pop().toLowerCase();

        if (!allowedTypes.includes(file.type) && !['json', 'csv'].includes(fileExt)) {
            this.showError('Only JSON and CSV files are supported.');
            return;
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('File size must be less than 10MB.');
            return;
        }

        this.uploadFile(file);
    }

    async uploadFile(file) {
        try {
            this.elements.uploadProgress.classList.remove('hidden');
            this.elements.progressFill.style.width = '0%';
            this.elements.uploadStatus.textContent = 'Uploading...';

            const formData = new FormData();
            formData.append('file', file);
            formData.append('sessionId', this.sessionId);

            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;
                this.elements.progressFill.style.width = progress + '%';
            }, 100);

            const headers = {};
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            const response = await fetch(`${this.apiBaseUrl}/api/chat/files/upload`, {
                method: 'POST',
                headers: headers,
                body: formData
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            const data = await response.json();

            // Complete progress
            this.elements.progressFill.style.width = '100%';
            this.elements.uploadStatus.textContent = 'Upload complete!';

            // Hide upload UI and show file info
            setTimeout(() => {
                this.hideFileUpload();
                this.showFileInfo(data);

                // Add system message about file upload
                this.addBotMessage(`✅ ${data.message}`);

                // Update UI to show current provider
                this.updateProviderUI();

                // Update placeholder to encourage file questions
                this.elements.messageInput.placeholder = 'Ask me anything about your uploaded file or this page...';
            }, 1000);

        } catch (error) {
            console.error('File upload failed:', error);
            this.elements.uploadProgress.classList.add('hidden');
            this.showError('Failed to upload file: ' + error.message);
        }
    }

    showFileInfo(fileData) {
        this.elements.fileInfoDisplay.classList.remove('hidden');
        this.elements.uploadedFileName.textContent = fileData.fileName;

        const details = [];
        details.push(`Type: ${fileData.fileType.toUpperCase()}`);
        details.push(`Size: ${(fileData.fileSize / 1024).toFixed(2)} KB`);

        if (fileData.summary) {
            if (fileData.fileType === 'csv') {
                details.push(`Columns: ${fileData.summary.columnCount}`);
                details.push(`Rows: ${fileData.summary.rowCount}`);
            } else if (fileData.fileType === 'json') {
                if (fileData.summary.type === 'array') {
                    details.push(`Array Length: ${fileData.summary.length}`);
                }
            }
        }

        this.elements.fileDetails.textContent = details.join(' • ');
    }

    async removeFile() {
        try {
            const headers = {};
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            const response = await fetch(`${this.apiBaseUrl}/api/chat/files/${this.sessionId}`, {
                method: 'DELETE',
                headers: headers
            });

            if (response.ok) {
                this.elements.fileInfoDisplay.classList.add('hidden');
                this.elements.messageInput.placeholder = 'Ask me anything about this page...';
                this.addBotMessage('📄 File data has been removed from this session.');
                this.updateProviderUI();
            }
        } catch (error) {
            console.error('Failed to remove file:', error);
            this.showError('Failed to remove file data.');
        }
    }

    updatePoweredByText() {
        // This will be updated when we receive response from AI showing which provider was used
        // For now, keep the default
    }

    applyBotConfiguration(config) {
        // Store configuration for later use
        this.botConfig = config;

        // Update bot name if provided
        if (config.botName) {
            this.currentProviderName = config.botName;
            this.elements.botName.textContent = config.botName;
            this.elements.typingText.textContent = `${config.botName} is typing...`;
        }

        // Update powered by text if provided
        if (config.poweredBy) {
            this.elements.poweredBy.textContent = `Powered by ${config.poweredBy}`;
        }

        // Update bot colors if provided
        if (config.botColor) {
            this.applyBotColors(config.botColor);
        }

        // Update bot icon if provided
        if (config.botIcon) {
            this.applyBotIcon(config.botIcon);
        }

        // Update message background color if provided
        if (config.botMsgBgColor) {
            this.applyMessageBgColor(config.botMsgBgColor);
        }
    }

    applyBotColors(color) {
        // Set CSS custom properties for dynamic color theming
        document.documentElement.style.setProperty('--bot-primary-color', color);

        // Create a darker variant for hover states (20% darker)
        const darkerColor = this.darkenColor(color, 20);
        document.documentElement.style.setProperty('--bot-primary-color-dark', darkerColor);

        // Create a lighter variant for backgrounds (80% lighter)
        const lighterColor = this.lightenColor(color, 80);
        document.documentElement.style.setProperty('--bot-primary-color-light', lighterColor);
    }

    applyBotIcon(iconUrl) {
        // Update bot avatar in header
        if (this.elements.botAvatar) {
            this.elements.botAvatar.innerHTML = `<img src="${iconUrl}" alt="Bot Avatar" class="bot-avatar-img">`;
        }

        // Update floating icon when minimized
        if (this.elements.chatBubbleIcon) {
            this.elements.chatBubbleIcon.innerHTML = `<img src="${iconUrl}" alt="Bot Icon" class="floating-bot-icon">`;
        }
    }

    applyMessageBgColor(color) {
        // Set CSS custom property for message background color
        document.documentElement.style.setProperty('--bot-msg-bg-color', color);

        // Create a darker variant for gradients
        const darkerColor = this.darkenColor(color, 20);
        document.documentElement.style.setProperty('--bot-msg-bg-color-dark', darkerColor);
    }

    updateProviderUI() {
        // Use configured bot name if available, otherwise use provider-based name
        const botName = this.botConfig?.botName || this.currentProviderName;
        const poweredBy = this.botConfig?.poweredBy || (this.currentProvider === 'openai' ? 'OpenAI' : 'Claude');

        // Update bot name in header
        this.elements.botName.textContent = botName;

        // Update typing indicator text
        this.elements.typingText.textContent = `${botName} is typing...`;

        // Update powered by text
        this.elements.poweredBy.textContent = `Powered by ${poweredBy}`;
    }
}

// Check if we're in the parent page or iframe
function initializeWidget() {
    // Prevent double initialization
    if (window.claudeWidgetInitialized) {
        return;
    }
    window.claudeWidgetInitialized = true;

    const container = document.getElementById('chatbot-container');

    if (!container) {
        // We're in the parent page - create iframe loader
        initializeIframeLoader();
    } else {
        // We're in the iframe - initialize the widget normally
        // Wait a bit to ensure all DOM elements are ready
        setTimeout(() => {
            try {
                window.claudeWidget = new ClaudeChatWidget();
            } catch (error) {
                console.error('Failed to initialize widget:', error);
            }
        }, 100);
    }
}

// Initialize iframe loader on parent page
function initializeIframeLoader() {
    const apiKey = WIDGET_CONFIG.apiKey;
    const baseUrl = WIDGET_CONFIG.apiBaseUrl;
    const userIdentifier = WIDGET_CONFIG.userIdentifier;

    if (!apiKey) {
        console.error('ClaudeChatWidget: API key not found in configuration.');
        return;
    }

    // Create iframe container
    const iframe = document.createElement('iframe');
    iframe.id = 'chatbot-iframe';
    iframe.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        height: 600px;
        border: none;
        border-radius: 12px;
        z-index: 999999;
        background: transparent;
    `;

    // Set iframe source to chatbot.html with embedded config
    const configParams = new URLSearchParams({
        apiKey: apiKey,
        botName: WIDGET_CONFIG.botName,
        botColor: WIDGET_CONFIG.botColor,
        botMsgBgColor: WIDGET_CONFIG.botMsgBgColor,
        botIconUrl: WIDGET_CONFIG.botIconUrl,
        poweredByText: WIDGET_CONFIG.poweredByText,
        _t: Date.now() // Cache buster
    });

    // Add userIdentifier if provided
    if (userIdentifier) {
        configParams.set('userIdentifier', userIdentifier);
    }

    iframe.src = `${baseUrl}/static/widget/chatbot.html?${configParams.toString()}`;

    // Append to body
    document.body.appendChild(iframe);

    console.log('ClaudeChatWidget: Iframe loaded with client configuration');
}

// Initialize the widget when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWidget);
} else {
    // DOM already loaded
    initializeWidget();
}

// Export for external access
window.ClaudeChatWidget = ClaudeChatWidget;
