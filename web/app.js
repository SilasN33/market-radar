/* Market Radar - SaaS Application Logic V2.0 */
/* Focus: Premium UI, Clear Hierarchy, Strategic Insights */

const API_BASE = window.location.origin + "/api";

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchUser();
    fetchOpportunities();
});

async function fetchUser() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`);
        if (res.ok) {
            const user = await res.json();
            document.getElementById('user-email').textContent = user.name || user.email.split('@')[0];
        } else {
            window.location.href = '/login.html';
        }
    } catch (e) {
        console.error("Auth failed", e);
    }
}

async function fetchOpportunities() {
    try {
        const res = await fetch(`${API_BASE}/ranking?limit=50`);
        const data = await res.json();
        renderGrid(data.opportunities || []);
    } catch (e) {
        console.error("Error fetching data:", e);
        document.getElementById('opportunities-grid').innerHTML = `
            <div style="color: var(--danger); text-align: center; grid-column: 1/-1;">
                Erro ao carregar oportunidades. Tente recarregar.
            </div>
        `;
    }
}

function renderGrid(opportunities) {
    const grid = document.getElementById('opportunities-grid');
    grid.innerHTML = ''; // Clear skeletons

    if (!opportunities.length) {
        grid.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 3rem;">Nenhuma oportunidade encontrada ainda. O radar está escaneando...</div>`;
        updateHeroStats(0, 0);
        return;
    }

    // Update Hero Stats with animated counter
    const totalSignals = opportunities.reduce((sum, opp) => sum + (opp.signal_count || 1), 0);
    updateHeroStats(totalSignals, opportunities.length);

    opportunities.forEach((opp, index) => {
        // Prepare V2 Metrics
        const score = opp.score.toFixed(1);
        const metrics = opp.scoring_breakdown || {}; // V2 Breakdown

        // Colors & Badges
        let scoreClass = 'score-low';
        let badgeHTML = '';
        let strategyText = '';

        if (score >= 80) {
            scoreClass = 'score-high';
            badgeHTML = `<span class="badge-hot">🔥 Alta Demanda</span>`;
            strategyText = "Crescimento explosivo. Ação imediata recomendada.";
        } else if (score >= 50) {
            scoreClass = 'score-med';
            badgeHTML = `<span class="badge-gap">💎 Lacuna Média</span>`;
            strategyText = "Bom potencial com competição moderada.";
        } else {
            badgeHTML = `<span class="badge-emerging">🧊 Frio</span>`;
            strategyText = "Monitorar para futuro crescimento.";
        }

        // Specific badges based on V2 Metrics
        if (metrics.IndiceLacunaOferta > 0.7) {
            badgeHTML += `<span class="badge-gap" style="margin-left:auto;">📉 Baixa Oferta</span>`;
        } else if (metrics.IndiceQualidadeConcorrencia < 0.4) {
            badgeHTML += `<span class="badge-emerging" style="margin-left:auto;">⭐ Qualidade Baixa</span>`;
        }

        // Safe Breakdown Access (with strict fallbacks)
        const v = (val) => Math.min(Math.max((val || 0) * 100, 5), 100); // Clamp 5-100%

        // Card HTML Structure
        const card = document.createElement('div');
        card.className = 'opp-card';
        card.innerHTML = `
            <div class="card-header">
                <div class="score-badge">
                    <div class="score-value ${scoreClass}">${score}</div>
                    <div class="score-label">Intent Score</div>
                </div>
                <!-- Mini Badges Container -->
                <div style="display:flex; flex-direction:column; gap:0.5rem; align-items:flex-end;">
                   ${badgeHTML}
                </div>
            </div>

            <div class="card-body">
                <img src="${opp.thumbnail || 'https://via.placeholder.com/80?text=Rad'}" 
                     class="product-thumb" alt="${opp.keyword}" 
                     onerror="this.src='https://placehold.co/80x80/1e293b/FFFFFF?text=No+Img'">
                
                <div class="product-info">
                    <h3 class="product-title">${opp.keyword}</h3>
                    <div class="product-meta">
                        ${strategyText}
                    </div>
                </div>
            </div>

            <!-- V2 Metrics Breakdown -->
            <div class="breakdown-container">
                <!-- Velocity -->
                <div class="metric-row">
                    <span class="metric-label">Velocidade</span>
                    <div class="metric-bar-bg">
                        <div class="metric-bar-fill" style="width: ${v(metrics.IndiceVelocidadeBusca || metrics.velocity_score)}%; background: #ef4444;"></div>
                    </div>
                    <span class="metric-value">${(v(metrics.IndiceVelocidadeBusca || metrics.velocity_score)).toFixed(0)}</span>
                </div>

                <!-- Gap (Supply) -->
                <div class="metric-row">
                    <span class="metric-label">Lacuna</span>
                    <div class="metric-bar-bg">
                        <div class="metric-bar-fill" style="width: ${v(metrics.IndiceLacunaOferta)}%; background: #10b981;"></div>
                    </div>
                    <span class="metric-value">${(v(metrics.IndiceLacunaOferta)).toFixed(0)}</span>
                </div>

                <!-- Quality Gap -->
                <div class="metric-row">
                    <span class="metric-label">Oportun.</span>
                    <div class="metric-bar-bg">
                        <div class="metric-bar-fill" style="width: ${v(1 - (metrics.IndiceQualidadeConcorrencia || 0.8))}%; background: #f59e0b;"></div>
                    </div>
                    <span class="metric-value">${(v(1 - (metrics.IndiceQualidadeConcorrencia || 0.8))).toFixed(0)}</span>
                </div>
            </div>

            <div class="card-actions">
                <a href="${opp.url}" target="_blank" class="btn btn-outline">
                    <i data-lucide="external-link" size="16"></i> Ver no ML
                </a>
                <button class="btn btn-primary" onclick="analyzeDetails('${opp.id}')">
                    <i data-lucide="bar-chart-2" size="16"></i> Detalhes
                </button>
            </div>
        `;

        // Future Conversion: Lock items after top 3?
        // if (index > 2 && user.role === 'free') { 
        //    card.classList.add('premium-lock'); 
        //    const overlay = document.createElement('div');
        //    overlay.className = 'lock-overlay';
        //    overlay.innerHTML = '<i data-lucide="lock"></i> Upgrade para ver';
        //    card.appendChild(overlay);
        // }

        grid.appendChild(card);
    });

    // Re-init icons for dynamic content
    lucide.createIcons();

    // Initialize 3D Tilt Effect
    initTiltEffect();
}

/**
 * Vanilla JS 3D Tilt Effect (Lightweight, no dependencies)
 * Aplica rotação 3D sutil nos cards baseado na posição do mouse
 */
function initTiltEffect() {
    const cards = document.querySelectorAll('.opp-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', handleTilt);
        card.addEventListener('mouseleave', resetTilt);
    });
}

function handleTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();

    // Calcular posição do mouse relativa ao centro do card (0 a 1)
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    // Converter para graus de rotação (-15deg a +15deg)
    const tiltX = (y - 0.5) * -20; // Inverte Y para efeito natural
    const tiltY = (x - 0.5) * 20;

    // Aplicar transform com suavidade
    card.style.transform = `
        translateY(-8px) 
        perspective(1000px) 
        rotateX(${tiltX}deg) 
        rotateY(${tiltY}deg)
        scale3d(1.02, 1.02, 1.02)
    `;

    // Adicionar brilho sutil que segue o mouse
    const glowX = x * 100;
    const glowY = y * 100;
    card.style.background = `
        radial-gradient(circle at ${glowX}% ${glowY}%, 
            rgba(139, 92, 246, 0.15), 
            transparent 50%),
        var(--bg-card-hover)
    `;
}

function resetTilt(e) {
    const card = e.currentTarget;

    // Reset suave para posição original
    card.style.transform = 'translateY(-8px) perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    card.style.background = '';

    // Após a transição, remove o translateY para evitar conflito com hover CSS
    setTimeout(() => {
        if (!card.matches(':hover')) {
            card.style.transform = '';
        }
    }, 400);
}

function analyzeDetails(id) {
    alert("Funcionalidade 'Deep Dive Analysis' disponível em breve no plano Pro!");
}

/**
 * Update Hero Section Stats with Animated Counter
 */
function updateHeroStats(signals, opportunities) {
    const signalsEl = document.getElementById('live-signals');
    const oppsEl = document.getElementById('live-opportunities');

    if (!signalsEl || !oppsEl) return;

    // Animated counter effect
    animateCounter(signalsEl, 0, signals, 1500);
    animateCounter(oppsEl, 0, opportunities, 1200);
}

function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    const range = end - start;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (easeOutCubic)
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (range * easeProgress));

        element.textContent = current.toLocaleString('pt-BR');

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}
