/**
 * Chat functionality for the RAG application.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Elements
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const chatContainer = document.getElementById('chat-container'); // äußerer Container
    const chatScroll = document.getElementById('chat-scroll'); // neuer innerer Scrollbereich
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

    // Privacy Consent Elements
    const privacyOverlay = document.getElementById('privacy-consent-overlay');
    const privacyCheckbox = document.getElementById('privacy-consent-checkbox');
    const privacyAcceptBtn = document.getElementById('privacy-consent-accept');

    // Consent key (increment version if text changes)
    const CONSENT_KEY = 'privacyConsentV2'; // Version erhöht damit Overlay erneut erscheint
    const consentGiven = localStorage.getItem(CONSENT_KEY) === 'true';

    // WARTUNGSHINWEIS:
    // Wenn sich der rechtliche Inhalt des Datenschutzhinweises ändert,
    // bitte CONSENT_KEY auf privacyConsentV2 (oder höher) erhöhen,
    // damit Nutzer den Hinweis erneut bestätigen müssen.

    // Initial consent check
    if (!consentGiven && privacyOverlay) {
        privacyOverlay.classList.remove('d-none');
        document.body.classList.add('no-scroll');
        if (chatInput) chatInput.disabled = true;
        if (sendButton) sendButton.disabled = true;
    }

    // Handle checkbox enable button
    if (privacyCheckbox && privacyAcceptBtn) {
        privacyCheckbox.addEventListener('change', () => {
            privacyAcceptBtn.disabled = !privacyCheckbox.checked;
        });
        privacyAcceptBtn.addEventListener('click', () => {
            localStorage.setItem(CONSENT_KEY, 'true');
            privacyOverlay.classList.add('d-none');
            document.body.classList.remove('no-scroll');
            if (chatInput) chatInput.disabled = false;
            if (sendButton) sendButton.disabled = false;
            chatInput?.focus();
        });
    }
    
    // Chat history array
    let messages = [];
    
    // Decision tree configuration
    const decisionTree = {
        start: "usage",
        nodes: {
            usage: {
                title: "Wie möchtest du dein neues Fahrrad nutzen?",
                options: [
                    { value: "sport", label: "Sport/Freizeit", next: "terrain" },
                    { value: "work", label: "Arbeitsweg", next: "work_route" },
                    { value: "errands", label: "Besorgungen", next: "cargo_weight" }
                ]
            },
            terrain: {
                title: "Wo fühlst du dich wohl?",
                options: [
                    { value: "forest", label: "Waldweg", next: "forest_type" },
                    { value: "road", label: "Straße", next: "road_type" }
                ]
            },
            forest_type: {
                title: "Welche Art von Waldwegen fährst du?",
                options: [
                    { value: "heavy", label: "Schweres Gelände, Bergab, Verwurzelt", next: "ebike_heavy" },
                    { value: "light", label: "Leichteres Gelände, Freeride", next: "ebike_light" },
                    { value: "gravel", label: "Waldautobahn, Schotterpisten, Wald und Wiesenwege", next: "ebike_gravel_forest" }
                ]
            },
            ebike_heavy: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_light: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_gravel_forest: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            road_type: {
                title: "Wie würden deine Touren aussehen?",
                options: [
                    { value: "gravel", label: "Gravel (Grund Hype)", next: "ebike_gravel" },
                    { value: "crossrace", label: "Straße/Schotter (Crossrace)", next: "ebike_crossrace" },
                    { value: "racing", label: "Schnell auf Strecke (Rennrad)", next: "racing_position" }
                ]
            },
            ebike_gravel: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_crossrace: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            racing_position: {
                title: "Wie möchtest du auf dem Fahrrad sitzen?",
                options: [
                    { value: "sporty", label: "Sportlich sitzend", result: true },
                    { value: "upright", label: "Aufrechter sitzend", result: true }
                ]
            },
            work_route: {
                title: "Wie sieht dein Arbeitsweg aus?",
                options: [
                    { value: "city", label: "Durch die Stadt", next: "city_position" },
                    { value: "countryside", label: "Über Land", next: "countryside_position" }
                ]
            },
            city_position: {
                title: "Wie möchtest du auf dem Fahrrad sitzen?",
                options: [
                    { value: "upright", label: "Aufrecht sitzend", next: "ebike_city_upright" },
                    { value: "medium", label: "Mittelaufrecht", next: "ebike_city_medium" },
                    { value: "sporty", label: "Sportlich sitzend", next: "ebike_city_sporty" }
                ]
            },
            ebike_city_upright: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_city_medium: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_city_sporty: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            countryside_position: {
                title: "Wie möchtest du auf dem Fahrrad sitzen?",
                options: [
                    { value: "medium", label: "Mittelaufrecht", next: "ebike_countryside_medium" },
                    { value: "sporty", label: "Sportlich sitzend", next: "ebike_countryside_sporty" }
                ]
            },
            ebike_countryside_medium: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_countryside_sporty: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            cargo_weight: {
                title: "Wie groß ist dein durchschnittliches Transportgewicht?",
                options: [
                    { value: "light", label: "Bis 25kg (City, urban, Trekking)", next: "cargo_light_position" },
                    { value: "heavy", label: "Ab 25 kg (Lastenrad)", next: "cargo_type" }
                ]
            },
            cargo_light_position: {
                title: "Wie möchtest du auf deinem Fahrrad sitzen?",
                options: [
                    { value: "upright", label: "Aufrecht sitzend", next: "ebike_cargo_upright" },
                    { value: "medium", label: "Mittelaufrecht", next: "ebike_cargo_medium" },
                    { value: "sporty", label: "Sportlich sitzend", next: "ebike_cargo_sporty" }
                ]
            },
            ebike_cargo_upright: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_cargo_medium: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            ebike_cargo_sporty: {
                title: "E-Bike?",
                options: [
                    { value: "yes", label: "Ja", result: true },
                    { value: "no", label: "Nein", result: true }
                ]
            },
            cargo_type: {
                title: "Was möchtest du transportieren?",
                options: [
                    { value: "children", label: "Kinder", result: true },
                    { value: "other", label: "Sonstiges", result: true }
                ]
            }
        }
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
        // Block submission if consent missing
        if (!localStorage.getItem(CONSENT_KEY)) {
            if (privacyOverlay) {
                privacyOverlay.classList.remove('d-none');
                document.body.classList.add('no-scroll');
            }
            return;
        }
        e.preventDefault();
        const query = chatInput.value.trim();
        if (query && !isLoading()) {
            sendMessage(query);
        }
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isLoading()) handleChatSubmit(e);
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

    function scrollToBottom(force = true) {
        // Immer nach unten scrollen (kann mit force=false deaktiviert werden)
        const target = chatScroll || chatContainer;
        if (force) {
            // Doppelt sicherstellen: sowohl sofort als auch nach Animation-Frame
            target.scrollTop = target.scrollHeight;
            requestAnimationFrame(() => {
                target.scrollTop = target.scrollHeight;
            });
        }
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
            currentNode: decisionTree.start,
            selections: [],
            nodeHistory: [],
            modal: overlay,
            progressBar: overlay.querySelector('.progress-bar'),
            stepIndicator: overlay.querySelector('.current-step'),
            questionElement: overlay.querySelector('.decision-tree-question'),
            optionsElement: overlay.querySelector('.decision-tree-options'),
            backButton: overlay.querySelector('.btn-back')
        };

        // Set up event handlers
        setupDecisionTreeHandlers(state);

        // Show first node
        showDecisionTreeNode(state);
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
            if (state.nodeHistory.length > 0) {
                state.currentNode = state.nodeHistory.pop();
                state.selections.pop();
                showDecisionTreeNode(state);
            }
        });
    }

    function showDecisionTreeNode(state) {
        const node = decisionTree.nodes[state.currentNode];
        
        // Update progress based on steps taken (linear progression)
        // Estimate average path length and calculate progress accordingly
        const estimatedTotalSteps = 5; // Most paths have about 4-5 questions
        const currentStep = state.selections.length + 1;
        const progress = Math.min((state.selections.length / estimatedTotalSteps) * 100, 90);
        state.progressBar.style.width = progress + '%';
        state.progressBar.setAttribute('aria-valuenow', currentStep);
        state.stepIndicator.textContent = currentStep;

        // Update question
        state.questionElement.textContent = node.title;

        // Clear and populate options
        state.optionsElement.innerHTML = '';
        
        node.options.forEach(option => {
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
        state.backButton.style.display = state.nodeHistory.length > 0 ? 'inline-block' : 'none';
    }

    function selectDecisionTreeOption(state, option) {
        const currentNode = decisionTree.nodes[state.currentNode];
        
        // Store the selection
        state.selections.push({
            node: state.currentNode,
            question: currentNode.title,
            value: option.value,
            label: option.label
        });

        // Check if this option has a result (end of tree) or leads to next node
        if (option.result) {
            // This is a final result
            completeDecisionTree(state);
        } else if (option.next) {
            // Move to next node
            state.nodeHistory.push(state.currentNode);
            state.currentNode = option.next;
            showDecisionTreeNode(state);
        } else {
            // This shouldn't happen with the new tree structure
            console.error('Option has neither result nor next node:', option);
        }
    }

    function completeDecisionTree(state) {
        // Show completion: set progress to 100%
        state.progressBar.style.width = '100%';
        state.progressBar.setAttribute('aria-valuenow', state.selections.length + 1);
        
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
