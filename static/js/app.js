// Camelot Poker Calculator - Enhanced Interactive JavaScript

const RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = [
    { symbol: '♠', name: 'spades', color: 'black' },
    { symbol: '♥', name: 'hearts', color: 'red' },
    { symbol: '♦', name: 'diamonds', color: 'red' },
    { symbol: '♣', name: 'clubs', color: 'black' }
];

// State management
const state = {
    selectedCards: [], // Ordered list of selected cards
    numOpponents: 0,
    history: [] // History of solved hands
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    generateCardGrid();
    setupEventListeners();
    loadHistory();
    updateUI();
    updateHistoryTicker();
});

// Create animated background particles
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 60; // Doubled particle density again
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random size
        const size = Math.random() * 30 + 10;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // Random horizontal position
        particle.style.left = Math.random() * 100 + '%';
        
        // Start particles from bottom or middle of screen, never from top
        const startPosition = 50 + Math.random() * 50; // 50% to 100% down the page
        particle.style.bottom = `-${size}px`; // Start just below viewport
        particle.style.top = 'auto';
        
        // Random animation delay and duration
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (Math.random() * 20 + 20) + 's';
        
        particlesContainer.appendChild(particle);
    }
}

// Generate single card grid
function generateCardGrid() {
    const grid = document.getElementById('cardGrid');
    grid.innerHTML = '';
    
    // Generate cards sorted by suit (all spades, then hearts, then diamonds, then clubs)
    // Within each suit, cards are already in rank order (A, K, Q, J, 10, 9, 8, 7, 6, 5, 4, 3, 2)
    SUITS.forEach(suit => {
        RANKS.forEach(rank => {
            const cardId = `${rank}${suit.symbol}`;
            const card = createCardElement(cardId, rank, suit);
            grid.appendChild(card);
        });
    });
}

// Create a card element
function createCardElement(cardId, rank, suit) {
    const card = document.createElement('div');
    card.className = `card ${suit.color === 'red' ? 'red' : ''}`;
    card.dataset.card = cardId;
    card.innerHTML = `
        ${rank}
        <span class="suit-icon">${suit.symbol}</span>
    `;
    
    card.addEventListener('click', () => handleCardClick(cardId));
    
    // Add entrance animation
    card.style.animationDelay = `${Math.random() * 0.3}s`;
    card.classList.add('flip-in');
    
    return card;
}

// Handle card selection with new logic
function handleCardClick(cardId) {
    const cardIndex = state.selectedCards.indexOf(cardId);
    
    if (cardIndex !== -1) {
        // Card is already selected, remove it
        state.selectedCards.splice(cardIndex, 1);
        updateCardVisuals();
    } else if (state.selectedCards.length < 7) {
        // Add the card
        state.selectedCards.push(cardId);
        updateCardVisuals();
        
        // Trigger haptic feedback on mobile
        if (window.navigator.vibrate) {
            window.navigator.vibrate(10);
        }
    } else {
        showMessage('Maximum 7 cards (2 hand + 5 board)', 'error');
    }
}

// Update card visuals based on selection
function updateCardVisuals() {
    // Reset all cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.remove('selected', 'hero-card', 'board-card', 'flip-in');
        // Reset any inline styles that might have been applied
        card.style.transform = '';
        card.style.opacity = '';
        const badge = card.querySelector('.selection-badge');
        if (badge) badge.remove();
    });
    
    // Update selected cards
    state.selectedCards.forEach((cardId, index) => {
        const card = document.querySelector(`[data-card="${cardId}"]`);
        if (card) {
            // Add classes with a slight delay for animation
            setTimeout(() => {
                card.classList.add('selected');
                
                // Add appropriate class based on position
                if (index < 2) {
                    card.classList.add('hero-card');
                } else {
                    card.classList.add('board-card');
                }
                
                // Add selection badge with number
                const badge = document.createElement('div');
                badge.className = 'selection-badge';
                badge.textContent = index + 1;
                card.appendChild(badge);
            }, index * 30); // Stagger the animations
        }
    });
    
    updateUI();
}

// Setup event listeners
function setupEventListeners() {
    // Opponent selection
    document.querySelectorAll('.opponent-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const opponents = parseInt(btn.dataset.opponents);
            state.numOpponents = opponents;
            
            // Update visual state with animation
            document.querySelectorAll('.opponent-btn').forEach(b => {
                b.classList.remove('selected');
            });
            btn.classList.add('selected');
            
            // Pulse animation
            btn.style.animation = 'pulse 0.3s ease-out';
            setTimeout(() => btn.style.animation = '', 300);
            
            updateUI();
        });
    });
    
    // Calculate button
    document.getElementById('calculateBtn').addEventListener('click', calculateOdds);
    
    // Clear button
    document.getElementById('clearBtn').addEventListener('click', clearAll);
    
    // Handle window resize for responsive layout
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check
}

// Handle responsive layout
function handleResize() {
    // Layout is now handled by CSS media queries
    // This function kept for potential future use
}

// Update UI state
function updateUI() {
    // Update status cards
    const heroCards = state.selectedCards.slice(0, 2);
    const boardCards = state.selectedCards.slice(2);
    
    // Hero status
    const heroStatus = document.getElementById('heroStatus');
    const heroValue = heroStatus.querySelector('.status-value');
    if (heroCards.length === 0) {
        heroValue.textContent = '-';
        heroStatus.classList.remove('active');
    } else {
        heroValue.textContent = heroCards.join(' ');
        heroStatus.classList.toggle('active', heroCards.length === 2);
    }
    
    // Board status
    const boardStatus = document.getElementById('boardStatus');
    const boardValue = boardStatus.querySelector('.status-value');
    const boardHint = document.getElementById('boardHint');
    
    if (boardCards.length === 0) {
        boardValue.textContent = '-';
        boardStatus.classList.remove('active', 'warning');
        boardHint.style.display = 'none';
    } else {
        boardValue.textContent = boardCards.join(' ');
        const validBoard = boardCards.length >= 3 && boardCards.length <= 5;
        boardStatus.classList.toggle('active', validBoard);
        boardStatus.classList.toggle('warning', boardCards.length > 0 && boardCards.length < 3);
        
        // Show hint for invalid board size
        boardHint.style.display = (boardCards.length > 0 && boardCards.length < 3) ? 'inline' : 'none';
    }
    
    // Opponent status
    const opponentStatus = document.getElementById('opponentStatus');
    const opponentValue = opponentStatus.querySelector('.status-value');
    if (state.numOpponents === 0) {
        opponentValue.textContent = '-';
        opponentStatus.classList.remove('active');
    } else {
        opponentValue.textContent = state.numOpponents;
        opponentStatus.classList.add('active');
    }
    
    // Enable/disable calculate button
    const calculateBtn = document.getElementById('calculateBtn');
    // Can calculate if: 2 hero cards, has opponents, and board is either 0 or 3-5 cards
    const validBoardSize = boardCards.length === 0 || (boardCards.length >= 3 && boardCards.length <= 5);
    const canCalculate = heroCards.length === 2 && state.numOpponents > 0 && validBoardSize;
    calculateBtn.disabled = !canCalculate;
    
    // Update button text with helpful message
    if (heroCards.length !== 2) {
        calculateBtn.textContent = 'Select 2 hole cards';
    } else if (state.numOpponents === 0) {
        calculateBtn.textContent = 'Select opponents';
    } else if (boardCards.length > 0 && boardCards.length < 3) {
        calculateBtn.textContent = `Add ${3 - boardCards.length} more board card${3 - boardCards.length > 1 ? 's' : ''}`;
    } else {
        calculateBtn.textContent = 'Calculate Odds';
    }
    
    if (canCalculate) {
        calculateBtn.classList.add('pulse-glow');
    } else {
        calculateBtn.classList.remove('pulse-glow');
    }
}

// Calculate odds with enhanced visuals
async function calculateOdds() {
    const loading = document.getElementById('loading');
    const heroCards = state.selectedCards.slice(0, 2);
    const boardCards = state.selectedCards.slice(2);
    
    // Show loading
    loading.style.display = 'block';
    
    // Prepare request data
    const requestData = {
        hero_hand: heroCards,
        num_opponents: state.numOpponents,
        board_cards: boardCards.length > 0 ? boardCards : null,
        simulation_mode: 'default'
    };
    
    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle validation errors specifically
            if (response.status === 422) {
                const errorDetail = data.detail?.[0]?.msg || data.detail || 'Invalid card configuration';
                showMessage(`Validation error: ${errorDetail}`, 'error');
            } else {
                showMessage(`Server error: ${response.status}`, 'error');
            }
            return;
        }
        
        if (data.success) {
            displayResults(data);
            addToHistory(data);
        } else {
            showMessage(data.error || 'Calculation failed', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
    } finally {
        loading.style.display = 'none';
    }
}

// Display results with enhanced animations
function displayResults(data) {
    const isLandscape = window.innerWidth > 1024;
    
    if (isLandscape) {
        // Show side panel
        document.getElementById('resultsPanel').classList.add('active');
        updateResultsDisplay('', data);
        // Hide mobile results if they were visible
        document.getElementById('mobileResults').style.display = 'none';
    } else {
        // Show mobile results
        document.getElementById('mobileResults').style.display = 'block';
        updateResultsDisplay('Mobile', data);
        // Make sure desktop panel is hidden
        document.getElementById('resultsPanel').classList.remove('active');
    }
}

// Update results display
function updateResultsDisplay(suffix, data) {
    const winBar = document.getElementById('winBar' + suffix);
    const tieBar = document.getElementById('tieBar' + suffix);
    const lossBar = document.getElementById('lossBar' + suffix);
    const details = document.getElementById('resultDetails' + suffix);
    
    const winPct = (data.win_probability * 100).toFixed(1);
    const tiePct = (data.tie_probability * 100).toFixed(1);
    const lossPct = (data.loss_probability * 100).toFixed(1);
    
    // Animate bars
    setTimeout(() => {
        winBar.style.width = winPct + '%';
        winBar.innerHTML = `<span style="font-size: 0.9rem;">WIN</span><br>${winPct}%`;
        
        tieBar.style.width = tiePct + '%';
        if (parseFloat(tiePct) > 5) {
            tieBar.innerHTML = `<span style="font-size: 0.8rem;">TIE</span><br>${tiePct}%`;
        }
        
        lossBar.style.width = lossPct + '%';
        lossBar.innerHTML = `<span style="font-size: 0.9rem;">LOSS</span><br>${lossPct}%`;
    }, 100);
    
    // Update details with enhanced visuals
    details.innerHTML = `
        <div class="result-stats">
            <div class="stat-card" style="animation: slideUp 0.3s ease-out">
                <h4>🎯 Simulations</h4>
                <div class="value">${data.simulations_run.toLocaleString()}</div>
            </div>
            <div class="stat-card" style="animation: slideUp 0.4s ease-out">
                <h4>⚡ Speed</h4>
                <div class="value">${data.execution_time_ms.toFixed(0)}ms</div>
            </div>
            <div class="stat-card" style="animation: slideUp 0.5s ease-out">
                <h4>📊 Confidence</h4>
                <div class="value">±${((data.confidence_interval[1] - data.confidence_interval[0]) * 50).toFixed(1)}%</div>
            </div>
        </div>
        <div class="hand-strength" style="animation: fadeIn 0.6s ease-out">
            <h4>💪 Hand Strength</h4>
            <div class="strength-meter">
                <div class="strength-fill" style="width: ${winPct}%; transition: width 1s ease-out;"></div>
            </div>
            <p style="margin-top: 0.5rem; opacity: 0.8; font-size: 0.9rem;">
                ${getStrengthDescription(parseFloat(winPct))}
            </p>
        </div>
        ${getHandCategoryBreakdown(data.hand_categories)}
    `;
}

// Get strength description based on win percentage
function getStrengthDescription(winPct) {
    if (winPct >= 80) return "🔥 Extremely strong hand!";
    if (winPct >= 65) return "💪 Very strong position";
    if (winPct >= 50) return "👍 Favorable odds";
    if (winPct >= 35) return "⚖️ Competitive hand";
    if (winPct >= 20) return "⚠️ Proceed with caution";
    return "🚫 Very weak position";
}

// Get hand category breakdown
function getHandCategoryBreakdown(categories) {
    if (!categories) return '';
    
    const topCategories = Object.entries(categories)
        .filter(([_, freq]) => freq > 0.01)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    
    if (topCategories.length === 0) return '';
    
    return `
        <div class="hand-categories" style="margin-top: 1rem; animation: fadeIn 0.7s ease-out;">
            <h4>🃏 Likely Outcomes</h4>
            <div style="margin-top: 0.5rem;">
                ${topCategories.map(([category, freq], i) => `
                    <div style="display: flex; justify-content: space-between; padding: 0.3rem 0; opacity: ${1 - i * 0.15};">
                        <span>${formatHandCategory(category)}</span>
                        <span style="font-weight: bold;">${(freq * 100).toFixed(1)}%</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Format hand category names
function formatHandCategory(category) {
    const icons = {
        'high_card': '🎴',
        'pair': '👥',
        'two_pair': '👥👥',
        'three_of_a_kind': '🎰',
        'straight': '📏',
        'flush': '🌊',
        'full_house': '🏠',
        'four_of_a_kind': '🎯',
        'straight_flush': '🌟',
        'royal_flush': '👑'
    };
    
    const name = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    return `${icons[category] || '🃏'} ${name}`;
}

// Clear all selections with animation
function clearAll() {
    // Animate cards out
    document.querySelectorAll('.card.selected').forEach((card, i) => {
        setTimeout(() => {
            card.style.transform = 'scale(0.8) rotate(10deg)';
            card.style.opacity = '0.5';
        }, i * 30);
    });
    
    // Reset after animation
    setTimeout(() => {
        state.selectedCards = [];
        state.numOpponents = 0;
        
        updateCardVisuals();
        
        document.querySelectorAll('.opponent-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Hide results
        document.getElementById('resultsPanel').classList.remove('active');
        document.getElementById('mobileResults').style.display = 'none';
        
        // Reset card styles
        document.querySelectorAll('.card').forEach(card => {
            card.style.transform = '';
            card.style.opacity = '';
        });
        
        updateUI();
    }, 300);
}

// Show message with animation
function showMessage(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#F44336' : '#4CAF50'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add item to history ticker
function addToHistory(data) {
    const historyItem = {
        heroHand: data.hero_hand,
        boardCards: data.board_cards,
        numOpponents: data.num_opponents,
        winProbability: data.win_probability,
        timestamp: new Date().toISOString()
    };
    
    // Add to beginning of history
    state.history.unshift(historyItem);
    
    // Keep only last 20 items
    if (state.history.length > 20) {
        state.history = state.history.slice(0, 20);
    }
    
    saveHistory();
    updateHistoryTicker();
}

// Save history to localStorage
function saveHistory() {
    try {
        localStorage.setItem('camelotHistory', JSON.stringify(state.history));
    } catch (e) {
        console.error('Failed to save history:', e);
    }
}

// Load history from localStorage
function loadHistory() {
    try {
        const saved = localStorage.getItem('camelotHistory');
        if (saved) {
            state.history = JSON.parse(saved);
            // Convert timestamp strings back to dates
            state.history = state.history.map(item => ({
                ...item,
                timestamp: new Date(item.timestamp)
            }));
        }
    } catch (e) {
        console.error('Failed to load history:', e);
        state.history = [];
    }
}

// Update history ticker display
function updateHistoryTicker() {
    const tickerItems = document.getElementById('tickerItems');
    tickerItems.innerHTML = '';
    
    if (state.history.length === 0) {
        tickerItems.innerHTML = '<span style="opacity: 0.5;">No hands calculated yet...</span>';
        return;
    }
    
    // Create ticker items
    state.history.forEach((item, index) => {
        const tickerItem = document.createElement('div');
        tickerItem.className = 'ticker-item';
        tickerItem.style.animationDelay = `${index * 0.1}s`;
        
        // Determine win/loss class
        let resultClass = 'tie';
        let resultText = 'Even';
        if (item.winProbability > 0.55) {
            resultClass = 'win';
            resultText = 'Strong';
        } else if (item.winProbability < 0.45) {
            resultClass = 'loss';
            resultText = 'Weak';
        }
        
        // Format time
        const timeAgo = getTimeAgo(item.timestamp);
        
        // Build HTML
        tickerItem.innerHTML = `
            <span class="ticker-hand">${item.heroHand.join(' ')}</span>
            ${item.boardCards.length > 0 ? `<span class="ticker-board">[${item.boardCards.join(' ')}]</span>` : ''}
            <span class="ticker-opponents">vs ${item.numOpponents}</span>
            <span class="ticker-result ${resultClass}">${(item.winProbability * 100).toFixed(0)}% ${resultText}</span>
            <span class="ticker-time">${timeAgo}</span>
        `;
        
        tickerItems.appendChild(tickerItem);
    });
    
    // Add scrolling class if we have items
    const tickerContent = document.getElementById('tickerContent');
    if (state.history.length > 0) {
        tickerContent.classList.add('scrolling');
    } else {
        tickerContent.classList.remove('scrolling');
    }
}

// Get human-readable time ago
function getTimeAgo(timestamp) {
    const seconds = Math.floor((new Date() - timestamp) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

// Update ticker times periodically
setInterval(() => {
    if (state.history.length > 0) {
        updateHistoryTicker();
    }
}, 30000); // Update every 30 seconds

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .pulse-glow {
        animation: pulseGlow 2s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 20px rgba(76, 175, 80, 0.5); }
        50% { box-shadow: 0 0 30px rgba(76, 175, 80, 0.8); }
    }
`;
document.head.appendChild(style);