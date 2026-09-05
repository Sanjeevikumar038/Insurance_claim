document.addEventListener('DOMContentLoaded', async () => {
    const claimSelect = document.getElementById('claim-select');
    const reviewBtn = document.getElementById('btn-review');
    const resultsContainer = document.getElementById('results-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    // Summary elements
    const summaryCard = document.getElementById('claim-summary');
    const sumId = document.getElementById('summary-id');
    const sumType = document.getElementById('summary-type');
    const sumAmount = document.getElementById('summary-amount');
    const sumDocs = document.getElementById('summary-docs');
    const sumPolicy = document.getElementById('summary-policy');

    let claimsData = [];

    // Load claims
    try {
        const res = await fetch('/api/claims');
        claimsData = await res.json();
        claimSelect.innerHTML = '<option value="" disabled selected>Select a claim...</option>';
        claimsData.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.claim_id;
            opt.textContent = `${c.claim_id} - ${c.incident_type.replace('_', ' ')} (${c.claim_amount} INR)`;
            claimSelect.appendChild(opt);
        });
        
        claimSelect.addEventListener('change', () => {
            reviewBtn.disabled = !claimSelect.value;
            resultsContainer.classList.add('hidden');
            
            const selected = claimsData.find(c => c.claim_id === claimSelect.value);
            if (selected) {
                summaryCard.classList.remove('hidden');
                sumId.textContent = selected.claim_id;
                sumType.textContent = selected.incident_type.replace('_', ' ').toUpperCase();
                sumAmount.textContent = `₹${parseInt(selected.claim_amount).toLocaleString('en-IN')}`;
                sumPolicy.textContent = selected.policy_id || 'UNKNOWN';
                sumDocs.textContent = 'PENDING REVIEW';
                sumDocs.className = 'metric-value doc-status';
            }
        });
    } catch (err) {
        console.error("Failed to load claims", err);
        claimSelect.innerHTML = '<option value="" disabled selected>Error loading claims</option>';
    }

    const loadingMessages = [
        "Analyzing claim evidence...",
        "Retrieving applicable policy clauses...",
        "Running deterministic checks..."
    ];

    // Run Review
    reviewBtn.addEventListener('click', async () => {
        const claimId = claimSelect.value;
        if (!claimId) return;

        resultsContainer.classList.add('hidden');
        loadingOverlay.classList.remove('hidden');
        reviewBtn.disabled = true;

        let msgIndex = 0;
        loadingText.textContent = loadingMessages[0];
        const msgInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % loadingMessages.length;
            loadingText.textContent = loadingMessages[msgIndex];
        }, 1500);

        try {
            const res = await fetch('/api/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ claim_id: claimId })
            });

            if (!res.ok) throw new Error("API responded with " + res.status);

            const data = await res.json();
            renderResults(data);
        } catch (err) {
            console.error("Review failed", err);
            renderResults({
                recommendation: 'ERROR',
                justification: 'Failed to communicate with the backend: ' + err.message,
                flags: [],
                missing_documents: [],
                findings: []
            });
        } finally {
            clearInterval(msgInterval);
            loadingOverlay.classList.add('hidden');
            reviewBtn.disabled = false;
        }
    });

    function renderResults(data) {
        resultsContainer.classList.remove('hidden');
        
        // 1. Outcome Card
        const outcomeCard = document.getElementById('outcome-card');
        const badge = document.getElementById('recommendation-badge');
        let recClass = data.recommendation.replace(' ', '-');
        
        // Reset classes
        outcomeCard.className = 'outcome-card';
        outcomeCard.classList.add(recClass);
        badge.textContent = data.recommendation;
        document.getElementById('justification-text').textContent = data.justification;

        // 2. Missing Documents Warning
        const missingDocsSection = document.getElementById('missing-docs-section');
        const missingDocsList = document.getElementById('missing-docs-list');
        missingDocsList.innerHTML = '';
        
        if (data.missing_documents && data.missing_documents.length > 0) {
            missingDocsSection.classList.remove('hidden');
            data.missing_documents.forEach(d => {
                const li = document.createElement('li');
                li.textContent = d.toUpperCase();
                missingDocsList.appendChild(li);
            });
            sumDocs.textContent = `${data.missing_documents.length} DOCUMENT(S) MISSING`;
            sumDocs.className = 'metric-value doc-status warning';
        } else {
            missingDocsSection.classList.add('hidden');
            sumDocs.textContent = 'ALL REQUIRED PRESENT';
            sumDocs.className = 'metric-value doc-status ok';
        }

        // 3. Separate Findings
        const allFindings = data.findings || [];
        const detFindings = allFindings.filter(f => f.source_type === 'system' || f.source_type === 'structured_data');
        const semanticFindings = allFindings.filter(f => f.source_type !== 'system' && f.source_type !== 'structured_data');

        // Counters
        let supported = 0, contradicted = 0, unknown = 0;
        allFindings.forEach(f => {
            if (f.status === 'SUPPORTED') supported++;
            else if (f.status === 'CONTRADICTED') contradicted++;
            else if (f.status === 'UNKNOWN') unknown++;
        });
        document.getElementById('count-supported').textContent = supported;
        document.getElementById('count-contradicted').textContent = contradicted;
        document.getElementById('count-unknown').textContent = unknown;

        // 4. Render Deterministic Checks
        const detList = document.getElementById('deterministic-list');
        detList.innerHTML = '';
        detFindings.forEach(f => {
            const div = document.createElement('div');
            div.className = `det-item ${f.status}`;
            
            let icon = '✓';
            if (f.status === 'CONTRADICTED') icon = '✗';
            else if (f.status === 'UNKNOWN') icon = '⚠';

            div.innerHTML = `
                <div class="det-icon">${icon}</div>
                <div class="det-content">
                    <div class="det-title">${f.finding}</div>
                    <div class="det-value">${f.evidence}</div>
                    <div class="det-status-text">${f.status.replace('_', ' ')}</div>
                </div>
            `;
            detList.appendChild(div);
        });

        // 6. Render Semantic Findings
        const findingsList = document.getElementById('findings-list');
        findingsList.innerHTML = '';
        
        if (semanticFindings.length > 0) {
            semanticFindings.forEach(f => {
                const div = document.createElement('div');
                div.className = `finding-card ${f.status}`;
                
                let icon = '✓';
                if (f.status === 'CONTRADICTED') icon = '⚠';
                else if (f.status === 'UNKNOWN') icon = '?';

                let policyHtml = '';
                if (f.policy_clause) {
                    policyHtml = `
                        <div class="policy-reference">
                            <div class="meta-label">POLICY REFERENCE</div>
                            <div class="meta-value">${f.policy_clause}</div>
                        </div>
                    `;
                }

                div.innerHTML = `
                    <div class="finding-card-header">
                        <div class="status-badge ${f.status}">
                            <span>${icon}</span>
                            <span>${f.status}</span>
                        </div>
                        <div class="source-badge">${f.source_type}</div>
                    </div>
                    <div class="finding-card-body">
                        <div class="finding-text">${f.finding}</div>
                        
                        <div class="meta-grid">
                            <div class="meta-item">
                                <span class="meta-label">SOURCE LOCATION</span>
                                <span class="meta-value">${f.source_id} • ${f.source_location}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">EVIDENCE SNIPPET</span>
                                <span class="meta-value quote">"${f.evidence}"</span>
                            </div>
                        </div>
                        
                        ${policyHtml}
                    </div>
                `;
                findingsList.appendChild(div);
            });
        } else {
            findingsList.innerHTML = '<div style="color: var(--text-muted); font-style: italic; padding: 1rem;">No semantic findings extracted for this claim.</div>';
        }
    }
});
