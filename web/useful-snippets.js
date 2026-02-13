/**
 * ============================================
 * MARKET RADAR - SNIPPETS ÚTEIS
 * ============================================
 * 
 * Coleção de código reutilizável para futuras
 * customizações e melhorias no UI
 * ============================================
 */

/* ============================================
   1. ANIMAÇÕES DE ENTRADA (Fade In)
   ============================================ */

/* CSS */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade -in -up {
    animation: fadeInUp 0.6s ease - out;
}

/* JavaScript - Aplicar ao scroll */
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-up');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.opp-card').forEach(card => {
    observer.observe(card);
});


/* ============================================
   2. TOAST NOTIFICATIONS (Premium)
   ============================================ */

/* CSS */
.toast {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    padding: 1rem 1.5rem;
    background: rgba(15, 23, 42, 0.95);
    backdrop - filter: blur(16px);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border - radius: 1rem;
    color: var(--text - main);
    box - shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    transform: translateX(400px);
    transition: transform 0.4s cubic - bezier(0.4, 0, 0.2, 1);
    z - index: 9999;
}

.toast.show {
    transform: translateX(0);
}

/* JavaScript */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <i data-lucide="${type === 'success' ? 'check-circle' : 'info'}" size="18"></i>
        <span style="margin-left: 0.5rem;">${message}</span>
    `;

    document.body.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// Uso:
// showToast('Oportunidade salva com sucesso!', 'success');


/* ============================================
   3. MODAL PREMIUM (Glassmorphism)
   ============================================ */

/* CSS */
.modal - overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop - filter: blur(8px);
    display: flex;
    align - items: center;
    justify - content: center;
    opacity: 0;
    pointer - events: none;
    transition: opacity 0.3s ease;
    z - index: 10000;
}

.modal - overlay.active {
    opacity: 1;
    pointer - events: all;
}

.modal - content {
    background: rgba(15, 23, 42, 0.95);
    backdrop - filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border - radius: 2rem;
    padding: 2rem;
    max - width: 600px;
    width: 90 %;
    max - height: 80vh;
    overflow - y: auto;
    box - shadow: 0 20px 60px rgba(139, 92, 246, 0.3);
    transform: scale(0.9);
    transition: transform 0.3s cubic - bezier(0.4, 0, 0.2, 1);
}

.modal - overlay.active.modal - content {
    transform: scale(1);
}

/* JavaScript */
function openModal(content) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-content">
            <button class="close-modal" style="float: right; background: none; border: none; color: var(--text-muted); cursor: pointer;">
                <i data-lucide="x" size="24"></i>
            </button>
            ${content}
        </div>
    `;

    document.body.appendChild(overlay);
    lucide.createIcons();

    setTimeout(() => overlay.classList.add('active'), 10);

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay || e.target.closest('.close-modal')) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
    });
}

// Uso:
// openModal('<h2>Detalhes da Oportunidade</h2><p>...</p>');


/* ============================================
   4. PROGRESS BAR (Topo da Página)
   ============================================ */

/* HTML - Adicionar no body */
// <div class="page-progress"></div>

/* CSS */
.page - progress {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: linear - gradient(90deg, var(--primary - purple), var(--secondary - pink));
    transform - origin: left;
    transform: scaleX(0);
    transition: transform 0.1s ease;
    z - index: 9999;
}

/* JavaScript */
window.addEventListener('scroll', () => {
    const progress = document.querySelector('.page-progress');
    if (!progress) return;

    const scrolled = window.pageYOffset;
    const height = document.body.scrollHeight - window.innerHeight;
    const percent = scrolled / height;

    progress.style.transform = `scaleX(${percent})`;
});


/* ============================================
   5. SKELETON LOADER (Premium)
   ============================================ */

/* CSS */
.skeleton - card {
    background: linear - gradient(
        90deg,
        rgba(139, 92, 246, 0.05) 0 %,
        rgba(139, 92, 246, 0.15) 50 %,
        rgba(139, 92, 246, 0.05) 100 %
    );
    background - size: 200 % 100 %;
    animation: skeleton - shimmer 2s ease -in -out infinite;
    border - radius: 1.5rem;
    height: 400px;
}

@keyframes skeleton - shimmer {
    0 % { background- position: 200 % 0;
}
100 % { background- position: -200 % 0; }
}

/* JavaScript */
function showSkeletons(count = 3) {
    const grid = document.getElementById('opportunities-grid');
    grid.innerHTML = '';

    for (let i = 0; i < count; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-card';
        grid.appendChild(skeleton);
    }
}


/* ============================================
   6. COPY TO CLIPBOARD (Premium Feedback)
   ============================================ */

/* JavaScript */
async function copyToClipboard(text, button) {
    try {
        await navigator.clipboard.writeText(text);

        // Visual feedback
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i data-lucide="check" size="16"></i> Copiado!';
        button.style.background = 'var(--neon-green)';

        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '';
            lucide.createIcons();
        }, 2000);

        showToast('Link copiado!', 'success');
    } catch (err) {
        showToast('Erro ao copiar', 'error');
    }
}

// Uso:
// <button onclick="copyToClipboard('https://...', this)">Copiar Link</button>


/* ============================================
   7. DARK/LIGHT MODE TOGGLE
   ============================================ */

/* CSS - Adicionar variáveis light mode */
[data - theme="light"] {
    --bg - slate - 900: #f8fafc;
    --bg - card: rgba(255, 255, 255, 0.8);
    --text - main: #0f172a;
    --text - muted: #475569;
}

/* JavaScript */
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Atualizar ícone do botão
    const icon = document.querySelector('.theme-toggle i');
    icon.setAttribute('data-lucide', newTheme === 'dark' ? 'sun' : 'moon');
    lucide.createIcons();
}

// Carregar tema salvo
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);


/* ============================================
   8. INFINITE SCROLL (Lazy Load)
   ============================================ */

/* JavaScript */
let currentPage = 1;
let isLoading = false;

window.addEventListener('scroll', () => {
    if (isLoading) return;

    const scrolled = window.innerHeight + window.pageYOffset;
    const threshold = document.body.offsetHeight - 500;

    if (scrolled >= threshold) {
        loadMoreOpportunities();
    }
});

async function loadMoreOpportunities() {
    isLoading = true;
    showSkeletons(3);

    try {
        currentPage++;
        const res = await fetch(`/api/ranking?page=${currentPage}&limit=10`);
        const data = await res.json();

        // Append new cards
        renderGrid(data.opportunities, true); // true = append mode
    } catch (err) {
        console.error('Error loading more:', err);
    } finally {
        isLoading = false;
    }
}


/* ============================================
   9. SEARCH/FILTER (Real-time)
   ============================================ */

/* JavaScript */
function filterOpportunities(query) {
    const cards = document.querySelectorAll('.opp-card');
    const lowerQuery = query.toLowerCase();

    cards.forEach(card => {
        const title = card.querySelector('.product-title').textContent.toLowerCase();
        const matches = title.includes(lowerQuery);

        card.style.display = matches ? 'block' : 'none';

        if (matches) {
            card.style.animation = 'fadeInUp 0.4s ease-out';
        }
    });
}

// Uso:
// <input type="text" oninput="filterOpportunities(this.value)" placeholder="Buscar...">


/* ============================================
   10. EXPORT TO CSV
   ============================================ */

/* JavaScript */
function exportToCSV(opportunities) {
    const headers = ['Keyword', 'Score', 'URL', 'Velocity', 'Gap'];
    const rows = opportunities.map(opp => [
        opp.keyword,
        opp.score,
        opp.url,
        opp.scoring_breakdown?.IndiceVelocidadeBusca || 0,
        opp.scoring_breakdown?.IndiceLacunaOferta || 0
    ]);

    const csv = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `market-radar-${Date.now()}.csv`;
    a.click();

    showToast('CSV exportado com sucesso!', 'success');
}


/* ============================================
   FIM DOS SNIPPETS
   ============================================ */
