document.addEventListener('DOMContentLoaded', async () => {
    const claimSelect = document.getElementById('claim-select');
    const reviewBtn = document.getElementById('btn-review');
    const resultsContainer = document.getElementById('results-container');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Load claims
    try {
        const res = await fetch('/api/claims');
        const claims = await res.json();
        claimSelect.innerHTML = '<option value="" disabled selected>Select a claim...</option>';
        claims.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.claim_id;
            opt.textContent = `${c.claim_id} - ${c.incident_type.replace('_', ' ')} (${c.claim_amount} INR)`;
            claimSelect.appendChild(opt);
        });
        claimSelect.addEventListener('change', () => {
            reviewBtn.disabled = !claimSelect.value;
        });
    } catch (err) {
        console.error("Failed to load claims", err);
        claimSelect.innerHTML = '<option value="" disabled selected>Error loading claims</option>';
    }

    // Run Review
    reviewBtn.addEventListener('click', async () => {
        const claimId = claimSelect.value;
        if (!claimId) return;

        resultsContainer.classList.add('hidden');
        loadingOverlay.classList.remove('hidden');

        try {
            const res = await fetch('/api/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ claim_id: claimId })
            });

            if (!res.ok) {
                throw new Error("API responded with " + res.status);
            }

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
            loadingOverlay.classList.add('hidden');
        }
    });

    function renderResults(data) {
        resultsContainer.classList.remove('hidden');
        
        // Recommendation Badge
        const badge = document.getElementById('recommendation-badge');
        let recClass = data.recommendation.replace(' ', '-');
        badge.className = `badge ${recClass}`;
        badge.textContent = data.recommendation;

        // Justification
        document.getElementById('justification-text').textContent = data.justification;

        // Flags
        const flagsCard = document.getElementById('flags-card');
        const flagsList = document.getElementById('flags-list');
        flagsList.innerHTML = '';
        if (data.flags && data.flags.length > 0) {
            flagsCard.classList.remove('hidden');
            data.flags.forEach(f => {
                const li = document.createElement('li');
                li.textContent = f;
                flagsList.appendChild(li);
            });
        } else {
            flagsCard.classList.add('hidden');
        }

        // Missing Docs
        const missingDocsCard = document.getElementById('missing-docs-card');
        const missingDocsList = document.getElementById('missing-docs-list');
        missingDocsList.innerHTML = '';
        if (data.missing_documents && data.missing_documents.length > 0) {
            missingDocsCard.classList.remove('hidden');
            data.missing_documents.forEach(d => {
                const li = document.createElement('li');
                li.textContent = d;
                missingDocsList.appendChild(li);
            });
        } else {
            missingDocsCard.classList.add('hidden');
        }

        // Findings
        const findingsList = document.getElementById('findings-list');
        findingsList.innerHTML = '';
        if (data.findings && data.findings.length > 0) {
            data.findings.forEach(f => {
                const div = document.createElement('div');
                div.className = `finding-item ${f.status}`;
                div.innerHTML = `
                    <div class="finding-header">
                        <span class="finding-status ${f.status}">${f.status}</span>
                    </div>
                    <div class="finding-content">${f.finding}</div>
                    <div class="finding-meta">
                        <p><strong>Source:</strong> ${f.source_type} (${f.source_id}) - <em>${f.source_location}</em></p>
                        <p><strong>Evidence:</strong> "${f.evidence}"</p>
                        ${f.policy_clause ? `<p><strong>Clause:</strong> ${f.policy_clause}</p>` : ''}
                    </div>
                `;
                findingsList.appendChild(div);
            });
        } else {
            findingsList.innerHTML = '<p style="color: #94a3b8">No specific findings extracted.</p>';
        }
    }
});
