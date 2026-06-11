document.addEventListener('DOMContentLoaded', () => {
    // State management
    let activeRawContent = '';
    
    // DOM Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const outputBody = document.getElementById('output-body');
    const copyBtn = document.getElementById('copy-btn');
    const historyList = document.getElementById('history-list');
    const historySearch = document.getElementById('history-search');
    
    // Forms
    const blogForm = document.getElementById('blog-form');
    const productForm = document.getElementById('product-form');
    const captionForm = document.getElementById('caption-form');
    const settingsForm = document.getElementById('settings-form');
    const settingsAlert = document.getElementById('settings-success-alert');

    // 1. Tab Navigation
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Toggle active classes on tab buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Toggle active panels
            tabPanels.forEach(panel => {
                if (panel.id === targetTab) {
                    panel.classList.add('active');
                } else {
                    panel.classList.remove('active');
                }
            });
        });
    });

    // 2. Simple Markdown Parser
    function renderMarkdown(text) {
        if (!text) return '';
        
        let html = text;
        
        // Escape HTML tags to prevent XSS but allow our formatting
        html = html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
            
        // Headings: # Header to <h1>Header</h1>
        html = html.replace(/^#\s+(.+)$/gm, '<h1 style="font-size: 1.6rem; color: var(--color-primary); margin: 1.5rem 0 1rem 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">$1</h1>');
        html = html.replace(/^##\s+(.+)$/gm, '<h2 style="font-size: 1.3rem; color: var(--color-secondary); margin: 1.3rem 0 0.8rem 0;">$1</h2>');
        html = html.replace(/^###\s+(.+)$/gm, '<h3 style="font-size: 1.1rem; color: var(--text-primary); margin: 1.1rem 0 0.6rem 0;">$1</h3>');
        
        // Horizontal Rules: --- to <hr>
        html = html.replace(/^---$/gm, '<hr style="border: 0; height: 1px; background: var(--border-color); margin: 1.5rem 0;">');
        
        // Bold: **text** to <strong>text</strong>
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-primary);">$1</strong>');
        
        // Italic: *text* to <em>text</em>
        html = html.replace(/\*(.*?)\*/g, '<em style="color: var(--text-secondary);">$1</em>');
        
        // Unordered lists: - item to <li>item</li> (and wrap in <ul>)
        html = html.replace(/^\s*-\s+(.+)$/gm, '<li style="margin-left: 1.5rem; margin-bottom: 0.4rem; color: var(--text-primary);">$1</li>');
        
        // Numbered lists: 1. item to <li>item</li>
        html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li style="margin-left: 1.5rem; margin-bottom: 0.4rem; list-style-type: decimal; color: var(--text-primary);">$1</li>');

        // Splicing double linebreaks into paragraphs
        // Split text by paragraphs, ignore lines that are headers, lists, hr, etc.
        const lines = html.split('\n\n');
        const formattedParagraphs = lines.map(p => {
            p = p.trim();
            if (!p) return '';
            
            // If it is a heading, list, or divider, return it without p wrap
            if (p.startsWith('<h') || p.startsWith('<li') || p.startsWith('<hr') || p.startsWith('📱')) {
                return p;
            }
            return `<p style="margin-bottom: 1rem; color: var(--text-primary); line-height: 1.6;">${p}</p>`;
        });
        
        return formattedParagraphs.join('\n');
    }

    // 3. Display Content
    function displayGeneratedOutput(prompt, text, dateStr) {
        activeRawContent = text;
        outputBody.innerHTML = `
            <div style="animation: fadeIn 0.4s ease-out;">
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border-left: 3px solid var(--color-primary);">
                    <strong>Prompt parameters:</strong> ${prompt}
                </div>
                <div class="rendered-content">${renderMarkdown(text)}</div>
            </div>
        `;
        copyBtn.disabled = false;
        copyBtn.innerHTML = `
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m-2 4h5m-3-3l3 3m0 0l-3 3"/></svg>
            Copy Copy
        `;
        copyBtn.className = "btn btn-secondary btn-icon";
    }

    // 4. Loading State Trigger
    function setConsoleLoading() {
        outputBody.innerHTML = `
            <div class="output-empty">
                <div class="spinner"></div>
                <p style="color: var(--color-primary); font-weight: 600; letter-spacing: 0.05em; font-family: var(--font-heading);">AI GENERATING CONTENT...</p>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">Connecting with LLM node</p>
            </div>
        `;
        copyBtn.disabled = true;
    }

    // 5. Add to History sidebar dynamically
    function addToHistorySidebar(id, type, prompt, text, date) {
        // Remove empty history placeholder if it exists
        const placeholder = document.getElementById('no-history-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        // Map short content type name to readable display name
        const displayTypes = {
            'blog': 'Blog Post',
            'product': 'Product Description',
            'caption': 'Social Media Caption'
        };
        const typeLabel = displayTypes[type] || type;

        const newItem = document.createElement('button');
        newItem.className = 'history-item active';
        newItem.setAttribute('data-id', id);
        newItem.innerHTML = `
            <span class="history-item-type">${typeLabel}</span>
            <span class="history-item-prompt">${prompt}</span>
            <span class="history-item-date">${date}</span>
        `;

        // Remove active class from other items
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.remove('active');
        });

        // Insert at the top
        historyList.insertBefore(newItem, historyList.firstChild);

        // Bind click event
        newItem.addEventListener('click', () => {
            loadHistoryItem(id, newItem);
        });
    }

    // 6. API Forms Submit Handler (AJAX)
    const handleFormSubmit = (form, endpoint, type) => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            setConsoleLoading();

            const formData = new FormData(form);

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    displayGeneratedOutput(data.prompt, data.generated_text, data.created_at);
                    addToHistorySidebar(data.id, data.content_type, data.prompt, data.generated_text, data.created_at);
                    form.reset();
                } else {
                    outputBody.innerHTML = `
                        <div class="output-empty" style="color: var(--color-accent);">
                            <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                            <p style="margin-top: 1rem; font-weight: 600;">Generation Error</p>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">${data.error || 'Something went wrong.'}</p>
                        </div>
                    `;
                }
            } catch (err) {
                console.error(err);
                outputBody.innerHTML = `
                    <div class="output-empty" style="color: var(--color-accent);">
                        <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                        <p style="margin-top: 1rem; font-weight: 600;">Network Connection Failure</p>
                        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">Could not connect to server. Check server status.</p>
                    </div>
                `;
            }
        });
    };

    handleFormSubmit(blogForm, '/generate/blog/', 'blog');
    handleFormSubmit(productForm, '/generate/product/', 'product');
    handleFormSubmit(captionForm, '/generate/caption/', 'caption');

    // 7. API Keys Form Submit Handler
    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(settingsForm);

        try {
            const response = await fetch('/settings/save/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                settingsAlert.innerText = data.message;
                settingsAlert.style.display = 'block';
                setTimeout(() => {
                    settingsAlert.style.display = 'none';
                }, 4000);
            } else {
                alert('Failed to save API keys.');
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred while saving API settings.');
        }
    });

    // 8. Load History Item Detail
    async function loadHistoryItem(id, elementNode) {
        // Toggle active selection state
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.remove('active');
        });
        elementNode.classList.add('active');
        
        outputBody.innerHTML = `
            <div class="output-empty">
                <div class="spinner"></div>
                <p>Loading saved content...</p>
            </div>
        `;

        try {
            const response = await fetch(`/history/${id}/`);
            const data = await response.json();

            if (data.success) {
                displayGeneratedOutput(data.prompt, data.generated_text, data.created_at);
            } else {
                outputBody.innerHTML = `
                    <div class="output-empty">
                        <p style="color: var(--color-accent)">Failed to load history detail.</p>
                    </div>
                `;
            }
        } catch (err) {
            console.error(err);
            outputBody.innerHTML = `
                <div class="output-empty">
                    <p style="color: var(--color-accent)">Network error while loading saved details.</p>
                </div>
            `;
        }
    }

    // Attach click events to initial history items loaded in page
    document.querySelectorAll('.history-item').forEach(item => {
        const id = item.getAttribute('data-id');
        item.addEventListener('click', () => {
            loadHistoryItem(id, item);
        });
    });

    // 9. Copy to Clipboard Action
    copyBtn.addEventListener('click', async () => {
        if (!activeRawContent) return;
        
        try {
            await navigator.clipboard.writeText(activeRawContent);
            
            // Visual success feedback
            copyBtn.className = "btn btn-copy-success btn-icon";
            copyBtn.innerHTML = `
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
                Copied!
            `;
            
            setTimeout(() => {
                copyBtn.className = "btn btn-secondary btn-icon";
                copyBtn.innerHTML = `
                    <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m-2 4h5m-3-3l3 3m0 0l-3 3"/></svg>
                    Copy Copy
                `;
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
            alert('Failed to copy to clipboard.');
        }
    });

    // 10. Search History filtering
    historySearch.addEventListener('input', () => {
        const query = historySearch.value.toLowerCase().trim();
        const items = document.querySelectorAll('.history-item');
        
        items.forEach(item => {
            const prompt = item.querySelector('.history-item-prompt').innerText.toLowerCase();
            const type = item.querySelector('.history-item-type').innerText.toLowerCase();
            
            if (prompt.includes(query) || type.includes(query)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
});
