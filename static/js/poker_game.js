// Poker Game Client-Side Logic

// Game state
let gameState = null;
let soundEnabled = true;
let animationQueue = [];
let isAnimating = false;

// Sound effects (using Web Audio API)
const sounds = {
    shuffle: { frequency: 800, duration: 100 },
    cardFlip: { frequency: 1200, duration: 50 },
    chipClick: { frequency: 600, duration: 30 },
    win: { frequency: 1600, duration: 500 },
    fold: { frequency: 400, duration: 200 },
    check: { frequency: 1000, duration: 100 },
    bet: { frequency: 900, duration: 150 },
    raise: { frequency: 1100, duration: 200 },
    allIn: { frequency: 1400, duration: 300 },
    turn: { frequency: 500, duration: 80 }
};

// Audio context
let audioContext = null;

// Bug Report Functions - Define these early so they're available globally
function showBugReportForm() {
    console.log('Showing bug report form');
    const modal = document.getElementById('bugReportModal');
    const textarea = document.getElementById('bugReportText');
    if (modal && textarea) {
        modal.style.display = 'flex';
        textarea.focus();
    } else {
        console.error('Bug report modal or textarea not found');
    }
}

function closeBugReportForm() {
    console.log('Closing bug report form');
    const modal = document.getElementById('bugReportModal');
    const textarea = document.getElementById('bugReportText');
    if (modal && textarea) {
        modal.style.display = 'none';
        textarea.value = '';
    }
}

async function submitBugReport() {
    console.log('submitBugReport called');
    const textarea = document.getElementById('bugReportText');
    const report = textarea.value.trim();
    
    if (!report) {
        alert('Please describe the issue before submitting.');
        return;
    }
    
    // Check if we have a game state
    if (!gameState || !gameState.game_id) {
        console.error('No game state available');
        alert('Unable to submit report - no active game. Please describe the issue and we\'ll log it.');
        
        // Log to console at least
        console.error('BUG REPORT (No Game):', report);
        console.error('Timestamp:', new Date().toISOString());
        
        // Still close the form
        closeBugReportForm();
        return;
    }
    
    try {
        console.log('Submitting bug report for game:', gameState.game_id);
        
        // Send bug report to server
        const response = await fetch(`/api/game/${gameState.game_id}/bug-report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                report: report,
                game_state: gameState,
                timestamp: new Date().toISOString()
            })
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            alert('Bug report submitted successfully. Thank you!');
            closeBugReportForm();
        } else {
            const errorText = await response.text();
            console.error('Submit failed:', errorText);
            alert('Failed to submit bug report. Please try again.');
        }
    } catch (error) {
        console.error('Error submitting bug report:', error);
        alert('Error submitting bug report. Please try again.');
    }
}

// Make bug report functions globally available immediately
window.showBugReportForm = showBugReportForm;
window.closeBugReportForm = closeBugReportForm;
window.submitBugReport = submitBugReport;

// Initialize the poker game
async function initializePokerGame(config) {
    console.log('Initializing poker game with config:', config);
    
    // Create particles for background
    createParticles();
    
    // Initialize audio context on first user interaction
    document.addEventListener('click', initAudio, { once: true });
    
    // Set up event listeners for bug report - ensure DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupBugReportListeners);
    } else {
        setupBugReportListeners();
    }
    
    // Start new game
    await startNewGame(config);
}

// Track if listeners are already set up
let bugReportListenersSetup = false;

// Set up bug report event listeners
function setupBugReportListeners() {
    // Prevent duplicate setup
    if (bugReportListenersSetup) {
        console.log('Bug report listeners already set up, skipping...');
        return;
    }
    
    console.log('Setting up bug report listeners...');
    console.log('Document ready state:', document.readyState);
    
    // Add click event to bug report button
    const bugReportBtn = document.getElementById('bugReportBtn');
    console.log('Bug report button element:', bugReportBtn);
    
    if (bugReportBtn) {
        // Remove any existing listeners
        const newBtn = bugReportBtn.cloneNode(true);
        bugReportBtn.parentNode.replaceChild(newBtn, bugReportBtn);
        
        // Get the new reference
        const btn = document.getElementById('bugReportBtn');
        
        // Test if element is clickable
        btn.style.cursor = 'pointer';
        
        // Add click listener
        btn.addEventListener('click', function(e) {
            console.log('Bug report button clicked via addEventListener!');
            e.preventDefault();
            e.stopPropagation();
            showBugReportForm();
        }, false);
        
        // Test immediate click binding
        btn.onclick = function(e) {
            console.log('Bug report button clicked via onclick!');
            e.preventDefault();
            e.stopPropagation();
            showBugReportForm();
            return false;
        };
        
        console.log('Bug report button listeners attached');
        console.log('Button onclick:', btn.onclick);
        console.log('Button listeners:', btn);
    } else {
        console.error('Bug report button not found!');
        console.error('Available elements:', document.body.innerHTML.substring(0, 500));
    }
    
    // Add click event to submit button (clone to prevent duplicate listeners)
    const submitBtn = document.getElementById('submitBugReportBtn');
    if (submitBtn) {
        const newSubmitBtn = submitBtn.cloneNode(true);
        submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);
        newSubmitBtn.addEventListener('click', submitBugReport);
    }
    
    // Add click event to cancel button (clone to prevent duplicate listeners)
    const cancelBtn = document.getElementById('cancelBugReportBtn');
    if (cancelBtn) {
        const newCancelBtn = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        newCancelBtn.addEventListener('click', closeBugReportForm);
    }
    
    // Add click outside to close modal
    const bugReportModal = document.getElementById('bugReportModal');
    if (bugReportModal) {
        bugReportModal.addEventListener('click', function(e) {
            if (e.target === bugReportModal) {
                closeBugReportForm();
            }
        });
    }
    
    // Add escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && bugReportModal && bugReportModal.style.display === 'flex') {
            closeBugReportForm();
        }
    });
    
    // Mark as setup
    bugReportListenersSetup = true;
    console.log('Bug report listeners setup complete');
}

// Create animated background particles
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random size
        const size = Math.random() * 30 + 10;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // Random horizontal position
        particle.style.left = Math.random() * 100 + '%';
        
        // Start particles from bottom or middle of screen
        const startPosition = 50 + Math.random() * 50;
        particle.style.bottom = `-${size}px`;
        particle.style.top = 'auto';
        
        // Random animation delay and duration
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (Math.random() * 20 + 20) + 's';
        
        particlesContainer.appendChild(particle);
    }
}

// Initialize audio context
function initAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
}

// Play sound effect
function playSound(soundName, variation = 0) {
    if (!soundEnabled || !audioContext || !sounds[soundName]) return;
    
    const sound = sounds[soundName];
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Add slight frequency variation for more natural sound
    const frequencyVariation = 1 + (variation * 0.1);
    oscillator.frequency.value = sound.frequency * frequencyVariation;
    
    // Vary volume slightly
    const volume = 0.1 * (0.8 + Math.random() * 0.4);
    gainNode.gain.setValueAtTime(volume, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + sound.duration / 1000);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + sound.duration / 1000);
}

// Start a new game
async function startNewGame(config) {
    try {
        console.log('Starting new game with config:', config);
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        console.log('Game start response:', data);
        
        if (data.success) {
            gameState = data.state;
            setupTable();
            
            // Process initial animations
            if (data.animations) {
                queueAnimations(data.animations);
            }
            
            // Start first hand after a delay
            console.log('Starting first hand in 2 seconds...');
            setTimeout(() => startNewHand(), 2000);
        } else {
            console.error('Failed to start game:', data.error);
        }
    } catch (error) {
        console.error('Error starting game:', error);
    }
}

// Setup the poker table
function setupTable() {
    const playerSeats = document.getElementById('playerSeats');
    playerSeats.innerHTML = '';
    
    // Set player count on body for CSS targeting
    document.body.setAttribute('data-player-count', gameState.players.length);
    
    // Create player seats
    gameState.players.forEach((player, index) => {
        const seat = createPlayerSeat(player, index);
        playerSeats.appendChild(seat);
    });
    
    // Update dealer button position
    updateDealerButton();
}

// Create a player seat element
function createPlayerSeat(player, position) {
    const seat = document.createElement('div');
    seat.className = 'player-seat';
    seat.dataset.position = position;
    seat.id = `seat_${player.id}`;
    
    // Player info box
    const info = document.createElement('div');
    info.className = 'player-info';
    info.id = `player_${player.id}`;
    
    info.innerHTML = `
        <div class="player-name">${player.name}</div>
        <div class="player-stack">$${player.stack}</div>
    `;
    
    // Hole cards container
    const cards = document.createElement('div');
    cards.className = 'player-cards';
    cards.id = `cards_${player.id}`;
    
    // Chip stack container
    const chips = document.createElement('div');
    chips.className = 'chip-stack';
    chips.id = `chips_${player.id}`;
    
    // Player bet display
    const betDisplay = document.createElement('div');
    betDisplay.className = 'player-bet-display';
    betDisplay.id = `bet_${player.id}`;
    betDisplay.style.display = 'none';
    betDisplay.innerHTML = '<span class="bet-amount">$0</span>';
    
    // Action timer (for active player)
    const timer = createActionTimer();
    timer.id = `timer_${player.id}`;
    
    seat.appendChild(info);
    seat.appendChild(cards);
    seat.appendChild(chips);
    seat.appendChild(betDisplay);
    seat.appendChild(timer);
    
    return seat;
}

// Create action timer SVG
function createActionTimer() {
    const timer = document.createElement('div');
    timer.className = 'action-timer';
    timer.style.display = 'none';
    
    timer.innerHTML = `
        <svg width="80" height="80">
            <circle cx="40" cy="40" r="35" class="timer-ring"></circle>
            <circle cx="40" cy="40" r="35" class="timer-path" 
                    stroke-dasharray="220" stroke-dashoffset="0"></circle>
            <text x="40" y="45" class="timer-text">30</text>
        </svg>
    `;
    
    return timer;
}

// Start a new hand
async function startNewHand() {
    try {
        console.log('Starting new hand for game:', gameState.game_id);
        
        // Clear any pending animations first
        animationQueue = [];
        isAnimating = false;
        
        // Clear the table before starting new hand
        clearTableForNewHand();
        
        const response = await fetch(`/api/game/${gameState.game_id}/new-hand`, {
            method: 'POST'
        });
        
        const data = await response.json();
        console.log('New hand response:', data);
        
        if (data.success) {
            // Check if game is over
            if (data.game_over) {
                console.log('Game is over! Winner:', data.winner);
                // Give players time to see the final board state before showing game over
                // Longer delay if hero won so they can savor the victory
                const delay = data.winner === 'hero' ? 8000 : 5000;
                console.log(`Showing game over screen in ${delay/1000} seconds...`);
                
                // Show a subtle countdown message
                const countdownMsg = document.createElement('div');
                countdownMsg.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(0, 0, 0, 0.8);
                    color: #FFD700;
                    padding: 1rem 2rem;
                    border-radius: 10px;
                    font-size: 1.2rem;
                    font-weight: bold;
                    z-index: 1000;
                    opacity: 0;
                    transition: opacity 0.5s ease-in;
                `;
                countdownMsg.textContent = data.winner === 'hero' ? 
                    'Congratulations! Victory is yours!' : 
                    'Game Over';
                document.body.appendChild(countdownMsg);
                
                // Fade in the message after 2 seconds
                setTimeout(() => {
                    countdownMsg.style.opacity = '1';
                }, 2000);
                
                setTimeout(() => {
                    if (countdownMsg.parentNode) {
                        countdownMsg.remove();
                    }
                    showGameOverScreen(data.winner, data.message);
                }, delay);
                return;
            }
            
            gameState = data.state;
            console.log('New hand state:', gameState);
            console.log('New hand animations:', data.animations);
            
            // Verify player hole cards are reset
            gameState.players.forEach(player => {
                console.log(`Player ${player.id} has ${player.hole_cards.length} hole cards`);
            });
            
            // Update dealer button position
            updateDealerButton();
            
            if (data.animations && data.animations.length > 0) {
                queueAnimations(data.animations);
            } else {
                console.error('No animations provided for new hand!');
                // Force UI update even without animations
                updateUI();
            }
        } else {
            console.error('Failed to start new hand:', data);
            console.error('Error details:', data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error starting new hand:', error);
    }
}

// Clear table elements for new hand
function clearTableForNewHand() {
    console.log('Clearing table for new hand');
    console.log('Board had', document.getElementById('communityCards')?.children.length || 0, 'cards before clearing');
    
    // Clear all hole cards
    document.querySelectorAll('.player-cards').forEach(cardsDiv => {
        cardsDiv.innerHTML = '';
    });
    
    // Clear community cards
    const communityCards = document.getElementById('communityCards');
    if (communityCards) {
        communityCards.innerHTML = '';
    }
    
    // Clear all chip stacks
    document.querySelectorAll('.chip-stack').forEach(chips => {
        chips.innerHTML = '';
    });
    
    // Clear all bet displays for new hand
    clearAllBetDisplays();
    
    // Remove folded class from all players
    document.querySelectorAll('.player-info').forEach(info => {
        info.classList.remove('folded', 'winner', 'active');
    });
    
    // Reset card opacity
    document.querySelectorAll('.player-cards').forEach(cards => {
        cards.style.opacity = '1';
    });
    
    // Clear any remaining player actions
    document.querySelectorAll('.player-action').forEach(action => {
        action.remove();
    });
    
    // Hide betting controls
    const bettingControls = document.getElementById('bettingControls');
    if (bettingControls) {
        bettingControls.classList.remove('active');
    }
    
    // Clear any celebration effects
    const winCelebration = document.getElementById('winCelebration');
    if (winCelebration) {
        winCelebration.innerHTML = '';
    }
    
    // Reset pot display
    const potAmount = document.getElementById('potAmount');
    if (potAmount) {
        potAmount.textContent = '$0';
    }
    
    // Update all player stacks from current game state
    if (gameState && gameState.players) {
        gameState.players.forEach(player => {
            updatePlayerStack(player.id, player.stack);
            // Mark players as busted ONLY if they have 0 chips at start of new hand
            if (player.stack === 0) {
                markPlayerAsBusted(player.id);
            }
        });
    }
}

// Queue animations for processing
function queueAnimations(animations) {
    animationQueue.push(...animations);
    processAnimationQueue();
}

// Process animation queue
async function processAnimationQueue() {
    if (isAnimating || animationQueue.length === 0) {
        console.log('Animation queue status:', { isAnimating, queueLength: animationQueue.length });
        return;
    }
    
    isAnimating = true;
    console.log(`Processing ${animationQueue.length} animations`);
    
    // Track if we're dealing board cards (phase transition)
    let hasPhaseTransition = false;
    
    while (animationQueue.length > 0) {
        const animation = animationQueue.shift();
        console.log('Playing animation:', animation.type);
        
        // Check if this is a board card animation (phase transition)
        if (animation.type === 'deal_board_card') {
            hasPhaseTransition = true;
            // Clear bet displays when transitioning to new betting round
            clearAllBetDisplays();
        }
        
        await playAnimation(animation);
    }
    
    isAnimating = false;
    
    // Add extra delay after phase transitions to let players see the new cards
    if (hasPhaseTransition) {
        console.log('Phase transition detected, adding extra delay');
        await sleep(1500);
    }
    
    // Update UI after animations
    console.log('Animations complete, updating UI...');
    console.log('Current game phase:', gameState?.phase);
    updateUI();
}

// Play individual animation
async function playAnimation(animation) {
    const delay = animation.delay || 0;
    await sleep(delay);
    
    switch (animation.type) {
        case 'sound':
            playSound(animation.sound);
            break;
            
        case 'blind_post':
            await animateBlindPost(animation);
            break;
            
        case 'deal_card':
            await animateDealCard(animation);
            break;
            
        case 'deal_board_card':
            await animateBoardCard(animation);
            break;
            
        case 'bet':
            await animateBet(animation);
            break;
            
        case 'fold':
            await animateFold(animation);
            break;
            
        case 'check':
            await animateCheck(animation);
            break;
            
        case 'delay':
            // Just a delay with optional message
            if (animation.message) {
                console.log(animation.message);
                // Show message on screen for important delays
                if (animation.message.includes('eliminated') || animation.message.includes('all-in') || animation.message.includes('All players')) {
                    const messageEl = document.createElement('div');
                    messageEl.style.cssText = `
                        position: fixed;
                        top: 30%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: rgba(0, 0, 0, 0.9);
                        color: #FFD700;
                        padding: 1.5rem 3rem;
                        border-radius: 15px;
                        font-size: 1.5rem;
                        font-weight: bold;
                        z-index: 1000;
                        opacity: 0;
                        transition: opacity 0.5s ease-in;
                        border: 2px solid #FFD700;
                        box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
                        text-align: center;
                        min-width: 400px;
                    `;
                    messageEl.textContent = animation.message;
                    document.body.appendChild(messageEl);
                    
                    // Add pulsing animation for all-in messages
                    if (animation.message.includes('All players all-in')) {
                        messageEl.style.animation = 'messagePulse 2s ease-in-out infinite';
                    }
                    
                    setTimeout(() => {
                        messageEl.style.opacity = '1';
                    }, 50);
                    
                    // Remove after the delay
                    setTimeout(() => {
                        messageEl.style.opacity = '0';
                        setTimeout(() => messageEl.remove(), 500);
                    }, Math.max(animation.delay - 500, 1000));
                }
            }
            break;
            
        case 'reveal_cards':
            await animateRevealCards(animation);
            break;
            
        case 'award_pot':
            await animateAwardPot(animation);
            break;
            
        case 'celebration':
            await animateCelebration(animation);
            break;
            
        case 'hand_complete':
            // Signal that the hand is complete - now safe to check game state
            console.log('Hand complete animation received');
            // Mark game state as ready for game over check
            if (gameState) {
                gameState.phase = 'GAME_OVER';
                // Force UI update to process game over
                setTimeout(() => updateUI(), 100);
            }
            break;
    }
}

// Animate blind posting
async function animateBlindPost(animation) {
    const player = getPlayerById(animation.player_id);
    const chips = document.getElementById(`chips_${animation.player_id}`);
    
    // Create chip element
    const chip = createChip(animation.amount);
    chips.appendChild(chip);
    
    // Update player stack
    updatePlayerStack(animation.player_id, player.stack);
    
    // Show action
    showPlayerAction(animation.player_id, `${animation.blind_type.toUpperCase()} BLIND`);
    
    playSound('chipClick');
    await sleep(300);
}

// Animate dealing card
async function animateDealCard(animation) {
    const player = gameState.players.find(p => p.id === animation.player_id);
    
    // Don't deal to busted players
    if (!player || player.stack === 0) {
        console.log(`Skipping card deal for busted/missing player ${animation.player_id}`);
        return;
    }
    
    const cardsContainer = document.getElementById(`cards_${animation.player_id}`);
    
    // Safety check: ensure we don't have more than 2 cards
    const existingCards = cardsContainer.querySelectorAll('.hole-card');
    if (existingCards.length >= 2) {
        console.warn(`Player ${animation.player_id} already has 2 cards, skipping deal`);
        return;
    }
    
    const card = document.createElement('div');
    card.className = 'hole-card face-down';
    
    // Add staggered animation delay for multiple cards
    const dealDelay = existingCards.length * 200;
    
    // Append card immediately but keep it invisible
    cardsContainer.appendChild(card);
    
    // Trigger dealing animation after a short delay
    setTimeout(() => {
        card.classList.add('dealing');
        playSound('cardFlip', Math.random());
    }, dealDelay);
    
    if (animation.is_hero && player) {
        // Show hero cards after deal animation completes
        setTimeout(() => {
            const cardData = player.hole_cards[animation.card_index];
            if (cardData) {
                // Simple reveal without complex animations
                card.classList.remove('face-down');
                card.innerHTML = formatCard(cardData);
                if (cardData.includes('♥') || cardData.includes('♦')) {
                    card.classList.add('red');
                }
            }
        }, dealDelay + 600);
    }
    
    await sleep(300 + dealDelay);
}

// Animate board card
async function animateBoardCard(animation) {
    const communityCards = document.getElementById('communityCards');
    
    // Log board card dealing for debugging
    const currentBoardCount = communityCards.children.length;
    console.log(`Dealing board card ${currentBoardCount + 1}: ${animation.card}`);
    
    const card = document.createElement('div');
    card.className = 'board-card';
    
    // Stagger board cards for better visual effect
    const baseDelay = currentBoardCount * 150;
    card.style.animationDelay = `${baseDelay}ms`;
    
    // Add phase-specific animation class
    if (currentBoardCount === 0) {
        card.classList.add('flop-card');
    } else if (currentBoardCount === 3) {
        card.classList.add('turn-card');
    } else if (currentBoardCount === 4) {
        card.classList.add('river-card');
    }
    
    card.innerHTML = formatCard(animation.card);
    
    if (animation.card.includes('♥') || animation.card.includes('♦')) {
        card.classList.add('red');
    }
    
    communityCards.appendChild(card);
    
    // Delayed sound for staggered effect
    setTimeout(() => playSound('cardFlip'), baseDelay);
    
    // Increase delay for board cards to make them more visible
    await sleep(500 + baseDelay);
}

// Animate bet/raise/call
async function animateBet(animation) {
    const player = getPlayerById(animation.player_id);
    const chips = document.getElementById(`chips_${animation.player_id}`);
    const playerInfo = document.getElementById(`player_${animation.player_id}`);
    
    // Add visual feedback to player box
    playerInfo.classList.add('betting');
    
    // Create chip stack with animation
    const chipCount = Math.min(5, Math.ceil(animation.amount / 20));
    for (let i = 0; i < chipCount; i++) {
        setTimeout(() => {
            const chip = createChip(animation.amount / chipCount);
            chip.style.opacity = '0';
            chip.style.transform = 'translateY(-20px)';
            chips.appendChild(chip);
            
            // Animate chip appearance
            setTimeout(() => {
                chip.style.transition = 'all 0.3s ease';
                chip.style.opacity = '1';
                chip.style.transform = 'translateY(0)';
            }, 10);
            
            playSound('chipClick');
        }, i * 100);
    }
    
    // Update player stack with animation
    updatePlayerStack(animation.player_id, player.stack);
    
    // Update bet displays immediately
    updatePlayerBetDisplays();
    
    // Show action with enhanced styling
    let actionText = animation.action.toUpperCase();
    let soundName = 'bet';
    
    if (animation.action === 'call') {
        actionText = `CALL $${animation.amount}`;
        soundName = 'bet';
    } else if (animation.action === 'raise') {
        actionText = `RAISE $${animation.amount}`;
        soundName = 'raise';
    } else if (animation.action === 'all_in') {
        actionText = 'ALL IN!';
        soundName = 'allIn';
        // Add special all-in animation
        playerInfo.classList.add('all-in');
    }
    
    showPlayerAction(animation.player_id, actionText);
    playSound(soundName);
    
    // Remove visual feedback
    setTimeout(() => {
        playerInfo.classList.remove('betting');
    }, 1000);
    
    await sleep(500 + (chipCount * 100));
}

// Animate fold
async function animateFold(animation) {
    const playerInfo = document.getElementById(`player_${animation.player_id}`);
    const cards = document.getElementById(`cards_${animation.player_id}`);
    
    playerInfo.classList.add('folded');
    cards.style.opacity = '0.3';
    
    showPlayerAction(animation.player_id, 'FOLD');
    playSound('fold');
    await sleep(300);
}

// Animate check
async function animateCheck(animation) {
    showPlayerAction(animation.player_id, 'CHECK');
    playSound('check');
    await sleep(300);
}

// Animate revealing cards
async function animateRevealCards(animation) {
    const cardsContainer = document.getElementById(`cards_${animation.player_id}`);
    const cards = cardsContainer.querySelectorAll('.hole-card');
    
    animation.cards.forEach((cardData, index) => {
        if (cards[index]) {
            cards[index].classList.remove('face-down');
            cards[index].innerHTML = formatCard(cardData);
            if (cardData.includes('♥') || cardData.includes('♦')) {
                cards[index].classList.add('red');
            }
        }
    });
    
    playSound('cardFlip');
    await sleep(500);
}

// Animate awarding pot
async function animateAwardPot(animation) {
    console.log('Animating pot award:', animation);
    const player = getPlayerById(animation.winner_id);
    
    if (!player) {
        console.error('Winner not found:', animation.winner_id);
        return;
    }
    
    const potAmount = document.getElementById('potAmount');
    const playerInfo = document.getElementById(`player_${animation.winner_id}`);
    const playerStack = document.querySelector(`#player_${animation.winner_id} .player-stack`);
    
    // Highlight winning cards if at showdown
    if (animation.hand_name && gameState.phase === 'SHOWDOWN') {
        highlightWinningCards(animation.winner_id);
    }
    
    // Animate pot moving to winner
    const potRect = potAmount.getBoundingClientRect();
    const playerRect = playerStack.getBoundingClientRect();
    
    // Create animated pot amount
    const animatedPot = document.createElement('div');
    animatedPot.className = 'animated-pot';
    animatedPot.textContent = `+$${animation.amount}`;
    animatedPot.style.cssText = `
        position: fixed;
        left: ${potRect.left}px;
        top: ${potRect.top}px;
        color: #FFD700;
        font-size: 1.5rem;
        font-weight: bold;
        z-index: 1000;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
    `;
    document.body.appendChild(animatedPot);
    
    // Animate to player
    setTimeout(() => {
        animatedPot.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
        animatedPot.style.left = playerRect.left + 'px';
        animatedPot.style.top = playerRect.top + 'px';
        animatedPot.style.transform = 'scale(1.2)';
    }, 50);
    
    // Update winner's stack with animation
    setTimeout(() => {
        updatePlayerStack(animation.winner_id, player.stack);
        playerStack.classList.add('stack-increase');
        setTimeout(() => playerStack.classList.remove('stack-increase'), 600);
    }, 800);
    
    // Remove animated pot
    setTimeout(() => {
        animatedPot.remove();
    }, 900);
    
    // Show win message with hand name if available
    let message;
    if (animation.hand_name) {
        message = animation.pot_number 
            ? `WIN POT ${animation.pot_number}: $${animation.amount} with ${animation.hand_name}!`
            : `WIN $${animation.amount} with ${animation.hand_name}!`;
    } else {
        message = animation.pot_number 
            ? `WIN POT ${animation.pot_number}: $${animation.amount}!`
            : `WIN $${animation.amount}!`;
    }
    showPlayerAction(animation.winner_id, message);
    
    // Clear all chip stacks with fade animation
    document.querySelectorAll('.chip-stack').forEach(chips => {
        chips.querySelectorAll('.poker-chip').forEach(chip => {
            chip.style.transition = 'opacity 0.5s ease';
            chip.style.opacity = '0';
        });
        setTimeout(() => chips.innerHTML = '', 500);
    });
    
    // Reset pot display
    potAmount.textContent = '$0';
    
    playSound('win');
    await sleep(1500);
}

// Highlight winning cards
function highlightWinningCards(winnerId) {
    const winnerCards = document.getElementById(`cards_${winnerId}`);
    if (winnerCards) {
        winnerCards.querySelectorAll('.hole-card').forEach(card => {
            card.classList.add('winning-card');
        });
        
        // Also highlight relevant board cards if possible
        // This would require knowing which cards made the hand
        document.querySelectorAll('.board-card').forEach(card => {
            card.classList.add('winning-board-card');
        });
    }
}

// Animate celebration
async function animateCelebration(animation) {
    const playerInfo = document.getElementById(`player_${animation.winner_id}`);
    playerInfo.classList.add('winner');
    
    // Create confetti
    createConfetti();
    
    await sleep(3000);
    
    playerInfo.classList.remove('winner');
}

// Create confetti particles
function createConfetti() {
    const celebration = document.getElementById('winCelebration');
    celebration.innerHTML = '';
    
    const colors = ['#FFD700', '#FF6347', '#4CAF50', '#2196F3', '#9C27B0'];
    
    for (let i = 0; i < 100; i++) {
        const particle = document.createElement('div');
        particle.className = 'confetti-particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.animationDelay = Math.random() * 3 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
        celebration.appendChild(particle);
    }
    
    setTimeout(() => {
        celebration.innerHTML = '';
    }, 5000);
}

// Helper functions
function getPlayerById(playerId) {
    return gameState.players.find(p => p.id === playerId);
}

function updatePlayerStack(playerId, stack) {
    const stackElement = document.querySelector(`#player_${playerId} .player-stack`);
    const playerInfo = document.getElementById(`player_${playerId}`);
    
    if (stackElement) {
        stackElement.textContent = `$${stack}`;
    }
}

// Mark player as busted (only called when they have 0 chips at start of new hand)
function markPlayerAsBusted(playerId) {
    const playerInfo = document.getElementById(`player_${playerId}`);
    if (!playerInfo || playerInfo.classList.contains('busted')) return;
    
    playerInfo.classList.add('busted');
    playerInfo.style.opacity = '0.5';
    playerInfo.style.filter = 'grayscale(1)';
    
    // Add BUSTED text in corner
    const bustedText = document.createElement('div');
    bustedText.className = 'busted-text';
    bustedText.textContent = 'BUSTED';
    bustedText.style.cssText = `
        position: absolute;
        top: -10px;
        right: -10px;
        background: #ff0000;
        color: #fff;
        font-size: 0.8rem;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        transform: rotate(15deg);
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        z-index: 10;
    `;
    
    playerInfo.style.position = 'relative';
    playerInfo.appendChild(bustedText);
}

function showPlayerAction(playerId, action) {
    const playerInfo = document.getElementById(`player_${playerId}`);
    
    // Remove any existing action
    const existingAction = playerInfo.querySelector('.player-action');
    if (existingAction) {
        existingAction.remove();
    }
    
    // Create new action element
    const actionElement = document.createElement('div');
    actionElement.className = 'player-action';
    actionElement.textContent = action;
    
    // Special styling for wins
    if (action.includes('WIN')) {
        actionElement.style.background = 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)';
        actionElement.style.color = '#000';
        actionElement.style.fontWeight = 'bold';
        actionElement.style.animationDuration = '3s';
    }
    
    playerInfo.appendChild(actionElement);
}

function createChip(amount) {
    const chip = document.createElement('div');
    chip.className = 'poker-chip';
    
    // Color based on amount
    if (amount >= 1000) {
        chip.classList.add('black');
    } else if (amount >= 100) {
        chip.classList.add('green');
    } else if (amount >= 25) {
        chip.classList.add('blue');
    } else if (amount >= 5) {
        chip.classList.add('red');
    }
    
    return chip;
}

// Update pot chips display
function updatePotChipsDisplay(potAmount) {
    const potChips = document.getElementById('potChips');
    if (!potChips) return;
    
    // Clear existing chips
    potChips.innerHTML = '';
    
    if (potAmount <= 0) return;
    
    // Calculate chip breakdown
    const chipValues = [1000, 100, 25, 5, 1];
    let remaining = potAmount;
    let chipCount = 0;
    const maxChips = 10; // Limit visual chips
    
    for (const value of chipValues) {
        while (remaining >= value && chipCount < maxChips) {
            const chip = createChip(value);
            chip.style.position = 'relative';
            chip.style.marginLeft = chipCount > 0 ? '-30px' : '0';
            chip.style.zIndex = chipCount;
            potChips.appendChild(chip);
            remaining -= value;
            chipCount++;
        }
        if (chipCount >= maxChips) break;
    }
}

function formatCard(cardStr) {
    if (!cardStr || cardStr === '?') return '?';
    
    let rank, suit;
    if (cardStr.startsWith('10')) {
        rank = '10';
        suit = cardStr.substring(2);
    } else {
        rank = cardStr[0];
        suit = cardStr.substring(1);
    }
    
    return `<div class="card-rank">${rank}</div><div class="card-suit">${suit}</div>`;
}

function updateDealerButton() {
    const button = document.getElementById('dealerButton');
    const dealerPlayer = gameState.players.find(p => p.is_dealer);
    
    if (dealerPlayer) {
        const playerInfo = document.getElementById(`player_${dealerPlayer.id}`);
        if (playerInfo) {
            const rect = playerInfo.getBoundingClientRect();
            const tableRect = document.querySelector('.poker-table-main').getBoundingClientRect();
            
            button.style.display = 'flex';
            // Position in top-left corner of player info box
            button.style.left = (rect.left - tableRect.left - 15) + 'px';
            button.style.top = (rect.top - tableRect.top - 15) + 'px';
        }
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Update UI after animations
function updateUI() {
    console.log('UpdateUI called');
    console.log('Game phase:', gameState?.phase);
    console.log('Action on:', gameState?.action_on);
    console.log('Players:', gameState?.players);
    
    // Update game info bar
    const potAmount = document.getElementById('potAmount');
    const tablePotAmount = document.getElementById('tablePotAmount');
    const handNumber = document.getElementById('handNumber');
    const blindsInfo = document.getElementById('blindsInfo');
    
    if (gameState) {
        // Use the server-calculated pot total
        let totalPot = gameState.current_pot_total || 0;
        
        // Fallback to client-side calculation if needed
        if (!totalPot) {
            if (gameState.pots && gameState.pots.length > 0) {
                totalPot = gameState.pots.reduce((sum, pot) => sum + pot.amount, 0);
            } else {
                // During betting rounds, calculate from player bets
                gameState.players.forEach(player => {
                    totalPot += player.current_bet || 0;
                });
            }
        }
        
        // Update pot display in info bar
        const potDisplay = `$${totalPot}`;
        if (potAmount) potAmount.textContent = potDisplay;
        
        // Update hand number
        handNumber.textContent = gameState.hand_number || '0';
        
        // Update blinds
        blindsInfo.textContent = `$${gameState.small_blind}/$${gameState.big_blind}`;
        
        // Update player bet displays
        updatePlayerBetDisplays();
        
        // Update betting controls
        updateBettingControls();
        
        // Update active player highlight
        updateActivePlayer();
        
        // Update hand strength indicator
        updateHandStrength();
        
        // Check if it's AI's turn and trigger action
        if (gameState.action_on >= 0 && gameState.action_on < gameState.players.length) {
            const activePlayer = gameState.players[gameState.action_on];
            console.log('Active player details:', {
                id: activePlayer.id,
                name: activePlayer.name,
                is_ai: activePlayer.is_ai,
                has_folded: activePlayer.has_folded,
                stack: activePlayer.stack,
                current_bet: activePlayer.current_bet
            });
            
            if (activePlayer && activePlayer.is_ai && !activePlayer.has_folded && activePlayer.stack > 0) {
                console.log('AI should act now. Triggering AI action for:', activePlayer.id);
                // Wait longer if we just transitioned phases
                const delay = isAnimating ? 3000 : 2000;
                setTimeout(() => {
                    console.log('Calling triggerAIAction for:', activePlayer.id);
                    triggerAIAction();
                }, delay);
            } else {
                console.log('Not AI turn or player cannot act');
            }
        } else {
            console.log('No valid action_on value:', gameState.action_on);
        }
        
        // Check if hand is over
        if (gameState.phase === 'GAME_OVER') {
            console.log('Hand is over - checking if game continues...');
            
            // CRITICAL: Don't process game over until ALL animations are complete!
            if (isAnimating || animationQueue.length > 0) {
                console.log('Animations still playing - waiting to process game over');
                console.log(`isAnimating: ${isAnimating}, queue length: ${animationQueue.length}`);
                // Check again after animations complete
                setTimeout(() => updateUI(), 1000);
                return;
            }
            
            // Count players with chips to determine if game is truly over
            const playersWithChips = gameState.players.filter(p => p.stack > 0).length;
            
            if (playersWithChips <= 1) {
                console.log('Game is truly over - only one player has chips');
                // Add extra delay to ensure all animations are visible
                setTimeout(() => {
                    startNewHand();
                }, 3000);
            } else {
                console.log('Hand is over but game continues - starting new hand');
                // Multiple players still have chips, continue the game
                setTimeout(() => {
                    animationQueue = [];
                    isAnimating = false;
                    startNewHand();
                }, 5000);
            }
        } else {
            // Log current game state to help debug phase skipping
            console.log('Current game state after UI update:');
            console.log('- Phase:', gameState.phase);
            console.log('- Board cards:', gameState.board_cards?.length || 0);
            console.log('- Action on:', gameState.action_on);
            console.log('- Current bet:', gameState.current_bet);
        }
    } else {
        console.error('No gameState available!');
    }
}

// Update betting controls based on game state
function updateBettingControls() {
    const controls = document.getElementById('bettingControls');
    const hero = gameState.players.find(p => !p.is_ai);
    
    if (!hero || gameState.action_on !== hero.position || hero.has_folded) {
        controls.classList.remove('active');
        return;
    }
    
    controls.classList.add('active');
    playSound('turn', Math.random());
    
    // Re-enable controls when it's hero's turn
    enableBettingControls();
    
    // Update button states
    const checkBtn = document.getElementById('checkBtn');
    const callBtn = document.getElementById('callBtn');
    const callAmount = document.getElementById('callAmount');
    const raiseBtn = document.getElementById('raiseBtn');
    const betSlider = document.getElementById('betSlider');
    const betAmount = document.getElementById('betAmount');
    const allInBtn = document.querySelector('.bet-button.all-in');
    
    const toCall = gameState.current_bet - hero.current_bet;
    
    // Check/Call logic with blind rules
    const isBigBlind = hero.is_big_blind;
    const isPreFlop = gameState.phase === 'PRE_FLOP';
    
    if (isPreFlop && isBigBlind && gameState.current_bet === gameState.big_blind) {
        // Big blind can check if no one raised
        checkBtn.style.display = 'block';
        callBtn.style.display = 'none';
    } else if (toCall === 0) {
        // Post-flop or when bet is matched
        checkBtn.style.display = 'block';
        callBtn.style.display = 'none';
    } else {
        // Must call or fold
        checkBtn.style.display = 'none';
        callBtn.style.display = 'block';
        const callAmountValue = Math.min(toCall, hero.stack);
        callAmount.textContent = callAmountValue;
        
        // If call would be all-in, highlight the button
        if (callAmountValue === hero.stack) {
            callBtn.classList.add('will-be-all-in');
            callBtn.innerHTML = `ALL IN $<span id="callAmount">${callAmountValue}</span>`;
        } else {
            callBtn.classList.remove('will-be-all-in');
            callBtn.innerHTML = `CALL $<span id="callAmount">${callAmountValue}</span>`;
        }
    }
    
    // Raise logic
    const minRaise = gameState.min_raise;
    const maxRaise = hero.stack - toCall;
    
    if (maxRaise <= 0) {
        raiseBtn.disabled = true;
        betSlider.disabled = true;
        allInBtn.disabled = toCall >= hero.stack; // Disable all-in if we can't even call
    } else {
        raiseBtn.disabled = false;
        betSlider.disabled = false;
        allInBtn.disabled = false;
        betSlider.min = minRaise;
        betSlider.max = maxRaise;
        betSlider.value = Math.min(minRaise * 2, maxRaise);
        betAmount.textContent = betSlider.value;
        
        // Update raise button if slider is at max
        updateRaiseButtonState();
    }
}

// Update raise button based on slider value
function updateRaiseButtonState() {
    const hero = gameState.players.find(p => !p.is_ai);
    const betSlider = document.getElementById('betSlider');
    const raiseBtn = document.getElementById('raiseBtn');
    const toCall = gameState.current_bet - hero.current_bet;
    const maxRaise = hero.stack - toCall;
    
    if (parseInt(betSlider.value) === maxRaise) {
        raiseBtn.classList.add('will-be-all-in');
        raiseBtn.textContent = 'ALL IN';
    } else {
        raiseBtn.classList.remove('will-be-all-in');
        raiseBtn.textContent = 'RAISE';
    }
}

// Update bet amount display
document.getElementById('betSlider')?.addEventListener('input', (e) => {
    document.getElementById('betAmount').textContent = e.target.value;
    updateRaiseButtonState();
});


// Update player bet displays
function updatePlayerBetDisplays() {
    if (!gameState || !gameState.players) return;
    
    // Determine if we're in a betting round with actual bets (not just blinds)
    const isPreFlopBlinds = gameState.phase === 'PRE_FLOP' && 
                           gameState.current_bet <= gameState.big_blind;
    
    gameState.players.forEach(player => {
        const betDisplay = document.getElementById(`bet_${player.id}`);
        if (betDisplay) {
            // Show bet if player has chips in pot and hasn't folded
            // Don't show during pre-flop if it's just blinds
            const shouldShowBet = player.current_bet > 0 && 
                                !player.has_folded && 
                                (!isPreFlopBlinds || player.current_bet > gameState.big_blind);
            
            if (shouldShowBet) {
                betDisplay.style.display = 'block';
                betDisplay.querySelector('.bet-amount').textContent = `$${player.current_bet}`;
            } else {
                betDisplay.style.display = 'none';
            }
        }
    });
}

// Clear all bet displays
function clearAllBetDisplays() {
    document.querySelectorAll('.player-bet-display').forEach(display => {
        display.style.display = 'none';
    });
}

// Update active player highlight
function updateActivePlayer() {
    // Remove all active classes and timers
    document.querySelectorAll('.player-info').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelectorAll('.action-timer').forEach(timer => {
        timer.style.display = 'none';
    });
    
    // Add active class to current player
    if (gameState.action_on >= 0) {
        const activePlayer = gameState.players[gameState.action_on];
        const playerInfo = document.getElementById(`player_${activePlayer.id}`);
        const timer = document.getElementById(`timer_${activePlayer.id}`);
        
        if (playerInfo) {
            playerInfo.classList.add('active');
            
            // Show timer for active player
            if (timer && !activePlayer.is_ai) {
                timer.style.display = 'block';
                startActionTimer(activePlayer.id);
            }
        }
    }
}

// Start action timer countdown
function startActionTimer(playerId) {
    const timer = document.getElementById(`timer_${playerId}`);
    if (!timer) return;
    
    const timerPath = timer.querySelector('.timer-path');
    const timerText = timer.querySelector('.timer-text');
    
    let timeRemaining = 30;
    const circumference = 2 * Math.PI * 35; // radius is 35
    
    const interval = setInterval(() => {
        timeRemaining--;
        timerText.textContent = timeRemaining;
        
        // Update timer ring
        const offset = circumference - (timeRemaining / 30) * circumference;
        timerPath.style.strokeDashoffset = offset;
        
        // Change color based on time remaining
        if (timeRemaining <= 5) {
            timerPath.classList.add('danger');
            timerPath.classList.remove('warning');
        } else if (timeRemaining <= 10) {
            timerPath.classList.add('warning');
        }
        
        if (timeRemaining <= 0) {
            clearInterval(interval);
            // Auto-fold if time runs out
            if (!gameState.players.find(p => p.id === playerId).is_ai) {
                playerAction('fold');
            }
        }
        
        // Clear timer if it's no longer this player's turn
        const activePlayer = gameState.players[gameState.action_on];
        if (!activePlayer || activePlayer.id !== playerId) {
            clearInterval(interval);
            timer.style.display = 'none';
        }
    }, 1000);
}

// Update hand strength indicator
async function updateHandStrength() {
    const hero = gameState?.players?.find(p => !p.is_ai);
    const container = document.getElementById('handStrengthContainer');
    
    if (!hero || !hero.hole_cards || hero.hole_cards.length !== 2 || !gameId) {
        container.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/game/${gameId}/hand-strength/${hero.id}`);
        const data = await response.json();
        
        if (data.success && data.has_cards) {
            // Show container with fade-in animation
            if (container.style.display === 'none') {
                container.style.display = 'block';
                container.style.opacity = '0';
                setTimeout(() => {
                    container.style.transition = 'opacity 0.3s ease';
                    container.style.opacity = '1';
                }, 10);
            }
            
            // Update win probability with animation
            const winProb = Math.round(data.win_probability * 100);
            const tieProb = Math.round(data.tie_probability * 100);
            
            // Animate number changes
            animateNumber('winProb', winProb);
            animateNumber('tieProb', tieProb);
            animateNumber('strengthPercentage', winProb);
            
            // Update strength bar with smooth transition
            const strengthBar = document.getElementById('strengthBar');
            const currentWidth = parseFloat(strengthBar.style.width) || 0;
            strengthBar.style.width = winProb + '%';
            
            // Add pulse animation if strength changed significantly
            if (Math.abs(currentWidth - winProb) > 20) {
                strengthBar.classList.add('pulse');
                setTimeout(() => strengthBar.classList.remove('pulse'), 600);
            }
            
            // Update current hand name with highlight effect
            const handNameEl = document.getElementById('currentHandName');
            const previousHand = handNameEl.textContent;
            if (data.current_hand) {
                handNameEl.textContent = data.current_hand;
                handNameEl.style.display = 'inline';
                
                // Highlight if hand improved
                if (previousHand && previousHand !== data.current_hand) {
                    handNameEl.classList.add('hand-improved');
                    setTimeout(() => handNameEl.classList.remove('hand-improved'), 1000);
                }
            } else {
                handNameEl.style.display = 'none';
            }
            
            // Update pot odds if facing a bet
            const potOddsInfo = document.getElementById('potOddsInfo');
            if (data.to_call > 0) {
                potOddsInfo.style.display = 'block';
                document.getElementById('toCallAmount').textContent = data.to_call;
                document.getElementById('potSizeDisplay').textContent = data.pot_size;
                document.getElementById('oddsNeeded').textContent = data.pot_odds_percentage + '%';
                
                // Update odds result with animation
                const oddsResult = document.getElementById('oddsResult');
                const wasGood = oddsResult.classList.contains('good');
                if (data.has_direct_odds) {
                    oddsResult.textContent = 'CALL +EV';
                    oddsResult.className = 'odds-result good';
                    if (!wasGood) {
                        oddsResult.classList.add('flash-good');
                        setTimeout(() => oddsResult.classList.remove('flash-good'), 600);
                    }
                } else {
                    oddsResult.textContent = 'FOLD';
                    oddsResult.className = 'odds-result bad';
                    if (wasGood) {
                        oddsResult.classList.add('flash-bad');
                        setTimeout(() => oddsResult.classList.remove('flash-bad'), 600);
                    }
                }
            } else {
                potOddsInfo.style.display = 'none';
            }
        } else {
            container.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching hand strength:', error);
        container.style.display = 'none';
    }
}

// Helper function to animate number changes
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const currentValue = parseInt(element.textContent) || 0;
    const difference = targetValue - currentValue;
    const duration = 300; // ms
    const steps = 20;
    const stepValue = difference / steps;
    const stepDuration = duration / steps;
    
    let step = 0;
    const interval = setInterval(() => {
        step++;
        const newValue = Math.round(currentValue + (stepValue * step));
        element.textContent = newValue + '%';
        
        if (step >= steps) {
            element.textContent = targetValue + '%';
            clearInterval(interval);
        }
    }, stepDuration);
}

// Track if we're processing an action
let isProcessingAction = false;

// Player action handler
async function playerAction(action) {
    // Prevent multiple simultaneous actions
    if (isProcessingAction) {
        console.log('Already processing an action, ignoring click');
        return;
    }
    
    const hero = gameState.players.find(p => !p.is_ai);
    if (!hero || gameState.action_on !== hero.position) return;
    
    let amount = 0;
    if (action === 'raise') {
        amount = parseInt(document.getElementById('betSlider').value);
    }
    
    // Disable all betting buttons immediately
    disableBettingControls();
    isProcessingAction = true;
    
    try {
        const response = await fetch(`/api/game/${gameState.game_id}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_id: hero.id,
                action: action,
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState = data.state;
            queueAnimations(data.animations);
            
            // If it's AI's turn, trigger AI action
            if (gameState.action_on >= 0) {
                const nextPlayer = gameState.players[gameState.action_on];
                if (nextPlayer.is_ai) {
                    // Add longer delay for AI to prevent rapid actions
                    console.log('AI turn after player action, waiting before trigger');
                    setTimeout(() => triggerAIAction(), 2000);
                }
            }
        } else {
            console.error('Action failed:', data.error);
            // Re-enable controls on error
            enableBettingControls();
        }
    } catch (error) {
        console.error('Error processing action:', error);
        // Re-enable controls on error
        enableBettingControls();
    } finally {
        // Reset processing flag after a short delay
        setTimeout(() => {
            isProcessingAction = false;
        }, 500);
    }
}

// Disable all betting controls
function disableBettingControls() {
    const buttons = document.querySelectorAll('.bet-button');
    const slider = document.getElementById('betSlider');
    
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
    });
    
    if (slider) {
        slider.disabled = true;
    }
}

// Enable betting controls (called when it's hero's turn again)
function enableBettingControls() {
    const buttons = document.querySelectorAll('.bet-button');
    const slider = document.getElementById('betSlider');
    
    buttons.forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
    });
    
    if (slider) {
        slider.disabled = false;
    }
}

// Trigger AI action
async function triggerAIAction() {
    console.log('triggerAIAction called');
    console.log('Current action_on:', gameState.action_on);
    
    if (gameState.action_on < 0 || gameState.action_on >= gameState.players.length) {
        console.error('Invalid action_on:', gameState.action_on);
        return;
    }
    
    const activePlayer = gameState.players[gameState.action_on];
    console.log('Active player in triggerAIAction:', activePlayer);
    
    if (!activePlayer || !activePlayer.is_ai) {
        console.log('Not an AI player or player not found');
        return;
    }
    
    try {
        console.log('Making AI action request for player:', activePlayer.id);
        const response = await fetch(`/api/game/${gameState.game_id}/ai-action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_id: activePlayer.id
            })
        });
        
        console.log('AI action response status:', response.status);
        const data = await response.json();
        console.log('AI action response data:', data);
        
        if (data.success) {
            gameState = data.state;
            console.log('New game state after AI action:', gameState);
            console.log('Phase after AI action:', gameState.phase);
            console.log('Board cards after AI action:', gameState.board_cards ? gameState.board_cards.length : 0);
            
            // Check if multiple phases have been skipped
            const boardCardCount = gameState.board_cards ? gameState.board_cards.length : 0;
            if (gameState.phase === 'RIVER' && boardCardCount === 5) {
                console.warn('WARNING: All 5 community cards dealt at once!');
            }
            
            queueAnimations(data.animations);
            
            // Continue with next AI if needed, but with proper delay
            if (gameState.action_on >= 0 && gameState.action_on < gameState.players.length) {
                const nextPlayer = gameState.players[gameState.action_on];
                console.log('Next player after AI action:', nextPlayer);
                if (nextPlayer && nextPlayer.is_ai && !nextPlayer.has_folded) {
                    console.log('Next player is also AI, scheduling action with longer delay');
                    // Increase delay to make AI actions more visible and realistic
                    setTimeout(() => triggerAIAction(), 2500 + Math.random() * 2500);
                }
            }
            
            // Check if hand is over
            if (gameState.phase === 'GAME_OVER') {
                console.log('Hand is over after AI action - checking if game continues...');
                const playersWithChips = gameState.players.filter(p => p.stack > 0).length;
                
                if (playersWithChips <= 1) {
                    console.log('Game is truly over - only one player has chips');
                    // Trigger startNewHand which will detect game over and show the screen
                    setTimeout(() => {
                        startNewHand();
                    }, 2000);
                } else {
                    console.log('Hand is over but game continues - starting new hand in 5 seconds');
                    setTimeout(() => {
                        animationQueue = [];
                        isAnimating = false;
                        startNewHand();
                    }, 5000);
                }
            }
        } else {
            console.error('AI action failed:', data.error);
        }
    } catch (error) {
        console.error('Error with AI action:', error);
        console.error('Error details:', error.stack);
    }
}

// Toggle sound
function toggleSound() {
    soundEnabled = !soundEnabled;
    const toggle = document.getElementById('soundToggle');
    toggle.textContent = soundEnabled ? '🔊' : '🔇';
    toggle.classList.toggle('muted', !soundEnabled);
}

// Leave game
function leaveGame() {
    if (confirm('Are you sure you want to leave the table?')) {
        window.location.href = '/';
    }
}

// Show game over screen
function showGameOverScreen(winnerId, message) {
    console.log('Showing game over screen');
    
    // Wait a bit to ensure all animations have completed
    setTimeout(() => {
        // Create game over overlay with fade-in animation
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9000;  /* Much lower than bug report button (99999) */
            opacity: 0;
            transition: opacity 1s ease-in;
        `;
        
        // Force bug report button to stay on top
        const bugReportBtn = document.getElementById('bugReportBtn');
        if (bugReportBtn) {
            // Temporarily boost z-index even higher
            bugReportBtn.style.zIndex = '999999';
            bugReportBtn.style.position = 'fixed';  // Ensure it's fixed positioned
        }
    
    // Trigger fade-in after adding to DOM
    setTimeout(() => {
        overlay.style.opacity = '1';
    }, 50);
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border: 3px solid #FFD700;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        box-shadow: 0 0 50px rgba(255, 215, 0, 0.5);
        position: relative;
    `;
    
    const title = document.createElement('h1');
    title.textContent = 'GAME OVER!';
    title.style.cssText = `
        color: #FFD700;
        font-size: 3rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
    `;
    
    const messageEl = document.createElement('h2');
    messageEl.textContent = message;
    messageEl.style.cssText = `
        color: #fff;
        font-size: 2rem;
        margin-bottom: 2rem;
    `;
    
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 2rem;
        margin-top: 2rem;
    `;
    
    const playAgainBtn = document.createElement('button');
    playAgainBtn.textContent = 'Play Again';
    playAgainBtn.style.cssText = `
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        border: none;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    `;
    playAgainBtn.onclick = () => {
        window.location.href = '/game/lobby';
    };
    
    const mainMenuBtn = document.createElement('button');
    mainMenuBtn.textContent = 'Main Menu';
    mainMenuBtn.style.cssText = `
        background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%);
        color: #fff;
        border: none;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    `;
    mainMenuBtn.onclick = () => {
        window.location.href = '/';
    };
    
    content.appendChild(title);
    content.appendChild(messageEl);
    buttonContainer.appendChild(playAgainBtn);
    buttonContainer.appendChild(mainMenuBtn);
    content.appendChild(buttonContainer);
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    
        // Create celebration if player won
        if (winnerId === 'hero') {
            createConfetti();
            playSound('win');
        }
    }, 1000); // Add 1 second delay before showing game over screen
}

// (Bug report functions moved to top of file)

// Make functions globally available immediately
window.playerAction = playerAction;
window.toggleSound = toggleSound;
window.leaveGame = leaveGame;
window.showBugReportForm = showBugReportForm;
window.closeBugReportForm = closeBugReportForm;
window.submitBugReport = submitBugReport;

// Also attach to window on load as backup
window.addEventListener('load', function() {
    console.log('Window loaded, setting up bug report again...');
    setupBugReportListeners();
});