document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('results-container');
    const resultsCount = document.getElementById('results-count');
    const loader = document.getElementById('loader');
    
    let intelligenceChart = null;

    // Fetch initial stats
    fetchStats();

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if(!query) return;

        await executeSearch(query);
    });

    async function executeSearch(query) {
        loader.classList.remove('hidden');
        resultsContainer.innerHTML = '';
        
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            resultsCount.textContent = data.total;
            
            if (data.hits.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="empty-state">
                        <p>No results found for "${query}"</p>
                    </div>`;
            } else {
                data.hits.forEach(hit => {
                    const card = createResultCard(hit);
                    resultsContainer.appendChild(card);
                });
            }

        } catch (error) {
            console.error(error);
            resultsContainer.innerHTML = `<div class="empty-state"><p style="color:var(--accent-alert)">Error executing search to Elasticsearch backend.</p></div>`;
        } finally {
            loader.classList.add('hidden');
        }
    }

    function createResultCard(hit) {
        const div = document.createElement('div');
        div.className = 'result-card';

        // Format Date
        const dateStr = hit.timestamp ? new Date(hit.timestamp).toLocaleString() : 'Unknown Date';
        
        // Highlights logic
        let snippetHtml = '';
        if (hit.highlights && hit.highlights.length > 0) {
            snippetHtml = `<div class="result-snippet">${hit.highlights.join(' ... ')}</div>`;
        }

        // Entities Logic
        let entitiesHtml = '';
        const ent = hit.entities;
        if(ent) {
            const allCrypto = [...(ent.btc_addresses||[]), ...(ent.xmr_addresses||[])];
            if(allCrypto.length > 0) {
                entitiesHtml += renderEntityGroup('Crypto Addresses', allCrypto, 'crypto');
            }
            if(ent.emails && ent.emails.length > 0) {
                entitiesHtml += renderEntityGroup('Emails', ent.emails, 'email');
            }
            if(ent.nlp_persons && ent.nlp_persons.length > 0) {
                entitiesHtml += renderEntityGroup('Persons', ent.nlp_persons, 'person');
            }
            if(ent.nlp_organizations && ent.nlp_organizations.length > 0) {
                entitiesHtml += renderEntityGroup('Organizations', ent.nlp_organizations, 'org');
            }
        }

        div.innerHTML = `
            <div class="result-header">
                <a href="${hit.url}" target="_blank" class="result-url">${hit.url}</a>
                <span class="result-time">${dateStr}</span>
            </div>
            ${snippetHtml}
            ${entitiesHtml}
        `;
        return div;
    }

    function renderEntityGroup(title, items, typeClass) {
        const tagsHtml = items.map(t => `<span class="tag ${typeClass}">${t}</span>`).join('');
        return `
            <div class="entity-group">
                <span class="entity-title">${title}</span>
                <div class="entity-tags">${tagsHtml}</div>
            </div>
        `;
    }

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stat-total-pages').textContent = data.total_pages;
            document.getElementById('stat-total-pages').classList.remove('loading');
            
            if (data.entities) {
                updateChart(data.entities);
                const totalEntities = Object.values(data.entities).reduce((a, b) => a + b, 0);
                document.getElementById('stat-entities').textContent = totalEntities;
                document.getElementById('stat-entities').classList.remove('loading');
            }
        } catch (e) {
            console.error("Stats fetch failed", e);
        }
    }

    function updateChart(entities) {
        const ctx = document.getElementById('intelligenceChart').getContext('2d');
        const labels = Object.keys(entities);
        const values = Object.values(entities);

        if (intelligenceChart) {
            intelligenceChart.destroy();
        }

        intelligenceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Extracted Entities',
                    data: values,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.5)',
                        'rgba(16, 185, 129, 0.5)',
                        'rgba(245, 158, 11, 0.5)',
                        'rgba(217, 70, 239, 0.5)',
                        'rgba(14, 165, 233, 0.5)',
                        'rgba(239, 68, 68, 0.5)'
                    ],
                    borderColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#d946ef', '#0ea5e9', '#ef4444'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#2c2d3c' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
});

