/**
 * Chat functionality for the RAG application.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Elements
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const chatContainer = document.getElementById('chat-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    // Templates
    const emptyChatTemplate = document.getElementById('empty-chat-template');
    const userMessageTemplate = document.getElementById('user-message-template');
    const assistantMessageTemplate = document.getElementById('assistant-message-template');
    
    // Quick action buttons
    const btnMyBike = document.getElementById('btn-my-bike');
    const btnWarranty = document.getElementById('btn-warranty');
    const btnCompany = document.getElementById('btn-company');
    const btnGuidedSelection = document.getElementById('btn-guided-selection');
    
    // Chat history array
    let messages = [];
    
    // Decision tree configuration
    const decisionTree = {
        layers: [
            {
                title: "Welcher Fahrradtyp?",
                options: [
                    { value: "stadtrad", label: "Stadtrad / City Bike" },
                    { value: "mountainbike", label: "Mountainbike" },
                    { value: "rennrad", label: "Rennrad" },
                    { value: "ebike", label: "E-Bike" },
                    { value: "tourenrad", label: "Tourenrad" }
                ]
            },
            {
                title: "Wie ist dein Budget?",
                options: [
                    { value: "unter-500", label: "Unter 500€" },
                    { value: "500-1000", label: "500€ - 1.000€" },
                    { value: "1000-2000", label: "1.000€ - 2.000€" },
                    { value: "2000-3000", label: "2.000€ - 3.000€" },
                    { value: "ueber-3000", label: "Über 3.000€" }
                ]
            },
            {
                title: "Wie oft fährst du?",
                options: [
                    { value: "gelegentlich", label: "Gelegentlich (1-2x pro Woche)" },
                    { value: "regelmaessig", label: "Regelmäßig (3-5x pro Woche)" },
                    { value: "taeglich", label: "Täglich" },
                    { value: "wochenende", label: "Nur am Wochenende" },
                    { value: "sport", label: "Für Sport/Training" }
                ]
            },
            {
                title: "Welche Strecken fährst du hauptsächlich?",
                options: [
                    { value: "stadt", label: "Stadt / Asphalt" },
                    { value: "wald", label: "Wald- und Feldwege" },
                    { value: "berge", label: "Hügel und Berge" },
                    { value: "gemischt", label: "Gemischt" },
                    { value: "langstrecke", label: "Lange Touren" }
                ]
            },
            {
                title: "Was ist dir am wichtigsten?",
                options: [
                    { value: "komfort", label: "Komfort" },
                    { value: "geschwindigkeit", label: "Geschwindigkeit" },
                    { value: "robustheit", label: "Robustheit" },
                    { value: "gewicht", label: "Geringes Gewicht" },
                    { value: "preis", label: "Gutes Preis-Leistungs-Verhältnis" }
                ]
            }
        ]
    };
    
    // Initialize empty chat
    if (emptyChatTemplate) {
        const emptyContent = emptyChatTemplate.content.cloneNode(true);
        chatHistory.appendChild(emptyContent);
    }
    
    // Event listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    chatInput.addEventListener('keydown', handleKeyDown);
    btnMyBike.addEventListener('click', () => sendQuickQuestion("Welches Fahrrad ist perfekt für mich?"));
    btnWarranty.addEventListener('click', () => sendQuickQuestion("Welche Garantie gibt es auf mein CUBE Fahrrad?"));
    btnCompany.addEventListener('click', () => sendQuickQuestion("Erzähle mir etwas über CUBE."));
    
    if (btnGuidedSelection) {
        btnGuidedSelection.addEventListener('click', showDecisionTreeModal);
    }

    function handleChatSubmit(e) {
        e.preventDefault();
        const query = chatInput.value.trim();
        if (query && !isLoading()) {
            sendMessage(query);
        }
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isLoading()) {
                handleChatSubmit(e);
            }
        }
    }

    function sendQuickQuestion(question) {
        if (!isLoading()) {
            sendMessage(question);
        }
    }

    function sendMessage(text) {
        hideError();
        
        // Add user message to UI
        addUserMessage(text);
        
        // Clear input field
        chatInput.value = '';
        
        // Add message to chat history
        const userMessage = {
            role: 'user',
            content: text
        };
        messages.push(userMessage);
        
        // Show loading indicator
        showLoading();
        
        // Send request to server
        fetch('/api/chat/completion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.response) {
                const assistantMessage = {
                    role: 'assistant',
                    content: data.response
                };
                messages.push(assistantMessage);
                addAssistantMessage(data.response, data.citations);
            } else {
                throw new Error('No response received');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            showError('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        });
    }

    function isLoading() {
        return !loadingIndicator.classList.contains('d-none');
    }

    function showLoading() {
        loadingIndicator.classList.remove('d-none');
        scrollToBottom();
    }

    function hideLoading() {
        loadingIndicator.classList.add('d-none');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
        scrollToBottom();
    }

    function hideError() {
        errorContainer.classList.add('d-none');
    }

    function addUserMessage(text) {
        if (userMessageTemplate) {
            clearEmptyChat();
            const messageContent = userMessageTemplate.content.cloneNode(true);
            const messageText = messageContent.querySelector('.message-content');
            if (messageText) {
                messageText.textContent = text;
            }
            chatHistory.appendChild(messageContent);
            scrollToBottom();
        }
    }

    function addAssistantMessage(text, citations) {
        if (assistantMessageTemplate) {
            clearEmptyChat();
            const messageContent = assistantMessageTemplate.content.cloneNode(true);
            const messageText = messageContent.querySelector('.message-content');
            
            if (messageText) {
                // Convert markdown to HTML (no citation processing)
                let processedText = convertMarkdownToHTML(text);
                // Remove any citation markers like [doc1], [doc2], etc.
                processedText = processedText.replace(/\[doc\d+\]/gi, '');
                messageText.innerHTML = processedText;
            }
            
            chatHistory.appendChild(messageContent);
            scrollToBottom();
        }
    }

    function processCitations(text, citations) {
        if (!citations || citations.length === 0) {
            return text;
        }

        let processedText = text;
        
        // Check if text already has citation markers like [doc1]
        const hasExistingMarkers = /\[doc\d+\]/i.test(text);
        
        if (hasExistingMarkers) {
            // Replace existing markers with clickable badges
            citations.forEach((citation, index) => {
                const marker = `[doc${index + 1}]`;
                const badge = `<span class="citation-badge" data-citation-index="${index}" onclick="showCitationModal(${index}, '${encodeURIComponent(citation.title)}', '${encodeURIComponent(citation.content)}')">${marker}</span>`;
                processedText = processedText.replace(new RegExp('\\' + marker, 'g'), badge);
            });
        }
        // Remove the "Quellen:" section - only show inline citations
        
        return processedText;
    }

    function convertMarkdownToHTML(text) {
        if (!text) return text;
        
        // Convert markdown to HTML
        let html = text;
        
        // Horizontal rules: --- or *** → <hr> or remove them entirely
        html = html.replace(/^---+$/gm, '<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">');
        html = html.replace(/^\*\*\*+$/gm, '<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">');
        
        // Headers: ### Header → <h3>Header</h3>
        html = html.replace(/^### (.+)$/gm, '<h3 style="font-size: 1.2em; font-weight: bold; margin: 15px 0 10px 0; color: #333;">$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2 style="font-size: 1.4em; font-weight: bold; margin: 15px 0 10px 0; color: #333;">$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1 style="font-size: 1.6em; font-weight: bold; margin: 15px 0 10px 0; color: #333;">$1</h1>');
        
        // Bold text: **text** or __text__
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Italic text: *text* or _text_
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Numbered lists: 1. item
        html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<div style="margin-left: 20px;">$1. $2</div>');
        
        // Bullet points: - item or * item
        html = html.replace(/^[-*]\s+(.+)$/gm, '<div style="margin-left: 20px;">• $1</div>');
        
        // Handle line breaks: Convert multiple newlines to proper spacing
        // Replace 3+ consecutive newlines with double line break (paragraph spacing)
        html = html.replace(/\n{3,}/g, '\n\n');
        // Replace double newlines with paragraph breaks
        html = html.replace(/\n\n/g, '<br><br>');
        // Replace single newlines with single line breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }

    function clearEmptyChat() {
        const emptyChat = chatHistory.querySelector('.empty-chat');
        if (emptyChat) {
            emptyChat.remove();
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
    }

    // Decision Tree Modal Functions
    function showDecisionTreeModal() {
        // Remove any existing modal
        const existingOverlay = document.querySelector('.decision-tree-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Create overlay and modal
        const overlay = document.createElement('div');
        overlay.className = 'decision-tree-overlay citation-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');

        overlay.innerHTML = `
            <div class="decision-tree-modal citation-modal" style="max-width: 600px; border-radius: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                <div class="citation-modal-header" style="background: rgb(123,156,145); color: white; border-radius: 1rem 1rem 0 0; padding: 1.5rem;">
                    <h5 class="citation-modal-title" style="margin: 0; font-weight: 600; font-size: 1.25rem;">🚴‍♀️ Finde dein perfektes CUBE</h5>
                    <button type="button" class="citation-close-button decision-tree-close" style="background: none; border: none; color: white; font-size: 1.5rem; opacity: 0.8; padding: 0; margin: 0;" aria-label="Close">&times;</button>
                </div>
                <div class="citation-modal-body" style="padding: 2rem;">
                    <div class="decision-tree-progress mb-4">
                        <div class="progress" style="height: 12px; border-radius: 15px; background-color: rgba(255,255,255,0.2); box-shadow: inset 0 2px 4px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.1);">
                            <div class="progress-bar" role="progressbar" style="width: 20%; background: linear-gradient(90deg, #ffffff 0%, #666666 40%, #000000 100%); border-radius: 15px; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 3px 12px rgba(0,0,0,0.4), inset 0 1px 2px rgba(255,255,255,0.3);" aria-valuenow="1" aria-valuemin="0" aria-valuemax="5"></div>
                        </div>
                        <small style="color: white; font-weight: 600; margin-top: 0.75rem; display: block; text-shadow: 0 1px 2px rgba(0,0,0,0.1);">Schritt <span class="current-step">1</span> von 5</small>
                    </div>
                    <div class="decision-tree-content">
                        <h6 class="decision-tree-question mb-4" style="color: #333; font-weight: 600; font-size: 1.1rem; line-height: 1.4;"></h6>
                        <div class="decision-tree-options"></div>
                    </div>
                    <div class="decision-tree-navigation mt-4 d-flex justify-content-between align-items-center">
                        <button type="button" class="btn btn-back" style="display: none; background-color: #f8f9fa; border: 1px solid #dee2e6; color: #6c757d; padding: 0.5rem 1.5rem; border-radius: 0.5rem; font-weight: 500;">← Zurück</button>
                        <div></div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Initialize decision tree state
        const state = {
            currentLayer: 0,
            selections: [],
            modal: overlay,
            progressBar: overlay.querySelector('.progress-bar'),
            stepIndicator: overlay.querySelector('.current-step'),
            questionElement: overlay.querySelector('.decision-tree-question'),
            optionsElement: overlay.querySelector('.decision-tree-options'),
            backButton: overlay.querySelector('.btn-back')
        };

        // Set up event handlers
        setupDecisionTreeHandlers(state);

        // Show first layer
        showDecisionTreeLayer(state);
    }

    function setupDecisionTreeHandlers(state) {
        // Close button
        const closeButton = state.modal.querySelector('.decision-tree-close');
        closeButton.addEventListener('click', () => {
            state.modal.remove();
        });

        // Close modal when clicking outside
        state.modal.addEventListener('click', function(e) {
            if (e.target === state.modal) {
                state.modal.remove();
            }
        });

        // Close modal on escape key
        document.addEventListener('keydown', function closeOnEscape(e) {
            if (e.key === 'Escape') {
                state.modal.remove();
                document.removeEventListener('keydown', closeOnEscape);
            }
        });

        // Back button
        state.backButton.addEventListener('click', () => {
            if (state.currentLayer > 0) {
                state.currentLayer--;
                state.selections.pop();
                showDecisionTreeLayer(state);
            }
        });
    }

    function showDecisionTreeLayer(state) {
        const layer = decisionTree.layers[state.currentLayer];
        
        // Update progress - calculate so that 100% is only reached after completion
        // Show progress based on questions answered, not current question
        const progress = (state.currentLayer / decisionTree.layers.length) * 100;
        state.progressBar.style.width = progress + '%';
        state.progressBar.setAttribute('aria-valuenow', state.currentLayer);
        state.stepIndicator.textContent = state.currentLayer + 1;

        // Update question
        state.questionElement.textContent = layer.title;

        // Clear and populate options
        state.optionsElement.innerHTML = '';
        
        layer.options.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn me-2 mb-3';
            button.style.cssText = `
                min-width: 140px;
                padding: 0.75rem 1.5rem;
                border: 2px solid rgb(123,156,145);
                background-color: white;
                color: rgb(123,156,145);
                border-radius: 0.75rem;
                font-weight: 500;
                font-size: 0.95rem;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            `;
            button.textContent = option.label;
            
            // Hover effects
            button.addEventListener('mouseenter', () => {
                button.style.backgroundColor = 'rgb(154,81,98)';
                button.style.borderColor = 'rgb(154,81,98)';
                button.style.color = 'white';
                button.style.transform = 'translateY(-1px)';
                button.style.boxShadow = '0 4px 12px rgba(154,81,98,0.3)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.backgroundColor = 'white';
                button.style.borderColor = 'rgb(123,156,145)';
                button.style.color = 'rgb(123,156,145)';
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
            });
            
            button.addEventListener('click', () => {
                selectDecisionTreeOption(state, option);
            });
            
            state.optionsElement.appendChild(button);
        });

        // Show/hide back button
        state.backButton.style.display = state.currentLayer > 0 ? 'inline-block' : 'none';
    }

    function selectDecisionTreeOption(state, option) {
        // Store the selection
        state.selections.push({
            layer: state.currentLayer,
            question: decisionTree.layers[state.currentLayer].title,
            value: option.value,
            label: option.label
        });

        // Move to next layer or finish
        if (state.currentLayer < decisionTree.layers.length - 1) {
            state.currentLayer++;
            showDecisionTreeLayer(state);
        } else {
            // All layers completed, send the message
            completeDecisionTree(state);
        }
    }

    function completeDecisionTree(state) {
        // Show completion: set progress to 100%
        state.progressBar.style.width = '100%';
        state.progressBar.setAttribute('aria-valuenow', 5);
        
        // Build the message from selections
        let prompt = "Ich suche ein Fahrrad basierend auf folgenden Kriterien:\n\n";
        
        for (let i = 0; i < state.selections.length; i++) {
            const selection = state.selections[i];
            prompt += selection.question + ": " + selection.label + "\n";
        }
        
        prompt += "\nKannst du mir das perfekte CUBE Fahrrad für meine Bedürfnisse empfehlen?";

        // Small delay to show completion animation, then close modal
        setTimeout(() => {
            state.modal.remove();
            // Send the message to the RAG system
            sendMessage(prompt);
        }, 500);
    }

    // Global function for citation modal (needed for onclick handlers)
    window.showCitationModal = function(index, title, content) {
        const decodedTitle = decodeURIComponent(title);
        const decodedContent = decodeURIComponent(content);
        
        // Remove any existing citation modal
        const existingModal = document.querySelector('.citation-overlay');
        if (existingModal) {
            existingModal.remove();
        }

        // Create citation modal
        const overlay = document.createElement('div');
        overlay.className = 'citation-overlay';
        overlay.innerHTML = `
            <div class="citation-modal">
                <div class="citation-modal-header">
                    <h5 class="citation-modal-title">Quelle ${index + 1}: ${decodedTitle}</h5>
                    <button type="button" class="citation-close-button" aria-label="Close">&times;</button>
                </div>
                <div class="citation-modal-body">
                    <p>${decodedContent}</p>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Add event listeners
        overlay.querySelector('.citation-close-button').addEventListener('click', () => {
            overlay.remove();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    };
});
