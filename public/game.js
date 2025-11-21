// 游戏常量
const SPIRIT_NAMES = {
    'AMULET': '护身符', 'MIRROR': '镜子', 'REMOTE_CONTROL': '遥控器',
    'ERASER': '橡皮擦', 'GLOVES': '手套', 'GREEN_POTION': '绿药水',
    'CREATION': '无中生有', 'MUSHROOM': '蘑菇', 'WHITE_POTION': '白药水',
    'SHUFFLER': '洗牌器', 'MAGNIFYING_GLASS': '放大镜', 'RED_POTION': '红药水',
    'HANDCUFFS': '手铐', 'TELEPHONE': '电话', 'PILLOW': '枕头',
    'CONTRACT': '契约书', 'RADIO': '无线电', 'HIDDEN': '神秘护符'
};

// 游戏状态
let gameMode = null;
let ws = null;
let gameState = null;
let waitingForTarget = false;
let waitingForSpiritTarget = false;
let activeSpiritIndex = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});

// 复制房间号功能
function copyRoomId() {
    const roomId = document.getElementById('displayRoomId').textContent;
    if (!roomId || roomId === '------') return;

    navigator.clipboard.writeText(roomId).then(() => {
        const btn = document.querySelector('.room-id-display .btn-icon');
        const originalText = btn.textContent;
        btn.textContent = '✅';
        setTimeout(() => btn.textContent = originalText, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制');
    });
}

// 屏幕切换
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}
function showMainMenu() { showScreen('mainMenu'); if (ws) { ws.close(); ws = null; } }
function showModeSelection() { showScreen('modeSelection'); }
function showAIDifficulty() { showScreen('aiDifficulty'); }
function showMultiplayerOptions() { showScreen('multiplayerOptions'); }
function showJoinRoom() { showScreen('joinRoomScreen'); }
function showRules() { showScreen('rulesScreen'); }
function showStats() { updateStatsDisplay(); showScreen('statsScreen'); }

// AI 游戏启动
function startAIGame(difficulty) {
    const name = prompt('请输入你的名字:', '玩家') || '玩家';
    connectWebSocket(() => {
        ws.send(JSON.stringify({
            type: 'create_ai_room',
            playerName: name,
            difficulty: difficulty
        }));
    });
}

// WebSocket Logic
function connectWebSocket(onOpenCallback) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        if (onOpenCallback) onOpenCallback();
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}`);

    ws.onopen = () => {
        if (onOpenCallback) onOpenCallback();
    };

    ws.onmessage = (e) => handleWebSocketMessage(JSON.parse(e.data));
    ws.onerror = () => alert('连接服务器失败，请检查服务器是否启动');
    ws.onclose = () => console.log('连接关闭');
}

function createRoom() {
    const name = prompt('请输入名字:', '玩家1') || '玩家1';
    connectWebSocket(() => {
        ws.send(JSON.stringify({ type: 'create_room', playerName: name }));
    });
}

function joinRoomWithId() {
    const roomId = document.getElementById('roomIdInput').value.trim().toUpperCase();
    const name = document.getElementById('playerNameInput').value.trim() || '玩家2';
    if (!roomId) return alert('请输入房间号');
    connectWebSocket(() => {
        ws.send(JSON.stringify({ type: 'join_room', roomId, playerName: name }));
    });
}

function quickMatch() {
    const name = prompt('请输入名字:', '玩家') || '玩家';
    connectWebSocket(() => {
        ws.playerName = name;
        ws.send(JSON.stringify({ type: 'quick_match', playerName: name }));
    });
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'room_created':
            if (!data.isAI) {
                document.getElementById('displayRoomId').textContent = data.roomId;
                showScreen('waitingRoom');
            }
            break;
        case 'waiting_for_opponent':
            document.getElementById('displayRoomId').textContent = '匹配中...';
            showScreen('waitingRoom');
            break;
        case 'game_start':
        case 'game_update':
            gameMode = 'online';
            gameState = data.gameState;
            showScreen('gameScreen');
            updateGameDisplay();
            checkGameOver();
            break;
        case 'private_info':
            alert(`🔍 私密信息: ${data.message}`);
            break;
        case 'opponent_disconnected':
            alert('对手已断开连接');
            showMainMenu();
            break;
        case 'error':
            alert(data.message);
            break;
    }
}

// Display Logic
function updateGameDisplay() {
    if (!gameState) return;
    const p = gameState.players[gameState.playerIndex || 0];
    const op = gameState.players[1 - (gameState.playerIndex || 0)];

    document.getElementById('playerName').textContent = p.name;
    updateHpBar('playerHpBar', p.hp, p.maxHp);

    document.getElementById('opponentName').textContent = op.name;
    updateHpBar('opponentHpBar', op.hp, op.maxHp);

    updateSpirits('playerSpirits', p.spirits, true);
    updateSpirits('opponentSpirits', op.spirits, false);

    updateStatus('playerStatus', p.status);
    updateStatus('opponentStatus', op.status);

    document.getElementById('fateDeckCount').textContent = gameState.fateDeck.length;

    const isMyTurn = gameState.currentPlayer === (gameState.playerIndex || 0);
    const ind = document.getElementById('turnIndicator');
    ind.textContent = isMyTurn ? '你的回合' : '对手回合';
    ind.className = isMyTurn ? 'turn-badge my-turn' : 'turn-badge';

    // 高亮当前回合玩家区域
    document.getElementById('playerArea').classList.toggle('active-turn', isMyTurn);
    document.getElementById('opponentArea').classList.toggle('active-turn', !isMyTurn);

    const logContainer = document.getElementById('gameLog');
    logContainer.innerHTML = '';
    (gameState.logs || []).forEach(msg => {
        const div = document.createElement('div');
        div.className = 'log-entry';
        div.textContent = msg;
        logContainer.appendChild(div);
    });
}

function updateHpBar(id, current, max) {
    const container = document.getElementById(id);
    container.innerHTML = '';
    for (let i = 0; i < max; i++) {
        const heart = document.createElement('span');
        heart.className = i < current ? 'hp-heart active' : 'hp-heart';
        heart.textContent = '♥';
        container.appendChild(heart);
    }
}

function updateSpirits(id, spirits, isSelf) {
    const container = document.getElementById(id);
    container.innerHTML = '';
    spirits.forEach((s, i) => {
        const card = document.createElement('div');
        card.className = 'spirit-card';
        if (isSelf && gameState.currentPlayer === (gameState.playerIndex || 0)) card.classList.add('clickable');

        if (!isSelf && waitingForSpiritTarget) {
            card.classList.add('target-candidate');
            card.onclick = () => selectSpiritTarget(i);
        } else if (isSelf) {
            card.onclick = () => useSpirit(i);
        }

        card.innerHTML = `<div class="spirit-icon">${getSpiritIcon(s)}</div><div class="spirit-name">${SPIRIT_NAMES[s] || s}</div>`;
        container.appendChild(card);
    });
}

function getSpiritIcon(s) {
    const icons = {
        'AMULET': '🛡️', 'MIRROR': '🪞', 'REMOTE_CONTROL': '📡', 'ERASER': '🧹',
        'GLOVES': '🧤', 'GREEN_POTION': '💚', 'CREATION': '✨', 'MUSHROOM': '🍄',
        'WHITE_POTION': '🤍', 'SHUFFLER': '🔀', 'MAGNIFYING_GLASS': '🔍',
        'RED_POTION': '❤️', 'HANDCUFFS': '⛓️', 'TELEPHONE': '📞', 'PILLOW': '🛏️',
        'CONTRACT': '📜', 'RADIO': '📻', 'HIDDEN': '❓'
    };
    return icons[s] || '❓';
}

function updateStatus(id, s) {
    const container = document.getElementById(id);
    container.innerHTML = '';
    const list = [];
    if (s.amuletTurns > 0) list.push(`护身符(${s.amuletTurns})`);
    if (s.isMirrored) list.push('镜子');
    if (s.isHandcuffed) list.push('手铐');
    if (s.pillowImmunity > 0) list.push(`免疫(${s.pillowImmunity})`);
    if (s.hasContract) list.push('契约');
    if (s.lastStand) list.push('背水一战');
    if (s.remoteControlActive) list.push('遥控');
    if (s.mushroomEffect) list.push('蘑菇');
    if (s.redPotionBonus > 0) list.push(`伤害+${s.redPotionBonus}`);

    list.forEach(t => {
        const b = document.createElement('div');
        b.className = 'status-badge';
        b.textContent = t;
        container.appendChild(b);
    });
}

// Actions
function useSpirit(index) {
    if (gameState.currentPlayer !== (gameState.playerIndex || 0)) return alert('不是你的回合');
    const p = gameState.players[gameState.playerIndex || 0];
    if (p.status.isHandcuffed) return alert('你被手铐束缚');

    const spirit = p.spirits[index];

    if (spirit === 'TELEPHONE') {
        const pos = prompt('你想查看第几张牌？(1-10)', '1');
        if (!pos) return;
        sendAction('use_spirit', { spiritIndex: index, param: parseInt(pos) });
    } else if (spirit === 'GLOVES' || spirit === 'RADIO') {
        activeSpiritIndex = index;
        waitingForSpiritTarget = true;
        alert('请点击选择对手的一个灵物');
        updateGameDisplay();
    } else {
        sendAction('use_spirit', { spiritIndex: index });
    }
}

function selectSpiritTarget(targetIndex) {
    if (!waitingForSpiritTarget) return;
    waitingForSpiritTarget = false;
    sendAction('use_spirit', { spiritIndex: activeSpiritIndex, targetSpiritIndex: targetIndex });
    activeSpiritIndex = null;
    updateGameDisplay();
}

function useFateCard() {
    if (gameState.currentPlayer !== (gameState.playerIndex || 0)) return alert('不是你的回合');
    waitingForTarget = true;
    document.getElementById('targetModal').classList.add('active');
}

function selectTarget(target) {
    document.getElementById('targetModal').classList.remove('active');
    if (!waitingForTarget) return;
    waitingForTarget = false;
    sendAction('use_fate_card', { target });
}

function sendAction(type, payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'game_action', action: type, ...payload }));
    }
}

function checkGameOver() {
    if (gameState.gameOver) {
        const winner = gameState.players[gameState.winner];
        const isWin = gameState.winner === (gameState.playerIndex || 0);
        document.getElementById('gameOverTitle').textContent = isWin ? '🎉 胜利！' : '💔 失败';
        document.getElementById('gameOverMessage').textContent = `${winner.name} 获胜！`;
        document.getElementById('gameOverModal').classList.add('active');

        if (isWin) stats.wins++; else stats.losses++;
        saveStats();
    }
}

function returnToMenu() {
    document.getElementById('gameOverModal').classList.remove('active');
    showMainMenu();
}

function leaveRoom() {
    if (ws) { ws.send(JSON.stringify({ type: 'leave_room' })); ws.close(); }
    showMainMenu();
}

let stats = { wins: 0, losses: 0 };
function loadStats() { const s = localStorage.getItem('stats'); if (s) stats = JSON.parse(s); }
function saveStats() { localStorage.setItem('stats', JSON.stringify(stats)); }
function updateStatsDisplay() {
    document.getElementById('winCount').textContent = stats.wins;
    document.getElementById('lossCount').textContent = stats.losses;
    const t = stats.wins + stats.losses;
    document.getElementById('winRate').textContent = t ? ((stats.wins / t) * 100).toFixed(1) + '%' : '0%';
}
