// Camelot Poker Calculator - Interactive JavaScript

const RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = [
    { symbol: '♠', name: 'spades', color: 'black' },
    { symbol: '♥', name: 'hearts', color: 'red' },
    { symbol: '♦', name: 'diamonds', color: 'red' },
    { symbol: '♣', name: 'clubs', color: 'black' }
];

// State management
const state = {
    heroCards: [],
    boardCards: [],
    numOpponents: 0,
    selectedCards: new Set()
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    generateCardGrids();
    setupEventListeners();
    updateUI();
});

// Generate card grids
function generateCardGrids() {
    const heroGrid = document.getElementById('heroCards');
    const boardGrid = document.getElementById('boardCards');
    
    // Clear existing cards
    heroGrid.innerHTML = '';
    boardGrid.innerHTML = '';
    
    // Generate cards for each suit and rank
    SUITS.forEach(suit => {
        RANKS.forEach(rank => {
            const cardId = `${rank}${suit.symbol}`;
            
            // Create card for hero selection
            const heroCard = createCardElement(cardId, rank, suit, 'hero');
            heroGrid.appendChild(heroCard);
            
            // Create card for board selection
            const boardCard = createCardElement(cardId, rank, suit, 'board');
            boardGrid.appendChild(boardCard);
        });
    });
}

// Create a card element
function createCardElement(cardId, rank, suit, type) {
    const card = document.createElement('div');
    card.className = `card ${suit.color === 'red' ? 'red' : ''}`;
    card.dataset.card = cardId;
    card.dataset.type = type;
    card.innerHTML = `
        ${rank}
        <span class="suit-icon">${suit.symbol}</span>
    `;
    
    card.addEventListener('click', () => handleCardClick(cardId, type));
    
    return card;
}

// Handle card selection
function handleCardClick(cardId, type) {
    // Check if card is already selected anywhere
    if (state.selectedCards.has(cardId)) {
        // Deselect if clicking the same card
        if ((type === 'hero' && state.heroCards.includes(cardId)) ||
            (type === 'board' && state.boardCards.includes(cardId))) {
            deselectCard(cardId, type);
        }
        return;
    }
    
    // Check selection limits
    if (type === 'hero' && state.heroCards.length >= 2) {
        showMessage('You can only select 2 hole cards', 'error');
        return;
    }
    
    if (type === 'board' && state.boardCards.length >= 5) {
        showMessage('You can only select up to 5 board cards', 'error');
        return;
    }
    
    // Select the card
    selectCard(cardId, type);
}

// Select a card
function selectCard(cardId, type) {
    state.selectedCards.add(cardId);
    
    if (type === 'hero') {
        state.heroCards.push(cardId);
    } else {
        state.boardCards.push(cardId);
    }
    
    // Update visual state
    const cards = document.querySelectorAll(`[data-card="${cardId}"]`);
    cards.forEach(card => {
        card.classList.add('selected');
        if (card.dataset.type !== type) {
            card.style.opacity = '0.5';
            card.style.pointerEvents = 'none';
        }
    });
    
    updateUI();
}

// Deselect a card
function deselectCard(cardId, type) {
    state.selectedCards.delete(cardId);
    
    if (type === 'hero') {
        state.heroCards = state.heroCards.filter(c => c !== cardId);
    } else {
        state.boardCards = state.boardCards.filter(c => c !== cardId);
    }
    
    // Update visual state
    const cards = document.querySelectorAll(`[data-card="${cardId}"]`);
    cards.forEach(card => {
        card.classList.remove('selected');
        card.style.opacity = '1';
        card.style.pointerEvents = 'auto';
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
            
            // Update visual state
            document.querySelectorAll('.opponent-btn').forEach(b => {
                b.classList.remove('selected');
            });
            btn.classList.add('selected');
            
            updateUI();
        });
    });
    
    // Calculate button
    document.getElementById('calculateBtn').addEventListener('click', calculateOdds);
    
    // Clear button
    document.getElementById('clearBtn').addEventListener('click', clearAll);
}

// Update UI state
function updateUI() {
    // Update selected cards display
    document.getElementById('selectedHero').textContent = 
        state.heroCards.length > 0 ? state.heroCards.join(', ') : 'None';
    
    document.getElementById('selectedBoard').textContent = 
        state.boardCards.length > 0 ? state.boardCards.join(', ') : 'None';
    
    // Enable/disable calculate button
    const calculateBtn = document.getElementById('calculateBtn');
    const canCalculate = state.heroCards.length === 2 && state.numOpponents > 0;
    calculateBtn.disabled = !canCalculate;
}

// Calculate odds
async function calculateOdds() {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    // Show loading
    loading.style.display = 'block';
    results.style.display = 'none';
    
    // Prepare request data
    const requestData = {
        hero_hand: state.heroCards,
        num_opponents: state.numOpponents,
        board_cards: state.boardCards.length > 0 ? state.boardCards : null,
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
        
        if (data.success) {
            displayResults(data);
        } else {
            showMessage(data.error || 'Calculation failed', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
    } finally {
        loading.style.display = 'none';
    }
}

// Display results
function displayResults(data) {
    const results = document.getElementById('results');
    results.style.display = 'block';
    results.classList.add('success-flash');
    
    // Update result bars
    const winBar = document.getElementById('winBar');
    const tieBar = document.getElementById('tieBar');
    const lossBar = document.getElementById('lossBar');
    
    const winPct = (data.win_probability * 100).toFixed(1);
    const tiePct = (data.tie_probability * 100).toFixed(1);
    const lossPct = (data.loss_probability * 100).toFixed(1);
    
    winBar.style.width = winPct + '%';
    winBar.textContent = winPct + '%';
    
    tieBar.style.width = tiePct + '%';
    tieBar.textContent = tiePct > 2 ? tiePct + '%' : '';
    
    lossBar.style.width = lossPct + '%';
    lossBar.textContent = lossPct + '%';
    
    // Update details
    const details = document.getElementById('resultDetails');
    details.innerHTML = `
        <div class="result-stats">
            <div class="stat-card">
                <h4>Simulations</h4>
                <div class="value">${data.simulations_run.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <h4>Time</h4>
                <div class="value">${data.execution_time_ms.toFixed(0)}ms</div>
            </div>
            <div class="stat-card">
                <h4>Confidence</h4>
                <div class="value">±${((data.confidence_interval[1] - data.confidence_interval[0]) * 50).toFixed(1)}%</div>
            </div>
        </div>
        <div class="hand-strength">
            <h4>Hand Strength</h4>
            <div class="strength-meter">
                <div class="strength-fill" style="width: ${winPct}%"></div>
            </div>
        </div>
    `;
    
    // Remove flash animation after completion
    setTimeout(() => {
        results.classList.remove('success-flash');
    }, 500);
}

// Clear all selections
function clearAll() {
    // Clear state
    state.heroCards = [];
    state.boardCards = [];
    state.numOpponents = 0;
    state.selectedCards.clear();
    
    // Clear visual selections
    document.querySelectorAll('.card').forEach(card => {
        card.classList.remove('selected');
        card.style.opacity = '1';
        card.style.pointerEvents = 'auto';
    });
    
    document.querySelectorAll('.opponent-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Hide results
    document.getElementById('results').style.display = 'none';
    
    updateUI();
}

// Show message
function showMessage(message, type = 'info') {
    // For now, just use alert. In production, use a proper notification system
    if (type === 'error') {
        console.error(message);
        alert('Error: ' + message);
    } else {
        console.log(message);
    }
}