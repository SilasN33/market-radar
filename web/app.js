// Market Radar Dashboard - Intent Engine v2.0

// Estado da aplicação
let allOpportunities = [];
let categories = new Set();
const API_BASE = window.location.origin;
let currentUser = null;

// Check authentication on load
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            credentials: 'include'
        });

        if (response.ok) {
            currentUser = await response.json();
            updateUIForUser();
        } else {
            // Redirect to login if not authenticated
            if (window.location.pathname !== '/login.html') {
                window.location.href = '/login.html';
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

function updateUIForUser() {
    // Add user info to header if element exists
    const header = document.querySelector('.header-stats');
    if (header && currentUser) {
        const userInfo = document.createElement('div');
        userInfo.className = 'stat-pill';
        userInfo.innerHTML = `
            <span class="stat-label">${currentUser.name || currentUser.email}</span>
            <span class="stat-value" style="font-size:0.75em;">${currentUser.role.toUpperCase()} | ${currentUser.credits} créditos</span>
        `;
        header.appendChild(userInfo);

        // Add logout button
        const logoutBtn = document.createElement('button');
        logoutBtn.className = 'btn-refresh';
        logoutBtn.innerHTML = 'Sair';
        logoutBtn.style.marginLeft = '1rem';
        logoutBtn.onclick = async () => {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    credentials: 'include'
                });
                window.location.href = '/login.html';
            } catch (e) {
                alert('Erro ao fazer logout');
            }
        };
        header.appendChild(logoutBtn);
    }
}

// Função para formatar data
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Desconhecido';
    try {
        const year = timestamp.substring(0, 4);
        const month = timestamp.substring(4, 6);
        const day = timestamp.substring(6, 8);
        const hour = timestamp.substring(9, 11);
        const minute = timestamp.substring(11, 13);
        return `${day}/${month}/${year} às ${hour}:${minute}`;
    } catch (e) {
        return timestamp;
    }
}

// Função para criar card de oportunidade (INTENT FOCUSED)
function createOpportunityCard(opportunity, index) {
    const card = document.createElement('div');
    card.className = 'opportunity-card';
    card.style.animationDelay = `${index * 0.05}s`;

    const score = opportunity.score || 0;
    const scorePercent = Math.min(score, 100);

    const meta = opportunity.meta || {};
    const signals = opportunity.signals || {};

    // Extrair dados (Prioritize Intent Data)
    const cluster = opportunity.cluster || meta.category || meta.marketplace || 'Oportunidade';
    const marketplace = meta.marketplace || 'Mercado Livre';
    const thumbnail = meta.thumbnail || '';
    const price = meta.price || 'N/A';
    const rating = meta.rating || '0.0';
    const prime = meta.prime || '';
    const freeShipping = meta.free_shipping === 'Sim' || meta.free_shipping === true;
    const url = meta.url || meta.example_url || '#';
    const title = meta.title || opportunity.keyword;

    // New Intent Fields
    const buyingIntent = meta.buying_intent || '';
    const whyTrending = meta.why_trending || '';

    // Adicionar categoria ao set
    if (cluster) categories.add(cluster);

    // Determinar ícone
    let defaultIcon = '📦';
    if (marketplace.includes('Amazon')) defaultIcon = '🛒';

    // Card HTML with Intent Data
    card.innerHTML = `
        <div class="card-rank">#${index + 1}</div>
        
        ${thumbnail ? `
            <div class="card-thumbnail">
                <img src="${thumbnail}" alt="${title}" loading="lazy" onerror="this.parentElement.classList.add('no-image'); this.style.display='none'; this.parentElement.innerHTML += '${defaultIcon}';">
            </div>
        ` : `
            <div class="card-thumbnail no-image">${defaultIcon}</div>
        `}
        
        <div class="card-content">
            <div class="card-header">
                <span class="card-category" style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:0.75em; font-weight:600; text-transform:uppercase;">${cluster}</span>
                <h3 class="card-title">${opportunity.keyword}</h3>
                
                ${buyingIntent ? `
                    <div style="font-size: 0.85em; color: #334155; margin-top: 6px; font-weight:500;">
                        🎯 ${buyingIntent}
                    </div>
                ` : ''}
                
                ${whyTrending ? `
                    <div style="font-size: 0.75em; color: #64748b; margin-top: 4px; font-style: italic; line-height:1.3;">
                        💡 ${whyTrending.substring(0, 100)}${whyTrending.length > 100 ? '...' : ''}
                    </div>
                ` : ''}
            </div>
            
            <div class="card-score">
                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>
                <div class="score-value">${score.toFixed(1)}</div>
            </div>
            
            <div class="card-metrics" style="display:flex; justify-content:space-between; margin-top:10px;">
                <div class="metric" title="Confiança da IA na Intenção">
                    <div class="metric-label" style="font-size:0.7em; color:#888;">INTENÇÃO</div>
                    <div class="metric-value" style="font-weight:bold;">${((signals.intent_confidence || 0) * 100).toFixed(0)}%</div>
                </div>
                <div class="metric" title="Validação de Mercado (Scraper)">
                    <div class="metric-label" style="font-size:0.7em; color:#888;">MERCADO</div>
                    <div class="metric-value" style="font-weight:bold;">${((signals.market_validation || 0) * 100).toFixed(0)}%</div>
                </div>
                 <div class="metric" title="Competição Estimada">
                    <div class="metric-label" style="font-size:0.7em; color:#888;">COMPETIÇÃO</div>
                    <div class="metric-value" style="font-weight:bold;">${((signals.competition || 0.5) * 100).toFixed(0)}%</div>
                </div>
            </div>
            
            <div class="card-footer" style="margin-top:auto; padding-top:10px; display:flex; gap:5px; flex-wrap:wrap;">
                ${price !== 'N/A' ? `<span class="badge info">💰 ${price}</span>` : ''}
                ${freeShipping ? `<span class="badge success">🚚 Free</span>` : ''}
                <span class="badge primary">${marketplace}</span>
            </div>
            
            ${url !== '#' ? `
                <div class="card-link" style="margin-top:10px;">
                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="btn-view" style="display:block; text-align:center; padding:6px; background:#f1f5f9; border-radius:4px; text-decoration:none; color:#0f172a; font-weight:600; font-size:0.85em;">
                        Ver Oportunidade →
                    </a>
                </div>
            ` : ''}
        </div>
    `;

    return card;
}

// Função para renderizar oportunidades
function renderOpportunities(opportunities) {
    const grid = document.getElementById('opportunities-grid');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const totalEl = document.getElementById('total-opps');

    if (totalEl) totalEl.textContent = opportunities.length;

    grid.innerHTML = ''; // Clear

    loadingState.style.display = 'none';
    errorState.style.display = 'none';
    grid.style.display = 'grid';

    if (opportunities.length === 0) {
        grid.style.display = 'none';
        // emptyState logic handled if needed
        return;
    }

    opportunities.forEach((opp, index) => {
        const card = createOpportunityCard(opp, index);
        grid.appendChild(card);
    });
}

// Função para carregar estatísticas
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();

        // Update KPI Cards
        const totalProducts = data.total_products || (data.mercado_livre_products + data.amazon_products) || 0;

        // Update header/sidebar counters if exist
        const mlCountEl = document.getElementById('ml-count');
        if (mlCountEl) mlCountEl.textContent = `Produtos Monitorados: ${totalProducts}`;

        // If specific KPI cards exist (assuming IDs based on common patterns)
        const avgScoreEl = document.getElementById('avg-score');
        if (avgScoreEl) avgScoreEl.textContent = (data.avg_score || 0).toFixed(1);

    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

// Função para carregar dados do ranking
async function loadRanking() {
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const grid = document.getElementById('opportunities-grid');

    // Only show full loading state on first load or if grid is empty
    if (grid.children.length === 0) loadingState.style.display = 'flex';
    errorState.style.display = 'none';

    try {
        // Force timestamp to avoid cache
        const response = await fetch(`${API_BASE}/api/ranking?t=${Date.now()}`);
        if (!response.ok) throw new Error('Dados não disponíveis');

        const data = await response.json();

        // Handle new API format
        allOpportunities = data.opportunities || [];
        categories.clear();

        renderOpportunities(allOpportunities);
        populateCategoryFilter();
        loadStats(); // Refresh stats with ranking

    } catch (error) {
        console.error('Erro ao carregar ranking:', error);
        loadingState.style.display = 'none';
        if (grid.children.length === 0) errorState.style.display = 'flex';
    }
}

// Filtros
function populateCategoryFilter() {
    const select = document.getElementById('category-filter');
    if (!select) return;

    // Save current selection
    const currentVal = select.value;

    select.innerHTML = '<option value="all">Todas as Intenções</option>';
    const sortedCategories = Array.from(categories).sort();
    sortedCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        select.appendChild(option);
    });

    // Restore selection if valid
    if (Array.from(select.options).some(o => o.value === currentVal)) {
        select.value = currentVal;
    }
}

function filterOpportunities() {
    const categoryFilter = document.getElementById('category-filter')?.value || 'all';
    const sortFilter = document.getElementById('sort-filter')?.value || 'score';
    const searchInput = document.getElementById('search-input')?.value.toLowerCase() || '';

    let filtered = [...allOpportunities];

    if (categoryFilter !== 'all') {
        filtered = filtered.filter(opp => (opp.cluster || opp.meta?.category) === categoryFilter);
    }

    if (searchInput) {
        filtered = filtered.filter(opp => {
            const kw = (opp.keyword || '').toLowerCase();
            const cluster = (opp.cluster || '').toLowerCase();
            const intent = (opp.meta?.buying_intent || '').toLowerCase();
            return kw.includes(searchInput) || cluster.includes(searchInput) || intent.includes(searchInput);
        });
    }

    // Sort
    if (sortFilter === 'score') {
        filtered.sort((a, b) => (b.score || 0) - (a.score || 0));
    } else if (sortFilter === 'validation') {
        filtered.sort((a, b) => (a.signals?.market_validation || 0) - (b.signals?.market_validation || 0));
    }

    renderOpportunities(filtered);
}

// --- MARKET EXPLORER FEATURES ---

function createSimpleProductCard(product) {
    const card = document.createElement('div');
    card.className = 'opportunity-card'; // Reuse style
    card.style.animation = 'fadeInUp 0.5s ease-out forwards';

    // Fallbacks
    const marketplace = product.marketplace || 'Mercado Livre';
    const keyword = product.search_keyword || 'Produto';
    const price = product.price ? `R$ ${product.price.toFixed(2)}` : 'N/A';
    const thumb = product.thumbnail || '';
    const link = product.permalink || '#';
    const title = product.title || 'Produto sem nome';

    let defaultIcon = '📦';
    if (marketplace.includes('Amazon')) defaultIcon = '🛒';

    card.innerHTML = `
        <div style="position:absolute; top:10px; right:10px; background:rgba(0,0,0,0.6); color:white; padding:4px 8px; border-radius:4px; font-size:0.7em; z-index:10;">
            ${marketplace}
        </div>
        
        ${thumb ? `
            <div class="card-thumbnail">
                <img src="${thumb}" alt="${title}" loading="lazy" style="object-fit:contain; padding:10px;" onerror="this.parentElement.classList.add('no-image'); this.style.display='none'; this.parentElement.innerHTML += '${defaultIcon}';">
            </div>
        ` : `
            <div class="card-thumbnail no-image">${defaultIcon}</div>
        `}
        
        <div class="card-content">
            <div class="card-header" style="margin-bottom:0.5rem;">
                <span class="card-category" style="background:#f1f5f9; color:#64748b; font-size:0.7em;">Busca: ${keyword}</span>
                <h3 class="card-title" style="font-size:1em; height:3em; overflow:hidden; margin-top:5px;">${title}</h3>
            </div>
            
            <div style="font-size:1.25em; font-weight:800; color:#fff; margin:10px 0;">
                ${price}
            </div>
            
            ${link !== '#' ? `
                <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn-view" style="margin-top:auto;">
                    Ver no Site
                </a>
            ` : ''}
        </div>
    `;

    return card;
}

async function loadAllProducts() {
    const btn = document.getElementById('btn-load-products');
    const loading = document.getElementById('products-loading');
    const grid = document.getElementById('products-grid');

    if (btn) btn.style.display = 'none';
    if (loading) loading.style.display = 'flex';
    if (grid) grid.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/api/products`);
        const data = await response.json();

        if (loading) loading.style.display = 'none';

        const products = data.products || [];

        if (products.length === 0) {
            grid.innerHTML = '<div class="empty-state"><h3>Nenhum produto encontrado.</h3><p>Execute os scrapers para popular a base.</p></div>';
            return;
        }

        // Render
        products.forEach(p => {
            grid.appendChild(createSimpleProductCard(p));
        });

        // Update button text to show count
        if (btn) {
            btn.style.display = 'inline-block';
            btn.textContent = `Atualizar Lista (${products.length} itens)`;
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-secondary'); // You might need to add style for secondary if not assumes basic button behavior
            btn.style.background = '#334155';
        }

    } catch (e) {
        console.error("Erro ao carregar produtos:", e);
        if (loading) loading.style.display = 'none';
        if (grid) grid.innerHTML = `<div class="error-state"><p>Erro ao carregar produtos: ${e.message}</p></div>`;
        if (btn) btn.style.display = 'inline-block';
    }
}

// Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check auth first
    checkAuth();

    loadRanking();

    // Event Bindings
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.addEventListener('input', filterOpportunities);

    const catFilter = document.getElementById('category-filter');
    if (catFilter) catFilter.addEventListener('change', filterOpportunities);

    const sortFilter = document.getElementById('sort-filter');
    if (sortFilter) sortFilter.addEventListener('change', filterOpportunities);

    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', loadRanking);

    // Refresh loop ranking only
    setInterval(loadRanking, 5 * 60 * 1000);
});

// --- NEW FEATURES (Phase 3) ---

async function saveOpportunity(index) {
    const opp = allOpportunities[index];
    if (!opp || !opp.id) {
        alert('Oportunidade inválida');
        return;
    }

    const notes = prompt('Adicionar notas (opcional):');

    try {
        const response = await fetch(`${API_BASE}/api/auth/save/${opp.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ notes: notes || '' })
        });

        if (response.ok) {
            showToast('✅ Oportunidade salva com sucesso!');
        } else {
            const data = await response.json();
            alert(data.error || 'Erro ao salvar');
        }
    } catch (e) {
        alert('Erro de conexão');
    }
}

function showDetails(index) {
    const opp = allOpportunities[index];
    if (!opp) return;

    const modal = document.createElement('div');
    modal.id = 'details-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease;
    `;

    const signals = opp.signals || {};
    const analysis = opp.analysis || {};
    const meta = opp.meta || {};

    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(20, 20, 40, 0.95));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2.5rem;
            max-width: 800px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            position: relative;
        ">
            <button onclick="document.getElementById('details-modal').remove()" style="
                position: absolute;
                top: 1rem;
                right: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 1.25rem;
                display: flex;
                align-items: center;
                justify-content: center;
            ">×</button>
            
            <h2 style="margin: 0 0 1rem 0; font-size: 1.75rem; color: white;">${opp.keyword}</h2>
            <p style="color: #94a3b8; margin-bottom: 2rem; font-size: 0.95rem;">${opp.cluster || 'Oportunidade'}</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div style="background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid rgba(102, 126, 234, 0.3);">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.25rem;">SCORE TOTAL</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">${opp.score || 0}</div>
                </div>
                <div style="background: rgba(34, 197, 94, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.25rem;">INTENÇÃO</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">${((signals.intent_confidence || 0) * 100).toFixed(0)}%</div>
                </div>
                <div style="background: rgba(147, 51, 234, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid rgba(147, 51, 234, 0.3);">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.25rem;">VALIDAÇÃO</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">${((signals.market_validation || 0) * 100).toFixed(0)}%</div>
                </div>
            </div>
            
            ${meta.buying_intent ? `
                <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 12px; border-left: 4px solid #667eea;">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.5rem; font-weight: 600;">🎯 INTENÇÃO DE COMPRA</div>
                    <div style="color: white; line-height: 1.6;">${meta.buying_intent}</div>
                </div>
            ` : ''}
            
            ${meta.why_trending ? `
                <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 12px; border-left: 4px solid #22c55e;">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.5rem; font-weight: 600;">💡 POR QUE ESTÁ EM ALTA</div>
                    <div style="color: white; line-height: 1.6;">${meta.why_trending}</div>
                </div>
            ` : ''}
            
            ${analysis.risk ? `
                <div style="margin-bottom: 1.5rem; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 12px; border-left: 4px solid #ef4444;">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.5rem; font-weight: 600;">⚠️ RISCOS</div>
                    <div style="color: #fca5a5; line-height: 1.6;">${analysis.risk}</div>
                </div>
            ` : ''}
            
            <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                ${meta.url ? `
                    <a href="${meta.url}" target="_blank" style="
                        flex: 1;
                        padding: 1rem;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 12px;
                        text-align: center;
                        text-decoration: none;
                        color: white;
                        font-weight: 600;
                    ">Ver no Marketplace →</a>
                ` : ''}
                <button onclick="saveOpportunity(${index})" style="
                    flex: 1;
                    padding: 1rem;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                ">⭐ Salvar Oportunidade</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function showToast(message, duration = 3000) {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        font-weight: 600;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
