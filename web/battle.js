/**
 * Pokemon Battle Simulator - JavaScript Frontend
 */

// Global state
const battleState = {
    pokemon1: null,
    pokemon2: null,
    pokemon1Moves: [],
    pokemon2Moves: [],
    battleInProgress: false,
    currentBattle: null,
    websocket: null
};

// Type colors mapping
const typeColors = {
    normal: '#a8a878',
    fire: '#f08030',
    water: '#6890f0',
    electric: '#f8d030',
    grass: '#78c850',
    ice: '#98d8d8',
    fighting: '#c03028',
    poison: '#a040a0',
    ground: '#e0c068',
    flying: '#a890f0',
    psychic: '#f85888',
    bug: '#a8b820',
    rock: '#b8a038',
    ghost: '#705898',
    dragon: '#7038f8',
    dark: '#705848',
    steel: '#b8b8d0',
    fairy: '#ee99ac'
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeLevelSliders();
    initializeMoveSelects();
    setupEventListeners();
    
    console.log('Pokemon Battle Simulator loaded!');
});

/**
 * Initialize level range sliders
 */
function initializeLevelSliders() {
    const level1Slider = document.getElementById('pokemon1Level');
    const level2Slider = document.getElementById('pokemon2Level');
    const level1Value = document.getElementById('pokemon1LevelValue');
    const level2Value = document.getElementById('pokemon2LevelValue');
    
    level1Slider.addEventListener('input', function() {
        level1Value.textContent = this.value;
        updatePokemonStats(1);
    });
    
    level2Slider.addEventListener('input', function() {
        level2Value.textContent = this.value;
        updatePokemonStats(2);
    });
}

/**
 * Initialize move select dropdowns
 */
function initializeMoveSelects() {
    // Add change listeners to move selects
    for (let p = 1; p <= 2; p++) {
        for (let m = 1; m <= 4; m++) {
            const select = document.getElementById(`pokemon${p}Move${m}`);
            if (select) {
                select.addEventListener('change', function() {
                    updateMoveInfo(p, m, this.value);
                    checkBattleReady();
                });
            }
        }
    }
}

/**
 * Setup additional event listeners
 */
function setupEventListeners() {
    // Pokemon name inputs
    document.getElementById('pokemon1Name').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') loadPokemon(1);
    });
    
    document.getElementById('pokemon2Name').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') loadPokemon(2);
    });
}

/**
 * Load Pokemon data
 */
async function loadPokemon(pokemonNumber) {
    const nameInput = document.getElementById(`pokemon${pokemonNumber}Name`);
    const pokemonName = nameInput.value.trim().toLowerCase();
    
    if (!pokemonName) {
        showError('Please enter a Pokémon name');
        return;
    }
    
    showLoading('Loading Pokémon data...');
    
    try {
        // Load Pokemon data
        const pokemonResponse = await fetch(`/api/pokemon/${pokemonName}`);
        if (!pokemonResponse.ok) {
            throw new Error('Pokémon not found');
        }
        const pokemonData = await pokemonResponse.json();
        
        // Load Pokemon moves
        const level = document.getElementById(`pokemon${pokemonNumber}Level`).value;
        const movesResponse = await fetch(`/api/pokemon/${pokemonName}/moves?level=${level}`);
        if (!movesResponse.ok) {
            throw new Error('Failed to load moves');
        }
        const movesData = await movesResponse.json();
        
        // Store data
        battleState[`pokemon${pokemonNumber}`] = pokemonData;
        battleState[`pokemon${pokemonNumber}Moves`] = movesData.moves;
        
        // Update UI
        updatePokemonPreview(pokemonNumber, pokemonData);
        updateMoveOptions(pokemonNumber, movesData.moves);
        
        hideLoading();
        showSuccess(`${pokemonData.name} loaded successfully!`);
        
    } catch (error) {
        hideLoading();
        showError(`Failed to load Pokémon: ${error.message}`);
    }
}

/**
 * Update Pokemon preview display
 */
function updatePokemonPreview(pokemonNumber, pokemonData) {
    const preview = document.getElementById(`pokemon${pokemonNumber}Preview`);
    const sprite = document.getElementById(`pokemon${pokemonNumber}Sprite`);
    const info = document.getElementById(`pokemon${pokemonNumber}Info`);
    
    // Update sprite
    if (pokemonData.sprites.front_default) {
        sprite.src = pokemonData.sprites.front_default;
        sprite.alt = pokemonData.name;
    }
    
    // Update info
    const level = document.getElementById(`pokemon${pokemonNumber}Level`).value;
    const stats = calculateStatsAtLevel(pokemonData.base_stats, parseInt(level));
    
    info.innerHTML = `
        <div class="pokemon-name">${pokemonData.name}</div>
        <div class="pokemon-types">
            ${pokemonData.types.map(type => 
                `<span class="type-badge type-${type}">${type.toUpperCase()}</span>`
            ).join('')}
        </div>
        <div class="pokemon-stats">
            HP: ${stats.hp} | ATK: ${stats.attack} | DEF: ${stats.defense}<br>
            SP.ATK: ${stats.special_attack} | SP.DEF: ${stats.special_defense} | SPD: ${stats.speed}
        </div>
    `;
}

/**
 * Calculate stats at specific level
 */
function calculateStatsAtLevel(baseStats, level) {
    const calcHP = (base, level) => Math.floor(((2 * base * level) / 100) + level + 10);
    const calcStat = (base, level) => Math.floor(((2 * base * level) / 100) + 5);
    
    return {
        hp: calcHP(baseStats.hp, level),
        attack: calcStat(baseStats.attack, level),
        defense: calcStat(baseStats.defense, level),
        special_attack: calcStat(baseStats.special_attack, level),
        special_defense: calcStat(baseStats.special_defense, level),
        speed: calcStat(baseStats.speed, level)
    };
}

/**
 * Update Pokemon stats when level changes
 */
function updatePokemonStats(pokemonNumber) {
    const pokemon = battleState[`pokemon${pokemonNumber}`];
    if (pokemon) {
        updatePokemonPreview(pokemonNumber, pokemon);
    }
}

/**
 * Update move select options
 */
function updateMoveOptions(pokemonNumber, moves) {
    for (let i = 1; i <= 4; i++) {
        const select = document.getElementById(`pokemon${pokemonNumber}Move${i}`);
        
        // Clear existing options
        select.innerHTML = '<option value="">Select Move</option>';
        
        // Add move options
        moves.forEach(move => {
            const option = document.createElement('option');
            option.value = move.name;
            option.textContent = move.display_name;
            option.dataset.type = move.type;
            option.dataset.power = move.power || '—';
            option.dataset.accuracy = move.accuracy || '—';
            option.dataset.pp = move.pp;
            option.dataset.category = move.category;
            option.dataset.effect = move.effect;
            select.appendChild(option);
        });
    }
}

/**
 * Update move info display when move is selected
 */
function updateMoveInfo(pokemonNumber, moveSlot, moveName) {
    const infoDiv = document.getElementById(`pokemon${pokemonNumber}Move${moveSlot}Info`);
    const select = document.getElementById(`pokemon${pokemonNumber}Move${moveSlot}`);
    const selectedOption = select.selectedOptions[0];
    
    if (!moveName || !selectedOption) {
        infoDiv.innerHTML = '';
        return;
    }
    
    const type = selectedOption.dataset.type;
    const power = selectedOption.dataset.power;
    const accuracy = selectedOption.dataset.accuracy;
    const pp = selectedOption.dataset.pp;
    const category = selectedOption.dataset.category;
    const effect = selectedOption.dataset.effect;
    
    infoDiv.innerHTML = `
        <div class="move-details">
            <span class="move-type type-${type}">${type.toUpperCase()}</span>
            <span class="move-stat">Power: ${power}</span>
            <span class="move-stat">Accuracy: ${accuracy}${accuracy !== '—' ? '%' : ''}</span>
            <span class="move-stat">PP: ${pp}</span>
            <span class="move-stat">Category: ${category}</span>
        </div>
        <div class="move-effect">${effect.substring(0, 100)}${effect.length > 100 ? '...' : ''}</div>
    `;
}

/**
 * Check if battle configuration is ready
 */
function checkBattleReady() {
    const pokemon1 = battleState.pokemon1;
    const pokemon2 = battleState.pokemon2;
    
    if (!pokemon1 || !pokemon2) {
        document.getElementById('battleBtn').disabled = true;
        return;
    }
    
    // Check if all moves are selected
    let allMovesSelected = true;
    for (let p = 1; p <= 2; p++) {
        for (let m = 1; m <= 4; m++) {
            const select = document.getElementById(`pokemon${p}Move${m}`);
            if (!select.value) {
                allMovesSelected = false;
                break;
            }
        }
        if (!allMovesSelected) break;
    }
    
    document.getElementById('battleBtn').disabled = !allMovesSelected;
}

/**
 * Validate battle configuration
 */
async function validateBattle() {
    if (!battleState.pokemon1 || !battleState.pokemon2) {
        showError('Please load both Pokémon first');
        return;
    }
    
    const config = getBattleConfig();
    showLoading('Validating battle configuration...');
    
    try {
        const response = await fetch('/api/battle/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        hideLoading();
        showValidationResults(result);
        
    } catch (error) {
        hideLoading();
        showError(`Validation failed: ${error.message}`);
    }
}

/**
 * Show validation results
 */
function showValidationResults(result) {
    const resultsDiv = document.getElementById('validationResults');
    const listElement = document.getElementById('validationList');
    
    resultsDiv.style.display = 'block';
    resultsDiv.className = `validation-results ${result.valid ? 'success' : 'error'}`;
    
    listElement.innerHTML = '';
    
    if (result.valid) {
        const li = document.createElement('li');
        li.textContent = '✓ Battle configuration is valid!';
        li.className = 'success';
        listElement.appendChild(li);
        
        document.getElementById('battleBtn').disabled = false;
    } else {
        result.errors.forEach(error => {
            const li = document.createElement('li');
            li.textContent = `✗ ${error}`;
            li.className = 'error';
            listElement.appendChild(li);
        });
        
        document.getElementById('battleBtn').disabled = true;
    }
}

/**
 * Get current battle configuration
 */
function getBattleConfig() {
    const getMoves = (pokemonNumber) => {
        const moves = [];
        for (let i = 1; i <= 4; i++) {
            const select = document.getElementById(`pokemon${pokemonNumber}Move${i}`);
            moves.push(select.value);
        }
        return moves;
    };
    
    return {
        pokemon1: {
            name: battleState.pokemon1.name,
            level: parseInt(document.getElementById('pokemon1Level').value),
            moves: getMoves(1)
        },
        pokemon2: {
            name: battleState.pokemon2.name,
            level: parseInt(document.getElementById('pokemon2Level').value),
            moves: getMoves(2)
        }
    };
}

/**
 * Start battle simulation
 */
async function startBattle() {
    if (battleState.battleInProgress) {
        showError('Battle already in progress');
        return;
    }
    
    const config = getBattleConfig();
    
    showLoading('Starting battle...');
    battleState.battleInProgress = true;
    
    try {
        // Hide setup, show arena
        document.getElementById('battleSetup').style.display = 'none';
        document.getElementById('battleArena').style.display = 'block';
        
        // Initialize battle UI
        initializeBattleArena(config);
        
        // Start battle simulation
        const response = await fetch('/api/battle/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            battleState.currentBattle = result;
            animateBattle(result);
        } else {
            throw new Error(result.error || 'Battle simulation failed');
        }
        
    } catch (error) {
        hideLoading();
        battleState.battleInProgress = false;
        showError(`Battle failed: ${error.message}`);
        backToSetup();
    }
}

/**
 * Initialize battle arena UI
 */
function initializeBattleArena(config) {
    // Set Pokemon sprites and names
    document.getElementById('battleSprite1').src = battleState.pokemon1.sprites.front_default;
    document.getElementById('battleSprite2').src = battleState.pokemon2.sprites.front_default;
    
    document.getElementById('battleName1').textContent = config.pokemon1.name;
    document.getElementById('battleName2').textContent = config.pokemon2.name;
    
    // Initialize health bars
    updateHealthBar(1, 100);
    updateHealthBar(2, 100);
    
    // Clear battle log
    document.getElementById('battleLog').innerHTML = '';
    
    // Reset turn counter
    document.getElementById('currentTurn').textContent = '1';
}

/**
 * Animate battle sequence
 */
async function animateBattle(battleResult) {
    const battleLog = document.getElementById('battleLog');
    let turnNumber = 1;
    
    for (const turn of battleResult.battle_log) {
        // Update turn counter
        document.getElementById('currentTurn').textContent = turn.turn;
        
        // Add turn header to log
        const turnHeader = document.createElement('div');
        turnHeader.className = 'log-entry log-turn';
        turnHeader.textContent = `Turn ${turn.turn}:`;
        battleLog.appendChild(turnHeader);
        
        // Animate events
        for (const event of turn.events) {
            await animateEvent(event);
            
            // Add to battle log
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${getLogClass(event)}`;
            logEntry.textContent = event.message;
            battleLog.appendChild(logEntry);
            
            // Auto-scroll log
            battleLog.scrollTop = battleLog.scrollHeight;
            
            // Pause between events
            await sleep(800);
        }
        
        // Update Pokemon states
        if (turn.pokemon_states) {
            updatePokemonStates(turn.pokemon_states);
        }
        
        // Longer pause between turns
        await sleep(1000);
    }
    
    // Show results
    showBattleResults(battleResult);
}

/**
 * Animate individual battle event
 */
async function animateEvent(event) {
    const sprite1 = document.getElementById('battleSprite1');
    const sprite2 = document.getElementById('battleSprite2');
    
    switch (event.type) {
        case 'move_use':
            // Animate attacker
            const attackerSprite = event.pokemon === battleState.pokemon1.name ? sprite1 : sprite2;
            attackerSprite.classList.add('attack-animation');
            setTimeout(() => attackerSprite.classList.remove('attack-animation'), 500);
            break;
            
        case 'damage':
            // Animate damage on defender
            const defenderSprite = event.defender === battleState.pokemon1.name ? sprite1 : sprite2;
            defenderSprite.classList.add('damage-animation');
            setTimeout(() => defenderSprite.classList.remove('damage-animation'), 500);
            break;
            
        case 'critical':
            // Screen flash effect
            document.body.style.filter = 'brightness(1.5)';
            setTimeout(() => document.body.style.filter = '', 200);
            break;
            
        case 'faint':
            // Faint animation
            const faintedSprite = event.pokemon === battleState.pokemon1.name ? sprite1 : sprite2;
            faintedSprite.classList.add('faint-animation');
            break;
    }
}

/**
 * Update Pokemon states in battle UI
 */
function updatePokemonStates(states) {
    Object.keys(states).forEach((pokemonName, index) => {
        const pokemonNumber = index + 1;
        const state = states[pokemonName];
        
        // Update health bar
        const healthPercentage = (state.hp.current / state.hp.max) * 100;
        updateHealthBar(pokemonNumber, healthPercentage);
        
        // Update health text
        document.getElementById(`healthText${pokemonNumber}`).textContent = 
            `${state.hp.current}/${state.hp.max} HP`;
        
        // Update status effects
        updateStatusEffects(pokemonNumber, state.status);
    });
}

/**
 * Update health bar
 */
function updateHealthBar(pokemonNumber, percentage) {
    const healthBar = document.getElementById(`healthBar${pokemonNumber}`);
    healthBar.style.width = percentage + '%';
    
    // Change color based on health
    if (percentage <= 25) {
        healthBar.className = 'health-fill low';
    } else if (percentage <= 50) {
        healthBar.className = 'health-fill medium';
    } else {
        healthBar.className = 'health-fill';
    }
}

/**
 * Update status effects display
 */
function updateStatusEffects(pokemonNumber, status) {
    const statusDiv = document.getElementById(`statusEffects${pokemonNumber}`);
    statusDiv.innerHTML = '';
    
    if (status && status.condition !== 'none') {
        const badge = document.createElement('span');
        badge.className = 'status-badge';
        badge.textContent = status.condition.toUpperCase();
        statusDiv.appendChild(badge);
    }
}

/**
 * Get CSS class for log entry type
 */
function getLogClass(event) {
    switch (event.type) {
        case 'move_use':
            return 'log-move';
        case 'damage':
            return 'log-damage';
        case 'effectiveness':
            if (event.message.includes('super effective')) {
                return 'log-effectiveness super-effective';
            } else if (event.message.includes('not very effective')) {
                return 'log-effectiveness not-very-effective';
            }
            return 'log-effectiveness';
        case 'critical':
            return 'log-critical';
        case 'faint':
            return 'log-faint';
        default:
            return '';
    }
}

/**
 * Show battle results
 */
function showBattleResults(battleResult) {
    // Hide battle arena
    document.getElementById('battleArena').style.display = 'none';
    
    // Show results screen
    const resultsScreen = document.getElementById('resultsScreen');
    resultsScreen.style.display = 'block';
    
    // Set winner announcement
    const winnerText = document.getElementById('winnerAnnouncement');
    if (battleResult.winner !== 'Draw') {
        winnerText.textContent = `🎉 ${battleResult.winner} wins! 🎉`;
    } else {
        winnerText.textContent = '🤝 It\'s a draw! 🤝';
    }
    
    // Show battle summary
    const summaryStats = document.getElementById('summaryStats');
    summaryStats.innerHTML = `
        <p><strong>Duration:</strong> ${battleResult.total_turns} turns</p>
        <p><strong>Winner:</strong> ${battleResult.winner}</p>
        <p><strong>Final HP:</strong></p>
        <ul>
            <li>${battleResult.participants.pokemon1.name}: ${battleResult.participants.pokemon1.final_hp.current}/${battleResult.participants.pokemon1.final_hp.max}</li>
            <li>${battleResult.participants.pokemon2.name}: ${battleResult.participants.pokemon2.final_hp.current}/${battleResult.participants.pokemon2.final_hp.max}</li>
        </ul>
    `;
    
    battleState.battleInProgress = false;
}

/**
 * Go back to battle setup
 */
function backToSetup() {
    // Hide all screens
    document.getElementById('battleArena').style.display = 'none';
    document.getElementById('resultsScreen').style.display = 'none';
    
    // Show setup screen
    document.getElementById('battleSetup').style.display = 'block';
    
    // Reset battle state
    battleState.battleInProgress = false;
    battleState.currentBattle = null;
}

/**
 * Start a new battle (reset everything)
 */
function newBattle() {
    backToSetup();
    resetBattle();
}

/**
 * Reset battle configuration
 */
function resetBattle() {
    // Clear Pokemon data
    battleState.pokemon1 = null;
    battleState.pokemon2 = null;
    battleState.pokemon1Moves = [];
    battleState.pokemon2Moves = [];
    
    // Reset form inputs
    document.getElementById('pokemon1Name').value = '';
    document.getElementById('pokemon2Name').value = '';
    document.getElementById('pokemon1Level').value = 50;
    document.getElementById('pokemon2Level').value = 50;
    document.getElementById('pokemon1LevelValue').textContent = '50';
    document.getElementById('pokemon2LevelValue').textContent = '50';
    
    // Reset Pokemon previews
    for (let i = 1; i <= 2; i++) {
        document.getElementById(`pokemon${i}Sprite`).src = '/static/placeholder.png';
        document.getElementById(`pokemon${i}Info`).innerHTML = `
            <div class="pokemon-name">Select a Pokémon</div>
            <div class="pokemon-types"></div>
            <div class="pokemon-stats"></div>
        `;
        
        // Clear move selects
        for (let j = 1; j <= 4; j++) {
            const select = document.getElementById(`pokemon${i}Move${j}`);
            select.innerHTML = '<option value="">Select Move</option>';
            document.getElementById(`pokemon${i}Move${j}Info`).innerHTML = '';
        }
    }
    
    // Reset validation results
    document.getElementById('validationResults').style.display = 'none';
    document.getElementById('battleBtn').disabled = true;
    
    showSuccess('Battle configuration reset!');
}

/**
 * Utility functions
 */
function showLoading(message) {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showError(message) {
    document.getElementById('errorText').textContent = message;
    document.getElementById('errorMessage').style.display = 'flex';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

function showSuccess(message) {
    // Simple success notification (could be enhanced with a toast)
    console.log('Success:', message);
    
    // Could add a toast notification here
    const toast = document.createElement('div');
    toast.className = 'success-toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-color);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1002;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .attack-animation {
        animation: attack 0.5s ease-in-out;
    }
    
    @keyframes attack {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(10px); }
        75% { transform: translateX(-5px); }
    }
`;
document.head.appendChild(style);