const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const AIPlayer = require('./ai_logic');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.static(path.join(__dirname, 'public')));

const rooms = new Map();
const waitingPlayers = [];

const SPIRITS = {
    AMULET: 'AMULET', MIRROR: 'MIRROR', REMOTE_CONTROL: 'REMOTE_CONTROL',
    ERASER: 'ERASER', GLOVES: 'GLOVES', GREEN_POTION: 'GREEN_POTION',
    CREATION: 'CREATION', MUSHROOM: 'MUSHROOM', WHITE_POTION: 'WHITE_POTION',
    SHUFFLER: 'SHUFFLER', MAGNIFYING_GLASS: 'MAGNIFYING_GLASS', RED_POTION: 'RED_POTION',
    HANDCUFFS: 'HANDCUFFS', TELEPHONE: 'TELEPHONE', PILLOW: 'PILLOW',
    CONTRACT: 'CONTRACT', RADIO: 'RADIO'
};

const HIDDEN_SPIRITS = ['AMULET', 'MIRROR'];

function generateRoomId() {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
}

wss.on('connection', (ws) => {
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            handleMessage(ws, data);
        } catch (error) {
            console.error('消息解析错误:', error);
        }
    });

    ws.on('close', () => handleDisconnect(ws));
});

function handleMessage(ws, data) {
    switch (data.type) {
        case 'create_room': createRoom(ws, data); break;
        case 'create_ai_room': createAIRoom(ws, data); break;
        case 'join_room': joinRoom(ws, data); break;
        case 'quick_match': quickMatch(ws); break;
        case 'game_action': handleGameAction(ws, data); break;
        case 'leave_room': leaveRoom(ws); break;
    }
}

function createRoom(ws, data) {
    const roomId = generateRoomId();
    const room = {
        id: roomId,
        players: [{ ws, name: data.playerName, ready: false, isAI: false }],
        gameState: null,
        ai: null
    };
    rooms.set(roomId, room);
    ws.roomId = roomId;
    ws.playerIndex = 0;
    ws.send(JSON.stringify({ type: 'room_created', roomId, playerIndex: 0 }));
}

function createAIRoom(ws, data) {
    const roomId = generateRoomId();
    const aiDifficulty = data.difficulty || 'expert';
    const room = {
        id: roomId,
        players: [
            { ws, name: data.playerName, ready: true, isAI: false },
            { ws: null, name: `AI (${aiDifficulty})`, ready: true, isAI: true }
        ],
        gameState: null,
        ai: new AIPlayer(aiDifficulty)
    };
    rooms.set(roomId, room);
    ws.roomId = roomId;
    ws.playerIndex = 0;

    startGame(room);
}

function joinRoom(ws, data) {
    const room = rooms.get(data.roomId);
    if (!room) return ws.send(JSON.stringify({ type: 'error', message: '房间不存在' }));
    if (room.players.length >= 2) return ws.send(JSON.stringify({ type: 'error', message: '房间已满' }));

    room.players.push({ ws, name: data.playerName, ready: false, isAI: false });
    ws.roomId = data.roomId;
    ws.playerIndex = 1;

    room.players.forEach((p, i) => {
        if (!p.isAI) p.ws.send(JSON.stringify({ type: 'player_joined', playerIndex: i }));
    });
    startGame(room);
}

function quickMatch(ws) {
    if (waitingPlayers.length > 0) {
        const opponent = waitingPlayers.shift();
        if (opponent.ws.readyState !== WebSocket.OPEN) {
            quickMatch(ws);
            return;
        }
        const roomId = generateRoomId();
        const room = {
            id: roomId,
            players: [
                { ws: opponent.ws, name: opponent.name, ready: true, isAI: false },
                { ws, name: ws.playerName, ready: true, isAI: false }
            ],
            gameState: null,
            ai: null
        };
        rooms.set(roomId, room);
        opponent.ws.roomId = roomId;
        opponent.ws.playerIndex = 0;
        ws.roomId = roomId;
        ws.playerIndex = 1;
        startGame(room);
    } else {
        waitingPlayers.push({ ws, name: ws.playerName });
        ws.send(JSON.stringify({ type: 'waiting_for_opponent' }));
    }
}

function startGame(room) {
    const gameState = initializeGameState(room.players.map(p => p.name));
    room.gameState = gameState;

    // 添加牌堆组成信息到日志
    const composition = getDeckComposition(gameState.fateDeck);
    const compositionText = formatDeckComposition(composition);
    addLog(gameState, `📋 命运牌堆组成 (共${gameState.fateDeck.length}张): ${compositionText}`);
    addLog(gameState, `🎲 ${gameState.players[gameState.currentPlayer].name} 先手，${gameState.players[1 - gameState.currentPlayer].name} 后手获得额外灵物`);

    broadcastGameState(room);

    // 如果是 AI 局且 AI 先手（虽然目前逻辑是玩家0先手，但为了通用性）
    if (room.players[gameState.currentPlayer].isAI) {
        setTimeout(() => processAITurn(room), 1000);
    }
}

function initializeGameState(playerNames) {
    const spiritDeck = [];
    Object.keys(SPIRITS).forEach(type => spiritDeck.push(type, type));
    shuffle(spiritDeck);

    const players = playerNames.map(name => ({
        name, hp: 4, maxHp: 5, spirits: [],
        status: {
            amuletTurns: 0, isMirrored: false, isHandcuffed: false,
            pillowImmunity: 0, skipNextTurn: false, hasContract: false,
            lastStand: false, redPotionBonus: 0, remoteControlActive: false,
            mushroomEffect: false, shufflerEffect: false
        }
    }));

    // 随机决定先手玩家
    const firstPlayer = Math.floor(Math.random() * 2);
    const secondPlayer = 1 - firstPlayer;

    // 先手2个灵物，后手3个灵物
    for (let i = 0; i < 2; i++) drawSpirit(players[firstPlayer], spiritDeck);
    for (let i = 0; i < 3; i++) drawSpirit(players[secondPlayer], spiritDeck);

    return {
        players,
        spiritDeck,
        fateDeck: createFateDeck(),
        currentPlayer: firstPlayer,
        gameOver: false,
        winner: null,
        extraTurnPlayer: null,
        logs: [],
        lastSpiritUsedByPlayer: [null, null]  // 添加连续使用限制跟踪
    };
}

function createFateDeck() {
    const cards = ['DIVINE_PUNISHMENT', 'DIVINE_BOON', 'THE_VOID', 'REINCARNATION', 'BACKLASH'];
    const deck = [];
    const size = Math.floor(Math.random() * 6) + 5;
    for (let i = 0; i < size; i++) deck.push(cards[Math.floor(Math.random() * cards.length)]);
    return deck;
}

function getDeckComposition(deck) {
    const composition = {};
    deck.forEach(card => {
        composition[card] = (composition[card] || 0) + 1;
    });
    return composition;
}

function formatDeckComposition(composition) {
    const names = {
        'DIVINE_PUNISHMENT': '天罚',
        'DIVINE_BOON': '恩赐',
        'THE_VOID': '虚无',
        'REINCARNATION': '轮回',
        'BACKLASH': '反噬'
    };
    const parts = [];
    for (const [card, count] of Object.entries(composition)) {
        parts.push(`${names[card]}×${count}`);
    }
    return parts.join(', ');
}

function drawSpirit(player, deck) {
    if (deck.length === 0) {
        Object.keys(SPIRITS).forEach(type => deck.push(type, type));
        shuffle(deck);
    }
    if (player.spirits.length < 5) player.spirits.push(deck.pop());
}

function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function handleGameAction(ws, data) {
    // 兼容 AI 调用（ws 可能为 null 或模拟对象）
    const roomId = ws.roomId || ws.id;
    const room = rooms.get(roomId);
    if (!room || !room.gameState) return;
    const gs = room.gameState;

    if (gs.gameOver) return;

    // 验证回合
    const playerIndex = ws.playerIndex !== undefined ? ws.playerIndex : ws.index;
    if (gs.currentPlayer !== playerIndex) {
        if (ws.send) ws.send(JSON.stringify({ type: 'error', message: '不是你的回合' }));
        return;
    }

    switch (data.action) {
        case 'use_spirit':
            handleUseSpirit(room, playerIndex, data);
            break;
        case 'use_fate_card':
            handleUseFateCard(room, playerIndex, data.target);
            break;
    }
}

function processAITurn(room) {
    if (!room.ai || room.gameState.gameOver) return;
    const gs = room.gameState;
    const aiIndex = room.players.findIndex(p => p.isAI);

    if (gs.currentPlayer !== aiIndex) return;

    const action = room.ai.decideAction(gs, aiIndex);

    // 模拟 AI 操作
    const mockWs = { roomId: room.id, playerIndex: aiIndex, id: room.id }; // id for fallback
    handleGameAction(mockWs, action);

    // 如果 AI 只是用了灵物，它可能还可以继续行动
    if (action.action === 'use_spirit' && !gs.gameOver && gs.currentPlayer === aiIndex) {
        setTimeout(() => processAITurn(room), 1500);
    }
}

function handleUseSpirit(room, playerIndex, data) {
    const gs = room.gameState;
    const player = gs.players[playerIndex];
    const opponent = gs.players[1 - playerIndex];
    const spiritIndex = data.spiritIndex;
    const spirit = player.spirits[spiritIndex];

    if (player.status.isHandcuffed) return;

    // 检查连续使用限制
    if ((spirit === 'REMOTE_CONTROL' || spirit === 'HANDCUFFS') &&
        gs.lastSpiritUsedByPlayer[playerIndex] === spirit) {
        addLog(gs, `${spirit === 'REMOTE_CONTROL' ? '遥控器' : '手铐'}无法连续使用！`);
        broadcastGameState(room);
        return;
    }

    player.spirits.splice(spiritIndex, 1);

    // 记录使用的灵物
    gs.lastSpiritUsedByPlayer[playerIndex] = spirit;

    if (HIDDEN_SPIRITS.includes(spirit)) {
        addLog(gs, `${player.name} 使用了 神秘护符`);
    } else {
        addLog(gs, `${player.name} 使用了 ${getSpiritName(spirit)}`);
    }

    switch (spirit) {
        case 'AMULET':
            player.status.amuletTurns = 2;
            break;
        case 'MIRROR':
            player.status.isMirrored = true;
            break;
        case 'GREEN_POTION':
            player.hp = Math.min(player.maxHp, player.hp + 1);
            addLog(gs, `${player.name} 恢复了1点生命`);
            break;
        case 'RED_POTION':
            player.status.redPotionBonus += 1;
            addLog(gs, `${player.name} 下次伤害+1`);
            break;
        case 'ERASER':
            if (opponent.spirits.length > 0) {
                const count = Math.min(2, opponent.spirits.length);
                const removedNames = [];
                for (let i = 0; i < count; i++) {
                    const idx = Math.floor(Math.random() * opponent.spirits.length);
                    const removed = opponent.spirits.splice(idx, 1)[0];
                    removedNames.push(getSpiritName(removed));
                }
                addLog(gs, `移除了对手的: ${removedNames.join(', ')}`);
            }
            break;
        case 'CREATION':
            drawSpirit(player, gs.spiritDeck);
            drawSpirit(player, gs.spiritDeck);
            addLog(gs, `${player.name} 获得了2个灵物`);
            break;
        case 'MUSHROOM':
            player.status.mushroomEffect = true;
            addLog(gs, '下一次抽牌将变幻莫测');
            break;
        case 'WHITE_POTION':
            const r = Math.random();
            if (r < 0.49) { player.hp = Math.min(player.maxHp, player.hp + 1); addLog(gs, '白药水: 恢复了1点生命'); }
            else if (r < 0.98) { takeDamage(player, 1, gs); addLog(gs, '白药水: 失去了1点生命'); }
            else if (r < 0.99) { player.hp = Math.min(player.maxHp, player.hp + 2); addLog(gs, '白药水: 大恢复！+2生命'); }
            else { takeDamage(player, 2, gs); addLog(gs, '白药水: 大失败！-2生命'); }
            break;
        case 'SHUFFLER':
            player.status.shufflerEffect = true;
            addLog(gs, '牌堆即将发生变化');
            break;
        case 'MAGNIFYING_GLASS':
            if (gs.fateDeck.length === 0) gs.fateDeck = createFateDeck();
            const nextCard = gs.fateDeck[0];
            sendPrivateInfo(room, playerIndex, `下一张牌是: ${getFateCardName(nextCard)}`);
            // AI 记牌
            if (room.ai && room.players[playerIndex].isAI) room.ai.knownNextFateCard = nextCard;
            break;
        case 'HANDCUFFS':
            if (opponent.status.pillowImmunity > 0) {
                addLog(gs, '对手免疫手铐效果');
            } else {
                opponent.status.isHandcuffed = true;
                drawSpirit(opponent, gs.spiritDeck);
                addLog(gs, '对手下回合无法使用灵物');
            }
            break;
        case 'TELEPHONE':
            if (gs.fateDeck.length === 0) gs.fateDeck = createFateDeck();
            const pos = Math.min(Math.max(1, parseInt(data.param) || 1), gs.fateDeck.length);
            const cardAtPos = gs.fateDeck[pos - 1];
            sendPrivateInfo(room, playerIndex, `第 ${pos} 张牌是: ${getFateCardName(cardAtPos)}`);
            break;
        case 'PILLOW':
            drawSpirit(player, gs.spiritDeck);
            drawSpirit(player, gs.spiritDeck);
            drawSpirit(player, gs.spiritDeck);
            player.status.skipNextTurn = true;
            player.status.pillowImmunity = 3;
            addLog(gs, '获得3个灵物，跳过下回合');
            break;
        case 'CONTRACT':
            takeDamage(player, 2, gs);
            player.status.hasContract = true;
            addLog(gs, '签订契约，失去2点生命');
            break;
        case 'REMOTE_CONTROL':
            player.status.remoteControlActive = true;
            addLog(gs, '遥控器已激活');
            break;
        case 'GLOVES':
            // 逻辑修正：必须指定 targetSpiritIndex，否则随机（防错）
            let stealIdx = data.targetSpiritIndex;
            if (typeof stealIdx !== 'number' || !opponent.spirits[stealIdx]) {
                if (opponent.spirits.length > 0) stealIdx = Math.floor(Math.random() * opponent.spirits.length);
                else stealIdx = -1;
            }

            if (stealIdx !== -1) {
                const stolen = opponent.spirits.splice(stealIdx, 1)[0];
                if (player.spirits.length < 5) player.spirits.push(stolen);
                const stolenName = getSpiritName(stolen);
                addLog(gs, `${player.name} 偷走了一个灵物`);
                sendPrivateInfo(room, playerIndex, `你偷到了: ${stolenName}`);
            }
            break;
        case 'RADIO':
            // 逻辑修正：必须指定 targetSpiritIndex，否则无效
            if (typeof data.targetSpiritIndex === 'number' && opponent.spirits[data.targetSpiritIndex]) {
                const forcedSpirit = opponent.spirits[data.targetSpiritIndex];
                addLog(gs, `强制对手使用了 ${getSpiritName(forcedSpirit)}`);
                opponent.spirits.splice(data.targetSpiritIndex, 1);
                // 强制使用时，决策者是 player (发起者)
                applyForcedSpiritEffect(room, 1 - playerIndex, forcedSpirit, playerIndex);
            }
            break;
    }

    broadcastGameState(room);
}

function applyForcedSpiritEffect(room, userIndex, spirit, decisionMakerIndex) {
    const gs = room.gameState;
    const player = gs.players[userIndex]; // 使用者（被强制的一方）
    // const decisionMaker = gs.players[decisionMakerIndex]; // 决策者（发起强制的一方）

    // 简化处理：对于需要参数的灵物，这里暂时随机或默认，
    // 因为前端交互太复杂（需要发起者在强制使用时就填好参数，或者二次交互）
    // 我们的 AI 逻辑里已经尽量填了参数，但真人玩家的 RADIO 交互目前只选了灵物
    // 为了体验，我们让随机性接管复杂参数，或者默认值

    switch (spirit) {
        case 'GREEN_POTION': player.hp = Math.min(player.maxHp, player.hp + 1); addLog(gs, `${player.name} 恢复了1点生命`); break;
        case 'RED_POTION': player.status.redPotionBonus += 1; addLog(gs, `${player.name} 下次伤害+1`); break;
        case 'CREATION': drawSpirit(player, gs.spiritDeck); drawSpirit(player, gs.spiritDeck); addLog(gs, `${player.name} 获得了2个灵物`); break;
        case 'WHITE_POTION':
            const r = Math.random();
            if (r < 0.49) { player.hp = Math.min(player.maxHp, player.hp + 1); addLog(gs, '白药水: 恢复了1点生命'); }
            else if (r < 0.98) { takeDamage(player, 1, gs); addLog(gs, '白药水: 失去了1点生命'); }
            else if (r < 0.99) { player.hp = Math.min(player.maxHp, player.hp + 2); addLog(gs, '白药水: 大恢复！+2生命'); }
            else { takeDamage(player, 2, gs); addLog(gs, '白药水: 大失败！-2生命'); }
            break;
        case 'CONTRACT': takeDamage(player, 2, gs); player.status.hasContract = true; addLog(gs, '签订契约'); break;
        case 'PILLOW':
            drawSpirit(player, gs.spiritDeck); drawSpirit(player, gs.spiritDeck); drawSpirit(player, gs.spiritDeck);
            player.status.skipNextTurn = true; player.status.pillowImmunity = 3;
            addLog(gs, '获得3个灵物，跳过下回合');
            break;
        case 'AMULET': player.status.amuletTurns = 2; addLog(gs, '使用了神秘护符'); break;
        case 'MIRROR': player.status.isMirrored = true; addLog(gs, '使用了神秘护符'); break;
        case 'ERASER':
            // 这里的 opponent 是相对于 user (被强制者) 的对手，也就是 decisionMaker
            const target = gs.players[decisionMakerIndex];
            if (target.spirits.length > 0) {
                const count = Math.min(2, target.spirits.length);
                for (let i = 0; i < count; i++) {
                    const idx = Math.floor(Math.random() * target.spirits.length);
                    target.spirits.splice(idx, 1);
                }
                addLog(gs, `移除了对手 ${count} 个灵物`);
            }
            break;
        // 复杂灵物降级处理
        case 'GLOVES': addLog(gs, '手套滑落了... (强制使用失效)'); break;
        case 'TELEPHONE': addLog(gs, '电话占线... (强制使用失效)'); break;
        case 'RADIO': addLog(gs, '信号干扰... (强制使用失效)'); break;
    }
}

function handleUseFateCard(room, playerIndex, targetType) {
    const gs = room.gameState;
    const player = gs.players[playerIndex];

    let card = drawFateCard(gs, player);
    const targetIndex = targetType === 'self' ? playerIndex : 1 - playerIndex;
    applyFateCardEffect(gs, card, playerIndex, targetIndex);

    // AI 记牌更新
    if (room.ai) room.ai.knownNextFateCard = null; // 牌被抽走了

    endTurn(room);
}

function drawFateCard(gs, player) {
    if (gs.fateDeck.length === 0) gs.fateDeck = createFateDeck();

    if (player.status.shufflerEffect) {
        player.status.shufflerEffect = false;
        if (gs.fateDeck.length > 1) {
            const idx = Math.floor(Math.random() * (gs.fateDeck.length - 1)) + 1;
            [gs.fateDeck[0], gs.fateDeck[idx]] = [gs.fateDeck[idx], gs.fateDeck[0]];
            addLog(gs, '洗牌器触发，牌堆已变动');
        }
    }

    if (player.status.mushroomEffect) {
        player.status.mushroomEffect = false;
        const newCard = createFateDeck()[0];
        gs.fateDeck.shift();
        addLog(gs, '蘑菇触发，卡牌已变形');
        return newCard;
    }

    return gs.fateDeck.shift();
}

function applyFateCardEffect(gs, card, userIndex, targetIndex) {
    let target = gs.players[targetIndex];
    const user = gs.players[userIndex];
    addLog(gs, `${user.name} 对 ${target.name} 使用了 ${getFateCardName(card)}`);

    let damageBonus = 0;
    if (target.status.isMirrored) {
        target.status.isMirrored = false;
        addLog(gs, '镜子反弹了效果！');
        target = user;
        damageBonus = 1;
    }

    switch (card) {
        case 'DIVINE_PUNISHMENT':
            takeDamage(target, 1 + user.status.redPotionBonus + damageBonus, gs);
            user.status.redPotionBonus = 0;
            break;
        case 'DIVINE_BOON':
            drawSpirit(target, gs.spiritDeck);
            addLog(gs, `${target.name} 获得了1个灵物`);
            break;
        case 'THE_VOID':
            if (target === user) {
                gs.extraTurnPlayer = gs.players.indexOf(target);
                addLog(gs, '虚无对己，获得额外回合');
            } else {
                addLog(gs, '虚无...什么都没发生');
            }
            break;
        case 'REINCARNATION':
            addLog(gs, '轮回触发，再次对自己使用');
            const nextCard = drawFateCard(gs, target);
            applyFateCardEffect(gs, nextCard, gs.players.indexOf(target), gs.players.indexOf(target));
            break;
        case 'BACKLASH':
            const dmg = takeDamage(target, 1 + user.status.redPotionBonus + damageBonus, gs);
            user.status.redPotionBonus = 0;
            if (dmg > 0) {
                gs.extraTurnPlayer = gs.players.indexOf(target);
                addLog(gs, '反噬触发，目标获得额外回合');
            }
            break;
    }
}

function takeDamage(player, amount, gs) {
    if (player.status.amuletTurns > 0) {
        if (amount > 1) {
            amount *= 2;
            player.status.amuletTurns = 0;
            addLog(gs, '护身符破碎！双倍伤害');
        } else {
            amount = 0;
            addLog(gs, '护身符抵挡了伤害');
        }
    }

    if (amount > 0) {
        player.hp -= amount;
        addLog(gs, `${player.name} 受到 ${amount} 点伤害`);
        for (let i = 0; i < amount * 2; i++) drawSpirit(player, gs.spiritDeck);
    }
    return amount;
}

function endTurn(room) {
    const gs = room.gameState;
    let currentPlayer = gs.players[gs.currentPlayer];

    if (currentPlayer.status.amuletTurns > 0) currentPlayer.status.amuletTurns--;
    if (currentPlayer.status.pillowImmunity > 0) currentPlayer.status.pillowImmunity--;

    if (currentPlayer.status.remoteControlActive) {
        currentPlayer.status.remoteControlActive = false;
        const opponent = gs.players[1 - gs.currentPlayer];
        addLog(gs, '遥控器生效！对手被迫对自己使用卡牌');
        const card = drawFateCard(gs, opponent);
        applyFateCardEffect(gs, card, 1 - gs.currentPlayer, 1 - gs.currentPlayer);
    }

    checkGameOver(gs);
    if (gs.gameOver) {
        broadcastGameState(room);
        return;
    }

    if (gs.extraTurnPlayer !== null) {
        gs.currentPlayer = gs.extraTurnPlayer;
        gs.extraTurnPlayer = null;
    } else {
        gs.currentPlayer = 1 - gs.currentPlayer;
        // 切换玩家时，清除上一个玩家的连续使用记录
        // 这样玩家在下一轮可以再次使用遥控器/手铐
        gs.lastSpiritUsedByPlayer[1 - gs.currentPlayer] = null;
    }

    const nextPlayer = gs.players[gs.currentPlayer];
    if (nextPlayer.status.skipNextTurn) {
        nextPlayer.status.skipNextTurn = false;
        addLog(gs, `${nextPlayer.name} 跳过回合`);
        endTurn(room);
        return;
    }

    nextPlayer.status.isHandcuffed = false;

    broadcastGameState(room);

    // 如果下一位是 AI，触发 AI 回合
    if (room.players[gs.currentPlayer].isAI) {
        setTimeout(() => processAITurn(room), 1000);
    }
}

function checkGameOver(gs) {
    gs.players.forEach((p, i) => {
        if (p.hp <= 0) {
            if (p.status.hasContract && !p.status.lastStand) {
                p.status.lastStand = true;
                p.hp = 1;
                drawSpirit(p, gs.spiritDeck);
                drawSpirit(p, gs.spiritDeck);
                drawSpirit(p, gs.spiritDeck);
                gs.extraTurnPlayer = i;
                addLog(gs, `${p.name} 契约生效！最终回合`);
            } else {
                gs.gameOver = true;
                gs.winner = 1 - i;
            }
        }

        // 检查最终回合是否已用完但未获胜
        if (p.status.lastStand && gs.extraTurnPlayer !== i && gs.currentPlayer !== i) {
            // 最终回合已结束，但玩家仍未获胜
            addLog(gs, `${p.name} 的最终回合已结束，契约失效！`);
            gs.gameOver = true;
            gs.winner = 1 - i;
        }
    });
}

function broadcastGameState(room) {
    room.players.forEach((p, i) => {
        if (p.isAI) return; // 不发给 AI
        const view = JSON.parse(JSON.stringify(room.gameState));
        const opponentIdx = 1 - i;
        view.players[opponentIdx].spirits = view.players[opponentIdx].spirits.map(s =>
            HIDDEN_SPIRITS.includes(s) ? 'HIDDEN' : s
        );
        view.playerIndex = i;
        p.ws.send(JSON.stringify({ type: 'game_update', gameState: view }));
    });
}

function sendPrivateInfo(room, playerIndex, msg) {
    const p = room.players[playerIndex];
    if (!p.isAI && p.ws) {
        p.ws.send(JSON.stringify({ type: 'private_info', message: msg }));
    }
}

function addLog(gs, msg) {
    gs.logs.unshift(msg);
    if (gs.logs.length > 20) gs.logs.pop();
}

function getSpiritName(code) {
    const names = {
        AMULET: '护身符', MIRROR: '镜子', REMOTE_CONTROL: '遥控器', ERASER: '橡皮擦',
        GLOVES: '手套', GREEN_POTION: '绿药水', CREATION: '无中生有', MUSHROOM: '蘑菇',
        WHITE_POTION: '白药水', SHUFFLER: '洗牌器', MAGNIFYING_GLASS: '放大镜',
        RED_POTION: '红药水', HANDCUFFS: '手铐', TELEPHONE: '电话', PILLOW: '枕头',
        CONTRACT: '契约书', RADIO: '无线电'
    };
    return names[code] || code;
}

function getFateCardName(code) {
    const names = {
        DIVINE_PUNISHMENT: '天罚', DIVINE_BOON: '恩赐', THE_VOID: '虚无',
        REINCARNATION: '轮回', BACKLASH: '反噬'
    };
    return names[code] || code;
}

function handleDisconnect(ws) {
    if (ws.roomId) {
        const room = rooms.get(ws.roomId);
        if (room) {
            room.players.forEach(p => {
                if (p.ws !== ws && p.ws && p.ws.readyState === WebSocket.OPEN) {
                    p.ws.send(JSON.stringify({ type: 'opponent_disconnected' }));
                }
            });
            rooms.delete(ws.roomId);
        }
    }
    const idx = waitingPlayers.findIndex(p => p.ws === ws);
    if (idx !== -1) waitingPlayers.splice(idx, 1);
}

function leaveRoom(ws) { handleDisconnect(ws); }

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
