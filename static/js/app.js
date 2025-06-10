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
    history: [], // History of solved hands
    currentStatsLevel: localStorage.getItem('statsLevel') || 'standard', // Load saved preference or default to standard
    lastCalculationData: null, // Store the last calculation result
    tournamentMode: localStorage.getItem('tournamentMode') === 'true',
    heroPosition: localStorage.getItem('heroPosition') || '',
    stackSizes: JSON.parse(localStorage.getItem('stackSizes') || '[100]'), // Hero stack at index 0
    potSize: parseInt(localStorage.getItem('potSize') || '0'),
    probabilityChart: null, // Chart instance for desktop
    probabilityChartMobile: null // Chart instance for mobile
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    generateCardGrid();
    setupEventListeners();
    loadHistory();
    updateUI();
    
    // Set dropdown values to match saved preference
    const dropdowns = document.querySelectorAll('.stats-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.value = state.currentStatsLevel;
    });
    
    // Restore tournament mode state
    if (state.tournamentMode) {
        document.getElementById('tournamentMode').checked = true;
        document.getElementById('tournamentOptions').classList.add('active');
        updateStackInputs();
    }
    
    // Restore tournament mode inputs
    if (state.heroPosition) {
        document.getElementById('heroPosition').value = state.heroPosition;
    }
    document.getElementById('heroStack').value = state.stackSizes[0];
    document.getElementById('potSize').value = state.potSize;
    
    // Setup help icon interactions for mobile
    setupHelpIconInteractions();
    
    // Start monitoring cache status
    startCacheStatusMonitoring();
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
    
    // Generate cards in rows by suit
    SUITS.forEach(suit => {
        // Create a row container for each suit
        const suitRow = document.createElement('div');
        suitRow.className = 'suit-row';
        
        // Add suit label
        const suitLabel = document.createElement('div');
        suitLabel.className = 'suit-label';
        suitLabel.innerHTML = `<span class="${suit.color === 'red' ? 'red' : ''}">${suit.symbol}</span>`;
        suitRow.appendChild(suitLabel);
        
        // Add cards container
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'suit-cards';
        
        RANKS.forEach(rank => {
            const cardId = `${rank}${suit.symbol}`;
            const card = createCardElement(cardId, rank, suit);
            cardsContainer.appendChild(card);
        });
        
        suitRow.appendChild(cardsContainer);
        grid.appendChild(suitRow);
    });
}

// Create a card element
function createCardElement(cardId, rank, suit) {
    const card = document.createElement('div');
    card.className = `card ${suit.color === 'red' ? 'red' : ''}`;
    card.dataset.card = cardId;
    card.innerHTML = `
        <div class="card-corner-top">
            <div>${rank}</div>
            <div>${suit.symbol}</div>
        </div>
        <div class="card-corner-bottom">
            <div>${rank}</div>
            <div>${suit.symbol}</div>
        </div>
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
            
            // Update stack inputs if in tournament mode
            if (state.tournamentMode) {
                updateStackInputs();
            }
            
            updateUI();
        });
    });
    
    // Calculate button
    document.getElementById('calculateBtn').addEventListener('click', calculateOdds);
    
    // Clear button
    document.getElementById('clearBtn').addEventListener('click', clearAll);
    
    // History button
    document.getElementById('historyBtn').addEventListener('click', showHistoryModal);
    
    // Close history modal
    document.getElementById('closeHistoryModal').addEventListener('click', hideHistoryModal);
    document.getElementById('historyModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) hideHistoryModal();
    });
    
    // Filter button handlers
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentFilter = e.target.dataset.filter;
            updateFilterButtons();
            renderHistory();
        });
    });
    
    // Clear history button
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
    
    // Click outside game visualization to deselect
    document.getElementById('historyModal').addEventListener('click', (e) => {
        if (e.target.closest('.history-item-full') || e.target.closest('.game-visualization')) {
            return;
        }
        deselectHistoryItem();
    });
    
    // Tournament mode toggle
    document.getElementById('tournamentMode').addEventListener('change', (e) => {
        state.tournamentMode = e.target.checked;
        localStorage.setItem('tournamentMode', state.tournamentMode);
        const options = document.getElementById('tournamentOptions');
        options.classList.toggle('active', state.tournamentMode);
        
        if (state.tournamentMode) {
            updateStackInputs();
        }
    });
    
    // Position selector
    document.getElementById('heroPosition').addEventListener('change', (e) => {
        state.heroPosition = e.target.value;
        localStorage.setItem('heroPosition', state.heroPosition);
    });
    
    // Hero stack input
    document.getElementById('heroStack').addEventListener('input', (e) => {
        const value = parseInt(e.target.value) || 100;
        state.stackSizes[0] = value;
        localStorage.setItem('stackSizes', JSON.stringify(state.stackSizes));
    });
    
    // Pot size input
    document.getElementById('potSize').addEventListener('input', (e) => {
        state.potSize = parseInt(e.target.value) || 0;
        localStorage.setItem('potSize', state.potSize);
    });
    
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
    loading.classList.add('active');
    
    // Prepare request data
    const requestData = {
        hero_hand: heroCards,
        num_opponents: state.numOpponents,
        board_cards: boardCards.length > 0 ? boardCards : null,
        simulation_mode: 'default'
    };
    
    // Add tournament mode parameters if enabled
    if (state.tournamentMode) {
        if (state.heroPosition) {
            requestData.hero_position = state.heroPosition;
        }
        if (state.stackSizes.length > 1) {
            requestData.stack_sizes = state.stackSizes.slice(0, state.numOpponents + 1);
        }
        if (state.potSize > 0) {
            requestData.pot_size = state.potSize;
        }
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
            state.lastCalculationData = data; // Store for tab switching
            displayResults(data);
            addToHistory(data);
        } else {
            showMessage(data.error || 'Calculation failed', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
    } finally {
        loading.classList.remove('active');
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
    const winPct = parseFloat((data.win_probability * 100).toFixed(1));
    const tiePct = parseFloat((data.tie_probability * 100).toFixed(1));
    const lossPct = parseFloat((data.loss_probability * 100).toFixed(1));
    
    // Create or update donut chart
    const chartId = suffix === 'Mobile' ? 'probabilityChartMobile' : 'probabilityChart';
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // Destroy existing chart if it exists
    if (suffix === 'Mobile' && state.probabilityChartMobile) {
        state.probabilityChartMobile.destroy();
    } else if (suffix === '' && state.probabilityChart) {
        state.probabilityChart.destroy();
    }
    
    // Add total equity in the center
    const equity = data.win_probability + (data.tie_probability * 0.5);
    const equityText = (equity * 100).toFixed(1) + '%';
    
    // Custom plugin to draw text in center
    const centerTextPlugin = {
        id: 'centerText',
        afterDraw: (chart) => {
            const ctx = chart.ctx;
            ctx.save();
            const centerX = chart.getDatasetMeta(0).data[0].x;
            const centerY = chart.getDatasetMeta(0).data[0].y;
            
            // Draw "Total Equity" label
            ctx.font = '12px sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('Total Equity', centerX, centerY - 10);
            
            // Draw equity percentage
            ctx.font = 'bold 24px sans-serif';
            ctx.fillStyle = equity > 0.5 ? '#4CAF50' : equity < 0.5 ? '#F44336' : '#FFC107';
            ctx.fillText(equityText, centerX, centerY + 10);
            
            ctx.restore();
        }
    };
    
    // Create new donut chart with the plugin included
    const chartConfig = {
        type: 'doughnut',
        data: {
            labels: ['Win', 'Tie', 'Loss'],
            datasets: [{
                data: [winPct, tiePct, lossPct],
                backgroundColor: ['#4CAF50', '#FFC107', '#F44336'],
                borderColor: ['#2E7D32', '#F57C00', '#C62828'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'white',
                        padding: 15,
                        font: {
                            size: 14
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label}: ${value}%`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].borderColor[i],
                                        lineWidth: 2,
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: false,
                duration: 1000
            },
            cutout: '60%'
        },
        plugins: [centerTextPlugin] // Register the plugin here
    };
    
    // Store chart instance
    if (suffix === 'Mobile') {
        state.probabilityChartMobile = new Chart(ctx, chartConfig);
    } else {
        state.probabilityChart = new Chart(ctx, chartConfig);
    }
    
    // Update details based on current stats level
    updateStatsContent(suffix, data, state.currentStatsLevel);
}

// Update stats content based on selected level
function updateStatsContent(suffix, data, level) {
    const details = document.getElementById('resultDetails' + suffix);
    
    switch(level) {
        case 'basic':
            details.innerHTML = getBasicStats(data);
            break;
        case 'standard':
            details.innerHTML = getStandardStats(data);
            break;
        case 'advanced':
            details.innerHTML = getAdvancedStats(data);
            break;
        case 'expert':
            details.innerHTML = getExpertStats(data);
            break;
        case 'mathematician':
            details.innerHTML = getMathematicianStats(data);
            break;
    }
}

// Basic statistics - just the essentials
function getBasicStats(data) {
    const winPct = (data.win_probability * 100).toFixed(1);
    
    return `
        <div class="hand-strength" style="animation: fadeIn 0.3s ease-out">
            <h4>💪 Hand Strength</h4>
            <div class="strength-meter">
                <div class="strength-fill" style="width: ${winPct}%; transition: width 1s ease-out;"></div>
            </div>
            <p style="margin-top: 0.5rem; font-size: 1.2rem; font-weight: bold;">
                ${getStrengthDescription(parseFloat(winPct))}
            </p>
        </div>
        <div style="text-align: center; margin-top: 2rem; opacity: 0.7;">
            <p>Win Rate: ${winPct}%</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">vs ${data.num_opponents} opponent${data.num_opponents > 1 ? 's' : ''}</p>
        </div>
    `;
}

// Standard statistics - common metrics
function getStandardStats(data) {
    const winPct = (data.win_probability * 100).toFixed(1);
    
    return `
        <div class="hand-strength" style="animation: fadeIn 0.3s ease-out">
            <h4>💪 Hand Strength</h4>
            <div class="strength-meter">
                <div class="strength-fill" style="width: ${winPct}%; transition: width 1s ease-out;"></div>
            </div>
            <p style="margin-top: 0.5rem; opacity: 0.8; font-size: 0.9rem;">
                ${getStrengthDescription(parseFloat(winPct))}
            </p>
        </div>
        <div class="result-stats" style="margin-top: 1rem;">
            <div class="stat-card" style="animation: slideUp 0.4s ease-out">
                <h4>🎯 Win Rate</h4>
                <div class="value" style="font-size: 1.5rem;">${winPct}%</div>
            </div>
            <div class="stat-card" style="animation: slideUp 0.5s ease-out">
                <h4>${getComputeIcon(data)} Computed</h4>
                <div class="value">${getComputeSource(data)}</div>
            </div>
        </div>
        ${getHandCategoryBreakdown(data.hand_categories)}
    `;
}

// Advanced statistics - detailed metrics
function getAdvancedStats(data) {
    const winPct = (data.win_probability * 100).toFixed(1);
    const tiePct = (data.tie_probability * 100).toFixed(1);
    const lossPct = (data.loss_probability * 100).toFixed(1);
    
    return `
        <div class="hand-strength" style="animation: fadeIn 0.3s ease-out">
            <h4>💪 Hand Strength</h4>
            <div class="strength-meter">
                <div class="strength-fill" style="width: ${winPct}%; transition: width 1s ease-out;"></div>
            </div>
            <p style="margin-top: 0.5rem; opacity: 0.8; font-size: 0.9rem;">
                ${getStrengthDescription(parseFloat(winPct))}
            </p>
        </div>
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
                <h4>${getComputeIcon(data)} Source</h4>
                <div class="value" style="font-size: 0.9rem;">${getComputeSource(data)}</div>
            </div>
        </div>
        <div style="margin: 1rem 0; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 10px;">
            <h4>📈 Probability Breakdown</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem;">
                <div style="text-align: center;">
                    <div style="color: #4CAF50; font-size: 1.3rem; font-weight: bold;">${winPct}%</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Win</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #FFC107; font-size: 1.3rem; font-weight: bold;">${tiePct}%</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Tie</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #F44336; font-size: 1.3rem; font-weight: bold;">${lossPct}%</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Loss</div>
                </div>
            </div>
        </div>
        ${getHandCategoryBreakdown(data.hand_categories)}
    `;
}

// Expert statistics - advanced poker metrics
function getExpertStats(data) {
    const winPct = (data.win_probability * 100).toFixed(1);
    const equity = data.win_probability + (data.tie_probability * 0.5);
    const potOdds = data.win_probability > 0 ? (1 / data.win_probability - 1).toFixed(2) : 'N/A';
    
    // Advanced features that might be available
    const hasICM = data.icm_equity !== undefined && data.icm_equity !== null;
    const hasPosition = data.position_aware_equity !== undefined && data.position_aware_equity !== null;
    const hasMultiway = data.multi_way_statistics !== undefined && data.multi_way_statistics !== null;
    const hasDefense = data.defense_frequencies !== undefined && data.defense_frequencies !== null;
    
    return `
        <div style="font-size: 0.9rem;">
            <h4 style="margin-bottom: 1rem;">🎯 Expert Analysis</h4>
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Core Metrics</h5>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                    <div>Win Rate: <strong style="color: #4CAF50;">${winPct}%</strong></div>
                    <div>Total Equity: <strong>${(equity * 100).toFixed(1)}%</strong>${createHelpIcon('Your overall share of the pot, including half of all tie scenarios')}</div>
                    <div>Pot Odds Needed: <strong>1:${potOdds}</strong>${createHelpIcon('The minimum pot odds required to make calling profitable')}</div>
                    <div>Opponents: <strong>${data.num_opponents}</strong></div>
                    <div>Computed: <strong>${getComputeIcon(data)} ${getComputeSource(data)}</strong></div>
                    <div>Speed: <strong>${data.execution_time_ms.toFixed(0)}ms</strong></div>
                </div>
            </div>
            
            ${hasICM || hasPosition || hasMultiway || hasDefense || data.stack_to_pot_ratio || data.tournament_pressure || data.fold_equity_estimates ? `
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 1rem;">Advanced Strategic Adjustments</h5>
                <div style="display: grid; gap: 0.8rem;">
                    ${hasICM ? `<div style="display: grid; grid-template-columns: minmax(140px, 180px) 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Tournament Pressure${createHelpIcon('ICM (Independent Chip Model) adjusts equity based on tournament payout structure')}</div>
                        <div style="line-height: 1.4;">${
                            data.icm_equity < data.win_probability * 0.9 
                                ? '🚨 High ICM pressure - tighten ranges significantly' 
                                : data.icm_equity < data.win_probability * 0.95 
                                    ? '⚠️ Moderate ICM pressure - avoid marginal spots'
                                    : '✅ Low ICM pressure - play close to chip EV'
                        }</div>
                    </div>` : ''}
                    ${data.tournament_pressure ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Stack Dynamics${createHelpIcon('How your stack size affects optimal strategy')}</div>
                        <div style="line-height: 1.4;">${
                            data.tournament_pressure.stack_pressure > 0.8
                                ? '📈 Big stack - apply maximum pressure, exploit ICM'
                                : data.tournament_pressure.stack_pressure > 0.5
                                    ? '⚖️ Average stack - balanced approach, pick spots carefully'
                                    : '📉 Short stack - push/fold mode, maximize fold equity'
                        }</div>
                    </div>` : ''}
                    ${hasPosition && typeof data.position_aware_equity === 'object' ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Position Advantage${createHelpIcon('Your seating position relative to the dealer button affects optimal strategy')}</div>
                        <div style="line-height: 1.4;">${
                            state.heroPosition === 'button' || state.heroPosition === 'co' 
                                ? '🎯 Late position - widen ranges, increase aggression'
                                : state.heroPosition === 'sb' || state.heroPosition === 'bb'
                                    ? '🛡️ Blinds - defend appropriately, use pot odds'
                                    : '⚖️ Early/Middle - play straightforward, value heavy'
                        }</div>
                    </div>` : ''}
                    ${data.fold_equity_estimates ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Fold Equity${createHelpIcon('Likelihood of opponents folding to your bets')}</div>
                        <div style="line-height: 1.4;">${
                            data.fold_equity_estimates.position_modifier > 1.1
                                ? '💪 High fold equity - increase bluff frequency'
                                : data.fold_equity_estimates.position_modifier > 0.9
                                    ? '⚖️ Standard fold equity - balanced betting'
                                    : '⚠️ Low fold equity - value bet primarily'
                        }</div>
                    </div>` : ''}
                    ${hasDefense && typeof data.defense_frequencies === 'object' ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Defense Strategy${createHelpIcon('How often you should defend against bets based on opponent tendencies')}</div>
                        <div style="line-height: 1.4;">${
                            Object.values(data.defense_frequencies).some(v => v > 0.4)
                                ? '🔴 Defend wide - opponent likely overbluffing'
                                : Object.values(data.defense_frequencies).some(v => v > 0.3)
                                    ? '🟡 Standard defense - balance value and bluffs'
                                    : '🟢 Tight defense - opponent likely value heavy'
                        }</div>
                    </div>` : ''}
                    ${data.stack_to_pot_ratio ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">SPR Strategy${createHelpIcon('Stack-to-Pot Ratio: effective stack size divided by pot size')}</div>
                        <div style="line-height: 1.4;">${
                            data.stack_to_pot_ratio < 4 
                                ? '💥 Low SPR - commit with top pairs, draws lose value'
                                : data.stack_to_pot_ratio < 10
                                    ? '⚔️ Medium SPR - balanced strategy, all options open'
                                    : '🏰 Deep SPR - implied odds matter, position crucial'
                        }</div>
                    </div>` : ''}
                    ${hasMultiway && data.multi_way_statistics ? `<div style="display: grid; grid-template-columns: 180px 1fr; align-items: start; gap: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; color: #90CAF9;">Multi-way Dynamics${createHelpIcon('How to adjust strategy with multiple opponents')}</div>
                        <div style="line-height: 1.4;">${
                            data.num_opponents >= 4
                                ? '🎯 Tighten significantly - nut hands dominate'
                                : data.num_opponents === 3
                                    ? '⚖️ Value-heavy approach - draws devalue'
                                    : '📊 Standard adjustments - position crucial'
                        }</div>
                    </div>` : ''}
                </div>
            </div>
            ` : ''}
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Strategic Insights</h5>
                <div style="display: grid; gap: 0.5rem;">
                    <div>Hand Class: <strong style="color: ${equity > 0.6 ? '#4CAF50' : equity > 0.4 ? '#FFC107' : '#F44336'}">
                        ${equity > 0.6 ? 'Premium' : equity > 0.5 ? 'Strong' : equity > 0.4 ? 'Marginal' : 'Weak'}
                    </strong>${createHelpIcon('Classification based on your total equity against opponents')}</div>
                    <div>Recommended Action: <strong>
                        ${equity > 0.6 ? 'Bet/Raise' : equity > 0.5 ? 'Bet/Call' : equity > 0.4 ? 'Check/Call' : 'Check/Fold'}
                    </strong>${createHelpIcon('Suggested action based on hand strength and game theory optimal play')}</div>
                    <div>Bluff Frequency: <strong>
                        ${data.num_opponents === 1 ? '~33%' : data.num_opponents === 2 ? '~20%' : '~10%'}
                    </strong>${createHelpIcon('Optimal bluffing frequency based on game theory and number of opponents')}</div>
                    ${data.bluff_catching_frequency !== undefined && data.bluff_catching_frequency !== null ? `<div>Bluff Catching: <strong>
                        ${data.bluff_catching_frequency > 0.4 ? 'Call liberally' : data.bluff_catching_frequency > 0.25 ? 'Call selectively' : 'Fold often'}
                    </strong>${createHelpIcon('How often you should call potential bluffs based on pot odds and opponent tendencies')}</div>` : ''}
                </div>
            </div>
            
            ${getHandCategoryBreakdown(data.hand_categories)}
            
            ${!state.tournamentMode ? `
            <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 5px; font-size: 0.8rem; opacity: 0.7;">
                <strong>Note:</strong> Enable Tournament Mode to unlock position-aware equity and ICM calculations.
            </div>
            ` : (!hasICM && !hasPosition && !data.stack_to_pot_ratio) ? `
            <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 5px; font-size: 0.8rem; opacity: 0.7;">
                <strong>Note:</strong> Advanced tournament features (ICM, position-aware equity) may not be available in the current poker_knight version. SPR calculations are shown when available.
            </div>
            ` : ''}
        </div>
    `;
}

// Mathematician statistics - all the numbers
function getMathematicianStats(data) {
    const winPct = (data.win_probability * 100).toFixed(6);
    const tiePct = (data.tie_probability * 100).toFixed(6);
    const lossPct = (data.loss_probability * 100).toFixed(6);
    const equity = data.win_probability + (data.tie_probability * 0.5);
    const potOdds = data.win_probability > 0 ? (1 / data.win_probability - 1).toFixed(6) : 'N/A';
    const ev = equity > 0.5 ? '+EV' : equity < 0.5 ? '-EV' : 'Neutral';
    
    // Get ALL data keys for complete dump
    const allDataKeys = Object.keys(data).sort();
    
    return `
        <div style="font-size: 0.85rem;">
            <h4 style="margin-bottom: 1rem;">📐 Complete Data Dump - All Available Statistics</h4>
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Core Probabilities (Maximum Precision)</h5>
                <div style="display: grid; gap: 0.5rem; font-family: monospace;">
                    <div>win_probability: <strong>${data.win_probability}</strong> (${winPct}%)</div>
                    <div>tie_probability: <strong>${data.tie_probability}</strong> (${tiePct}%)</div>
                    <div>loss_probability: <strong>${data.loss_probability}</strong> (${lossPct}%)</div>
                    <div>total_equity: <strong>${equity}</strong> (${(equity * 100).toFixed(6)}%)</div>
                </div>
            </div>
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Simulation Metadata</h5>
                <div style="display: grid; gap: 0.5rem; font-family: monospace;">
                    <div>simulations_run: <strong>${data.simulations_run}</strong></div>
                    <div>execution_time_ms: <strong>${data.execution_time_ms}</strong></div>
                    <div>simulations_per_second: <strong>${Math.round(data.simulations_run / (data.execution_time_ms / 1000))}</strong></div>
                    <div>confidence_interval: <strong>[${data.confidence_interval[0]}, ${data.confidence_interval[1]}]</strong></div>
                    <div>margin_of_error: <strong>±${(data.confidence_interval[1] - data.confidence_interval[0]) / 2}</strong></div>
                    <div>simulation_mode: <strong>${data.simulation_mode || 'default'}</strong></div>
                </div>
            </div>
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Input Parameters</h5>
                <div style="display: grid; gap: 0.5rem; font-family: monospace;">
                    <div>hero_hand: <strong>${JSON.stringify(data.hero_hand)}</strong></div>
                    <div>board_cards: <strong>${JSON.stringify(data.board_cards)}</strong></div>
                    <div>num_opponents: <strong>${data.num_opponents}</strong></div>
                </div>
            </div>
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Derived Metrics</h5>
                <div style="display: grid; gap: 0.5rem; font-family: monospace;">
                    <div>pot_odds_required: <strong>1:${potOdds}</strong></div>
                    <div>break_even_percentage: <strong>${data.win_probability > 0 ? (100 / (1 + parseFloat(potOdds))).toFixed(6) : 'N/A'}%</strong></div>
                    <div>expected_value_indicator: <strong>${ev}</strong></div>
                    <div>information_ratio: <strong>${(1 - (data.confidence_interval[1] - data.confidence_interval[0])).toFixed(6)}</strong></div>
                    <div>relative_hand_strength: <strong>${(equity / (1 / (data.num_opponents + 1))).toFixed(6)}</strong></div>
                </div>
            </div>
            
            ${data.hand_categories ? `
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Complete Hand Category Distribution</h5>
                <div style="display: grid; gap: 0.3rem; font-family: monospace; font-size: 0.8rem;">
                    ${Object.entries(data.hand_categories)
                        .sort((a, b) => b[1] - a[1])
                        .map(([category, freq]) => `
                            <div style="display: flex; justify-content: space-between;">
                                <span>${category}:</span>
                                <span><strong>${freq}</strong> (${(freq * 100).toFixed(6)}%)</span>
                            </div>
                        `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${data.position_aware_equity || data.icm_equity || data.multi_way_statistics || data.defense_frequencies || data.coordination_effects || data.stack_to_pot_ratio || data.tournament_pressure || data.fold_equity_estimates || data.bubble_factor || data.bluff_catching_frequency ? `
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Tournament & Advanced Features</h5>
                <div style="display: grid; gap: 0.5rem; font-family: monospace; font-size: 0.8rem;">
                    ${data.icm_equity !== undefined && data.icm_equity !== null ? `<div>icm_equity: <strong>${data.icm_equity}</strong></div>` : ''}
                    ${data.position_aware_equity ? `<div>position_aware_equity: <strong>${JSON.stringify(data.position_aware_equity, null, 2)}</strong></div>` : ''}
                    ${data.stack_to_pot_ratio !== undefined && data.stack_to_pot_ratio !== null ? `<div>stack_to_pot_ratio: <strong>${data.stack_to_pot_ratio}</strong></div>` : ''}
                    ${data.tournament_pressure ? `<div>tournament_pressure: <strong>${JSON.stringify(data.tournament_pressure, null, 2)}</strong></div>` : ''}
                    ${data.fold_equity_estimates ? `<div>fold_equity_estimates: <strong>${JSON.stringify(data.fold_equity_estimates, null, 2)}</strong></div>` : ''}
                    ${data.bubble_factor !== undefined && data.bubble_factor !== null ? `<div>bubble_factor: <strong>${data.bubble_factor}</strong></div>` : ''}
                    ${data.bluff_catching_frequency !== undefined && data.bluff_catching_frequency !== null ? `<div>bluff_catching_frequency: <strong>${data.bluff_catching_frequency}</strong></div>` : ''}
                    ${data.multi_way_statistics ? `<div>multi_way_statistics: <strong>${JSON.stringify(data.multi_way_statistics, null, 2)}</strong></div>` : ''}
                    ${data.defense_frequencies ? `<div>defense_frequencies: <strong>${JSON.stringify(data.defense_frequencies, null, 2)}</strong></div>` : ''}
                    ${data.coordination_effects ? `<div>coordination_effects: <strong>${JSON.stringify(data.coordination_effects, null, 2)}</strong></div>` : ''}
                </div>
            </div>
            ` : ''}
            
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h5 style="color: #FFD700; margin-bottom: 0.5rem;">Raw API Response (All Fields)</h5>
                <div style="font-family: monospace; font-size: 0.75rem; max-height: 300px; overflow-y: auto;">
                    ${allDataKeys.map(key => {
                        const value = data[key];
                        const displayValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : value;
                        return `<div style="margin-bottom: 0.5rem;"><strong>${key}:</strong> ${displayValue}</div>`;
                    }).join('')}
                </div>
            </div>
            
            <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 5px; font-size: 0.8rem; opacity: 0.7;">
                <strong>Note:</strong> This view shows ALL data returned by the poker_knight API, including internal fields and metadata.
            </div>
        </div>
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

// Get computation source icon
function getComputeIcon(data) {
    if (data.backend === 'cache') return '💾';
    if (data.gpu_used || data.backend === 'cuda') return '🎮';
    return '🖥️';
}

// Get computation source description
function getComputeSource(data) {
    if (data.backend === 'cache') {
        return 'Cached';
    }
    if (data.gpu_used || data.backend === 'cuda') {
        if (data.device) {
            return `GPU (${data.device})`;
        }
        return 'GPU';
    }
    return 'CPU';
}

// Create help icon with tooltip
function createHelpIcon(tooltipText) {
    // Generate unique ID for this tooltip
    const tooltipId = 'tooltip-' + Math.random().toString(36).substr(2, 9);
    return `<span class="help-icon" data-tooltip-id="${tooltipId}" data-tooltip-text="${tooltipText.replace(/"/g, '&quot;')}" onclick="event.stopPropagation()">?</span>`;
}

// Get hand category breakdown
function getHandCategoryBreakdown(categories) {
    if (!categories) return '';
    
    const topCategories = Object.entries(categories)
        .filter(([_, freq]) => freq > 0.01)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    
    if (topCategories.length === 0) return '';
    
    // Generate unique canvas ID
    const canvasId = 'handChart' + Math.random().toString(36).substr(2, 9);
    
    // Prepare data for chart
    const labels = topCategories.map(([category]) => formatHandCategory(category));
    const data = topCategories.map(([_, freq]) => (freq * 100).toFixed(1));
    
    // Create chart after DOM updates
    setTimeout(() => {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(76, 175, 80, 0.7)',
                        'rgba(139, 195, 74, 0.7)',
                        'rgba(255, 193, 7, 0.7)',
                        'rgba(255, 152, 0, 0.7)',
                        'rgba(244, 67, 54, 0.7)'
                    ],
                    borderColor: [
                        'rgba(76, 175, 80, 1)',
                        'rgba(139, 195, 74, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(255, 152, 0, 1)',
                        'rgba(244, 67, 54, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.x + '%';
                            }
                        }
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'end',
                        color: 'white',
                        font: {
                            weight: 'bold',
                            size: 12
                        },
                        formatter: function(value) {
                            return value + '%';
                        },
                        offset: 4
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: Math.max(...data.map(d => parseFloat(d))) * 1.2,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 13
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    delay: (context) => context.dataIndex * 100,
                    onComplete: function() {
                        // Draw value labels on bars after animation completes
                        const chart = this;
                        const ctx = chart.ctx;
                        ctx.font = 'bold 12px sans-serif';
                        ctx.fillStyle = 'white';
                        ctx.textAlign = 'left';
                        ctx.textBaseline = 'middle';
                        
                        chart.data.datasets.forEach((dataset, i) => {
                            const meta = chart.getDatasetMeta(i);
                            meta.data.forEach((bar, index) => {
                                const data = dataset.data[index];
                                const x = bar.x + 5;
                                const y = bar.y;
                                ctx.fillText(data + '%', x, y);
                            });
                        });
                    }
                }
            }
        });
    }, 100);
    
    return `
        <div class="hand-categories" style="margin-top: 1rem; animation: fadeIn 0.7s ease-out;">
            <h4>🃏 Likely Outcomes</h4>
            <div style="position: relative; height: ${topCategories.length * 50 + 20}px; margin-top: 0.5rem;">
                <canvas id="${canvasId}"></canvas>
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
        
        // Destroy charts if they exist
        if (state.probabilityChart) {
            state.probabilityChart.destroy();
            state.probabilityChart = null;
        }
        if (state.probabilityChartMobile) {
            state.probabilityChartMobile.destroy();
            state.probabilityChartMobile = null;
        }
        
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


// Get human-readable time ago
function getTimeAgo(timestamp) {
    // Ensure timestamp is a Date object
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (isNaN(seconds)) return 'unknown';
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}


// Current filter state
let currentFilter = 'all';
let selectedHistoryItem = null;

// Show history modal
function showHistoryModal() {
    const modal = document.getElementById('historyModal');
    currentFilter = 'all'; // Reset filter
    updateFilterButtons();
    renderHistory();
    modal.classList.add('active');
}

// Update filter button states
function updateFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === currentFilter);
    });
}

// Render history based on current filter
function renderHistory() {
    const modalBody = document.getElementById('historyModalBody');
    modalBody.innerHTML = '';
    
    // Filter history based on current filter
    let filteredHistory = state.history;
    if (currentFilter !== 'all') {
        filteredHistory = state.history.filter(item => {
            const stage = getGameStageKey(item.boardCards ? item.boardCards.length : 0);
            return stage === currentFilter;
        });
    }
    
    if (filteredHistory.length === 0) {
        const emptyMessage = currentFilter === 'all' 
            ? 'No calculations yet. Start by selecting cards and opponents!' 
            : `No ${currentFilter.charAt(0).toUpperCase() + currentFilter.slice(1)} calculations yet.`;
        modalBody.innerHTML = `
            <div style="text-align: center; padding: 3rem; opacity: 0.7;">
                <p style="font-size: 1.2rem; margin-bottom: 1rem;">${emptyMessage}</p>
                <p style="font-size: 2rem;">🃏</p>
            </div>
        `;
        return;
    }
    
    // Add statistics section
    const stats = calculateStats(filteredHistory);
    const statsSection = document.createElement('div');
    statsSection.className = 'history-stats';
    statsSection.innerHTML = `
        <div class="stat-box">
            <div class="stat-box-value">${stats.total}</div>
            <div class="stat-box-label">Total Hands</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.avgWin}%</div>
            <div class="stat-box-label">Avg Win Rate</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.strongHands}</div>
            <div class="stat-box-label">Strong Hands</div>
        </div>
        <div class="stat-box">
            <div class="stat-box-value">${stats.weakHands}</div>
            <div class="stat-box-label">Weak Hands</div>
        </div>
    `;
    modalBody.appendChild(statsSection);
    
    // Create detailed history items
    filteredHistory.forEach((item, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item-full';
        historyItem.style.animationDelay = `${index * 0.05}s`;
        
        // Determine result strength
        let resultClass = 'tie';
        let resultText = 'Even Odds';
        let resultIcon = '⚖️';
        if (item.winProbability > 0.55) {
            resultClass = 'win';
            resultText = 'Strong Hand';
            resultIcon = '💪';
        } else if (item.winProbability < 0.45) {
            resultClass = 'loss';
            resultText = 'Weak Hand';
            resultIcon = '⚠️';
        }
        
        const boardLength = item.boardCards ? item.boardCards.length : 0;
        historyItem.innerHTML = `
            <div class="history-item-header">
                <div class="history-item-cards">
                    <span style="color: #90CAF9; font-size: 1.3rem;">${item.heroHand.join(' ')}</span>
                    ${boardLength > 0 ? `<span style="color: #FFD700; margin-left: 1rem; font-size: 1.1rem;">[${item.boardCards.join(' ')}]</span>` : ''}
                </div>
                <div class="history-item-time">${getTimeAgo(item.timestamp)}</div>
            </div>
            <div class="history-item-details">
                <div class="history-detail">
                    <div class="history-detail-label">Opponents</div>
                    <div class="history-detail-value">${item.numOpponents} ${item.numOpponents === 1 ? 'player' : 'players'}</div>
                </div>
                <div class="history-detail">
                    <div class="history-detail-label">Win Probability</div>
                    <div class="history-detail-value ${resultClass}" style="font-size: 1.3rem;">${(item.winProbability * 100).toFixed(1)}%</div>
                </div>
                <div class="history-detail">
                    <div class="history-detail-label">Assessment</div>
                    <div class="history-detail-value ${resultClass}">${resultIcon} ${resultText}</div>
                </div>
                <div class="history-detail">
                    <div class="history-detail-label">Stage</div>
                    <div class="history-detail-value">${getGameStage(boardLength)}</div>
                </div>
            </div>
        `;
        
        // Add click handler for visualization
        historyItem.addEventListener('click', () => {
            selectHistoryItem(item, historyItem);
        });
        
        modalBody.appendChild(historyItem);
    });
}

// Calculate statistics for history
function calculateStats(history) {
    if (history.length === 0) {
        return { total: 0, avgWin: 0, strongHands: 0, weakHands: 0 };
    }
    
    const totalWin = history.reduce((sum, item) => sum + item.winProbability, 0);
    const strongHands = history.filter(item => item.winProbability > 0.55).length;
    const weakHands = history.filter(item => item.winProbability < 0.45).length;
    
    return {
        total: history.length,
        avgWin: Math.round((totalWin / history.length) * 100),
        strongHands,
        weakHands
    };
}

// Hide history modal
function hideHistoryModal() {
    document.getElementById('historyModal').classList.remove('active');
    deselectHistoryItem();
}

// Get game stage based on board cards
function getGameStage(boardCardCount) {
    switch(boardCardCount) {
        case 0: return 'Pre-flop';
        case 3: return 'Flop';
        case 4: return 'Turn';
        case 5: return 'River';
        default: return 'Unknown';
    }
}

// Get game stage key for filtering
function getGameStageKey(boardCardCount) {
    switch(boardCardCount) {
        case 0: return 'preflop';
        case 3: return 'flop';
        case 4: return 'turn';
        case 5: return 'river';
        default: return 'unknown';
    }
}

// Clear history with animation
function clearHistory() {
    if (confirm('Are you sure you want to clear all calculation history? This cannot be undone.')) {
        // Animate all history items imploding
        const items = document.querySelectorAll('.history-item-full');
        items.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('clearing');
            }, index * 50); // Stagger the animations
        });
        
        // Clear after animations complete
        setTimeout(() => {
            state.history = [];
            saveHistory();
            renderHistory();
            showMessage('History cleared successfully', 'info');
            deselectHistoryItem();
        }, items.length * 50 + 500);
    }
}

// Select history item and show visualization
function selectHistoryItem(item, element) {
    // Remove previous selection
    document.querySelectorAll('.history-item-full').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Add selection to clicked item
    element.classList.add('selected');
    selectedHistoryItem = item;
    
    // Show visualization
    showGameVisualization(item);
}

// Deselect history item
function deselectHistoryItem() {
    document.querySelectorAll('.history-item-full').forEach(el => {
        el.classList.remove('selected');
    });
    selectedHistoryItem = null;
    document.getElementById('gameVisualization').classList.remove('active');
}

// Show game visualization
function showGameVisualization(item) {
    const viz = document.getElementById('gameVisualization');
    const heroCardsDiv = document.getElementById('heroCards');
    const tableCardsDiv = document.getElementById('tableCards');
    const gameInfoDiv = document.getElementById('gameInfo');
    
    // Clear previous cards
    heroCardsDiv.innerHTML = '';
    tableCardsDiv.innerHTML = '';
    
    // Create hero cards
    item.heroHand.forEach((card, index) => {
        const cardEl = createPokerCard(card);
        cardEl.style.animationDelay = `${index * 0.1}s`;
        heroCardsDiv.appendChild(cardEl);
    });
    
    // Create board cards only if they exist
    if (item.boardCards && item.boardCards.length > 0) {
        item.boardCards.forEach((card, index) => {
            const cardEl = createPokerCard(card);
            cardEl.style.animationDelay = `${(index + 2) * 0.1}s`;
            tableCardsDiv.appendChild(cardEl);
        });
    }
    // For pre-flop, the table center remains empty
    
    // Update game info
    const winPct = (item.winProbability * 100).toFixed(1);
    const stage = getGameStage(item.boardCards ? item.boardCards.length : 0);
    
    gameInfoDiv.innerHTML = `
        <h3>Game Details</h3>
        <div class="game-stats">
            <div class="game-stat">
                <div class="game-stat-label">Win Rate</div>
                <div class="game-stat-value" style="color: ${getResultColor(item.winProbability)}">
                    ${winPct}%
                </div>
            </div>
            <div class="game-stat">
                <div class="game-stat-label">Opponents</div>
                <div class="game-stat-value">${item.numOpponents}</div>
            </div>
            <div class="game-stat">
                <div class="game-stat-label">Stage</div>
                <div class="game-stat-value">${stage}</div>
            </div>
            <div class="game-stat">
                <div class="game-stat-label">Time</div>
                <div class="game-stat-value">${getTimeAgo(item.timestamp)}</div>
            </div>
        </div>
    `;
    
    // Show visualization panel
    viz.classList.add('active');
}

// Create a poker card element
function createPokerCard(cardStr) {
    const card = document.createElement('div');
    card.className = 'poker-card';
    
    // Parse card string
    let rank, suit;
    if (cardStr.startsWith('10')) {
        rank = '10';
        suit = cardStr.substring(2);
    } else {
        rank = cardStr[0];
        suit = cardStr.substring(1);
    }
    
    // Determine if red suit
    if (suit === '♥' || suit === '♦') {
        card.classList.add('red');
    }
    
    card.innerHTML = `
        <div class="rank">${rank}</div>
        <div class="suit">${suit}</div>
    `;
    
    return card;
}

// Get result color based on win probability
function getResultColor(winProb) {
    if (winProb > 0.55) return '#4CAF50';
    if (winProb < 0.45) return '#F44336';
    return '#FFC107';
}

// Switch statistics level
function switchStatsLevel(suffix, level) {
    // Update current level
    state.currentStatsLevel = level;
    
    // Save preference
    localStorage.setItem('statsLevel', level);
    
    // Update content if we have data
    if (state.lastCalculationData) {
        updateStatsContent(suffix, state.lastCalculationData, level);
    }
}

// Update stack inputs based on number of opponents
function updateStackInputs() {
    const container = document.getElementById('stackInputs');
    const heroInput = container.querySelector('#heroStack').parentElement;
    
    // Clear existing opponent inputs
    container.querySelectorAll('.opponent-stack').forEach(el => el.remove());
    
    // Add inputs for each opponent
    for (let i = 1; i <= state.numOpponents; i++) {
        const stackDiv = document.createElement('div');
        stackDiv.className = 'stack-input opponent-stack';
        stackDiv.innerHTML = `
            <label>Opp ${i}</label>
            <input type="number" placeholder="100" min="1" value="${state.stackSizes[i] || 100}" data-index="${i}">
        `;
        
        const input = stackDiv.querySelector('input');
        input.addEventListener('input', (e) => {
            const value = parseInt(e.target.value) || 100;
            const index = parseInt(e.target.dataset.index);
            state.stackSizes[index] = value;
            localStorage.setItem('stackSizes', JSON.stringify(state.stackSizes));
        });
        
        container.appendChild(stackDiv);
    }
    
    // Trim stack sizes array
    state.stackSizes = state.stackSizes.slice(0, state.numOpponents + 1);
    
    // Fill with defaults if needed
    while (state.stackSizes.length < state.numOpponents + 1) {
        state.stackSizes.push(100);
    }
}

// Show position help modal
function showPositionHelp() {
    document.getElementById('positionHelpModal').classList.add('active');
}

// Hide position help modal
function hidePositionHelp() {
    document.getElementById('positionHelpModal').classList.remove('active');
}

// Setup help icon interactions for mobile
function setupHelpIconInteractions() {
    let currentTooltip = null;
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'help-tooltip';
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
    
    // Mouse enter - show tooltip
    document.addEventListener('mouseenter', (e) => {
        const helpIcon = e.target.closest('.help-icon');
        if (helpIcon && window.innerWidth > 768) {
            const text = helpIcon.getAttribute('data-tooltip-text');
            if (text) {
                tooltip.innerHTML = text;
                tooltip.style.display = 'block';
                tooltip.style.opacity = '0';
                tooltip.style.visibility = 'hidden';
                
                // Position tooltip
                const rect = helpIcon.getBoundingClientRect();
                tooltip.style.opacity = '0';
                tooltip.style.visibility = 'visible';
                const tooltipRect = tooltip.getBoundingClientRect();
                tooltip.style.visibility = 'hidden';
                
                // For Core Metrics section, always show tooltip to the left or right
                const isInCoreMetrics = helpIcon.closest('div').textContent.includes('Total Equity') || 
                                       helpIcon.closest('div').textContent.includes('Pot Odds Needed');
                
                let top, left;
                
                if (isInCoreMetrics) {
                    // Position to the left of the icon
                    top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                    left = rect.left - tooltipRect.width - 10;
                    
                    // If it would go off left edge, show to the right instead
                    if (left < 10) {
                        left = rect.right + 10;
                    }
                } else {
                    // Default positioning - try above first
                    top = rect.top - tooltipRect.height - 8;
                    left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                    
                    // If tooltip would go off top of screen, show below
                    if (top < 10) {
                        top = rect.bottom + 8;
                    }
                }
                
                // Keep tooltip on screen
                if (left < 10) {
                    left = 10;
                } else if (left + tooltipRect.width > window.innerWidth - 10) {
                    left = window.innerWidth - tooltipRect.width - 10;
                }
                
                if (top < 10) {
                    top = 10;
                } else if (top + tooltipRect.height > window.innerHeight - 10) {
                    top = window.innerHeight - tooltipRect.height - 10;
                }
                
                tooltip.style.top = top + 'px';
                tooltip.style.left = left + 'px';
                
                // Fade in
                setTimeout(() => {
                    tooltip.style.opacity = '1';
                    tooltip.style.visibility = 'visible';
                }, 10);
                
                currentTooltip = helpIcon;
            }
        }
    }, true);
    
    // Mouse leave - hide tooltip
    document.addEventListener('mouseleave', (e) => {
        const helpIcon = e.target.closest('.help-icon');
        if (helpIcon && helpIcon === currentTooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
            setTimeout(() => {
                tooltip.style.display = 'none';
            }, 200);
            currentTooltip = null;
        }
    }, true);
    
    // Handle mobile taps
    document.addEventListener('click', (e) => {
        const helpIcon = e.target.closest('.help-icon');
        if (helpIcon && window.innerWidth <= 768) {
            e.preventDefault();
            e.stopPropagation();
            
            const text = helpIcon.getAttribute('data-tooltip-text');
            if (text) {
                // For mobile, show centered
                tooltip.innerHTML = text;
                tooltip.style.display = 'block';
                tooltip.style.position = 'fixed';
                tooltip.style.top = '50%';
                tooltip.style.left = '50%';
                tooltip.style.transform = 'translate(-50%, -50%)';
                tooltip.style.opacity = '1';
                tooltip.style.visibility = 'visible';
                tooltip.style.maxWidth = '90vw';
                
                // Hide on next tap anywhere
                setTimeout(() => {
                    document.addEventListener('click', hideTooltip, { once: true });
                }, 100);
            }
        }
    });
    
    function hideTooltip() {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        setTimeout(() => {
            tooltip.style.display = 'none';
            tooltip.style.transform = '';
        }, 200);
    }
}

// Cache status monitoring
let cacheStatusInterval = null;

function startCacheStatusMonitoring() {
    // Check cache status immediately
    checkCacheStatus();
    
    // Then check every 2 seconds
    cacheStatusInterval = setInterval(checkCacheStatus, 2000);
}

// Reset cache function (debugging feature)
async function resetCache() {
    if (!confirm('Are you sure you want to reset the cache? This will clear all cached calculations.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/cache-reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Cache has been reset successfully!');
            // Force reload to restart cache warming
            window.location.reload();
        } else {
            alert('Failed to reset cache: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Failed to reset cache:', error);
        alert('Failed to reset cache: ' + error.message);
    }
}

async function checkCacheStatus() {
    try {
        const response = await fetch('/api/cache-status');
        const data = await response.json();
        
        const cacheStatusEl = document.getElementById('cacheStatus');
        const cacheCountEl = document.getElementById('cacheCount');
        const cacheRateEl = document.getElementById('cacheRate');
        
        // Debug logging
        console.log('Cache status data:', data);
        console.log('Elements found:', {
            status: !!cacheStatusEl,
            count: !!cacheCountEl,
            rate: !!cacheRateEl
        });
        
        if (data.is_warming) {
            // Show the indicator
            cacheStatusEl.style.display = 'flex';
            
            // Show warming progress this session
            if (data.warming_this_session !== undefined) {
                cacheCountEl.textContent = `+${data.warming_this_session.toLocaleString()}`;
                // Add progress info if available
                if (data.progress_percent) {
                    cacheCountEl.textContent += ` (${data.progress_percent}%)`;
                }
            } else {
                // Fallback if warming_this_session is not available
                cacheCountEl.textContent = '0';
            }
            
            // Convert rate per second to rate per minute
            const ratePerMinute = data.rate_per_second * 60;
            cacheRateEl.textContent = ratePerMinute.toFixed(0);
        } else {
            // Hide the indicator with fade out
            if (cacheStatusEl.style.display === 'flex') {
                cacheStatusEl.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => {
                    cacheStatusEl.style.display = 'none';
                    cacheStatusEl.style.animation = '';
                }, 300);
                
                // Stop checking once warming is complete
                if (cacheStatusInterval) {
                    clearInterval(cacheStatusInterval);
                    cacheStatusInterval = null;
                }
            }
        }
    } catch (error) {
        console.error('Failed to check cache status:', error);
    }
}

// Make functions globally available
window.switchStatsLevel = switchStatsLevel;
window.showPositionHelp = showPositionHelp;
window.hidePositionHelp = hidePositionHelp;

// Navigation functions
function navigateToSection(section) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.section === section) {
            btn.classList.add('active');
        }
    });
    
    // Hide all sections
    document.querySelectorAll('.app-section').forEach(sec => {
        sec.style.display = 'none';
    });
    
    // Show selected section
    if (section === 'calculator') {
        document.getElementById('calculatorSection').style.display = 'block';
    } else if (section === 'play') {
        document.getElementById('playSection').style.display = 'block';
    }
}

// Join game function
function joinGame(gameId) {
    // For now, just show an alert. We'll implement the actual game later
    console.log(`Joining game: ${gameId}`);
    
    // Create game configuration based on gameId
    const gameConfigs = {
        'beginner-luck': {
            players: 2,
            heroStack: 200,
            opponentStacks: [200],
            difficulty: 'easy',
            bigBlind: 2
        },
        'short-stack-survival': {
            players: 6,
            heroStack: 20,
            opponentStacks: [25, 30, 15, 50, 40],
            difficulty: 'medium',
            bigBlind: 2
        },
        'high-stakes': {
            players: 4,
            heroStack: 500,
            opponentStacks: [450, 600, 550],
            difficulty: 'hard',
            bigBlind: 10
        },
        'tournament-bubble': {
            players: 5,
            heroStack: 35,
            opponentStacks: [80, 25, 15, 45],
            difficulty: 'expert',
            bigBlind: 4
        }
    };
    
    const config = gameConfigs[gameId];
    if (config) {
        // Store game config and redirect to game page
        sessionStorage.setItem('gameConfig', JSON.stringify(config));
        // For now, just log it
        console.log('Game configuration:', config);
        alert(`Coming soon! ${gameId} game will start with ${config.players} players.`);
    }
}

// Make navigation functions globally available
window.navigateToSection = navigateToSection;
window.joinGame = joinGame;

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