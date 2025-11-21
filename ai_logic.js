const SPIRITS = {
    AMULET: 'AMULET', MIRROR: 'MIRROR', REMOTE_CONTROL: 'REMOTE_CONTROL',
    ERASER: 'ERASER', GLOVES: 'GLOVES', GREEN_POTION: 'GREEN_POTION',
    CREATION: 'CREATION', MUSHROOM: 'MUSHROOM', WHITE_POTION: 'WHITE_POTION',
    SHUFFLER: 'SHUFFLER', MAGNIFYING_GLASS: 'MAGNIFYING_GLASS', RED_POTION: 'RED_POTION',
    HANDCUFFS: 'HANDCUFFS', TELEPHONE: 'TELEPHONE', PILLOW: 'PILLOW',
    CONTRACT: 'CONTRACT', RADIO: 'RADIO'
};

const HIDDEN_SPIRITS = ['AMULET', 'MIRROR'];
const MAX_SPIRITS = 5;

class AIPlayer {
    constructor(difficulty = 'expert') {
        this.difficulty = difficulty;
        this.knownNextFateCard = null;
        this.knownFateDeckComposition = {}; // For Hell AI
    }

    decideAction(gameState, myIndex) {
        const me = gameState.players[myIndex];
        const opponent = gameState.players[1 - myIndex];

        // 模拟思考时间
        // 在实际服务器中，我们直接返回决策，延时由调用者控制或前端动画处理

        // 1. 检查是否被手铐
        if (me.status.isHandcuffed) {
            return { action: 'use_fate_card', target: this.chooseFateCardTarget(gameState, myIndex) };
        }

        // 2. 评估灵物使用
        const bestSpirit = this.evaluateSpiritUse(gameState, myIndex);

        // 阈值判断：只有分数足够高才使用灵物
        if (bestSpirit && bestSpirit.score > 35) {
            // 构建 action 数据
            const actionData = {
                action: 'use_spirit',
                spiritIndex: bestSpirit.index
            };

            // 补充参数
            const spiritName = me.spirits[bestSpirit.index];
            if (spiritName === 'TELEPHONE') {
                actionData.param = Math.floor(Math.random() * gameState.fateDeck.length) + 1;
            } else if (spiritName === 'GLOVES') {
                actionData.targetSpiritIndex = this.chooseSpiritToSteal(opponent.spirits);
            } else if (spiritName === 'RADIO') {
                const forceTarget = this.chooseSpiritToForceUse(opponent.spirits, opponent);
                if (forceTarget !== null) {
                    actionData.targetSpiritIndex = forceTarget;
                } else {
                    // 如果没有好的强制目标，放弃使用无线电
                    return { action: 'use_fate_card', target: this.chooseFateCardTarget(gameState, myIndex) };
                }
            }

            return actionData;
        }

        // 3. 默认使用命运卡
        return { action: 'use_fate_card', target: this.chooseFateCardTarget(gameState, myIndex) };
    }

    evaluateSpiritUse(gameState, myIndex) {
        const me = gameState.players[myIndex];
        const opponent = gameState.players[1 - myIndex];
        const tendency = this.determineStrategicTendency(me, opponent);

        let bestIndex = -1;
        let highestScore = -Infinity;

        me.spirits.forEach((spirit, i) => {
            let score = 0;

            // 基础评分逻辑 (移植自 Python ExpertAIPlayer)
            if (spirit === 'GREEN_POTION') score += (me.maxHp - me.hp) * 40;
            else if (spirit === 'ERASER') score += opponent.spirits.length * 25;
            else if (spirit === 'GLOVES') {
                const stealableCount = opponent.spirits.filter(s => s !== 'GLOVES').length;
                if (stealableCount > 0 && me.spirits.length < MAX_SPIRITS) score += 35 + stealableCount * 5;
            }
            else if (spirit === 'CREATION') score += (MAX_SPIRITS - me.spirits.length) * 15;
            else if (spirit === 'MAGNIFYING_GLASS' && !this.knownNextFateCard) score += 80;
            else if (spirit === 'CONTRACT' && !me.status.hasContract) {
                if (me.hp <= 2) score += 150;
                else if (me.hp === 3) score += 50;
            }
            else if (spirit === 'WHITE_POTION') score += me.hp > 1 ? 15 : -200;
            else if (spirit === 'PILLOW' && me.spirits.length <= 2) score += 80 - opponent.hp * 5;
            else if (spirit === 'RADIO' && opponent.spirits.length > 0) score += 50;
            else if (HIDDEN_SPIRITS.includes(spirit)) {
                score += tendency === 'Defensive' ? 90 : 40;
            }
            else score += 30;

            // 配合透视
            if (this.knownNextFateCard && ['DIVINE_PUNISHMENT', 'BACKLASH'].includes(this.knownNextFateCard)) {
                if (spirit === 'RED_POTION') score += 120;
                if (spirit === 'MIRROR') score += 60;
            }

            // 策略倾向修正
            if (tendency === 'Aggressive') {
                if (['RED_POTION', 'ERASER', 'HANDCUFFS', 'REMOTE_CONTROL', 'RADIO'].includes(spirit)) score *= 1.5;
            }
            if (tendency === 'Defensive') {
                if (['AMULET', 'MIRROR', 'GREEN_POTION'].includes(spirit)) score *= 1.8;
            }

            // 避免连续使用遥控器/手铐
            if (['REMOTE_CONTROL', 'HANDCUFFS'].includes(spirit) &&
                gameState.lastSpiritUsedByPlayer &&
                gameState.lastSpiritUsedByPlayer[myIndex] === spirit) {
                score = -1000;
            }

            if (score > highestScore) {
                highestScore = score;
                bestIndex = i;
            }
        });

        return bestIndex !== -1 ? { index: bestIndex, score: highestScore } : null;
    }

    determineStrategicTendency(me, opponent) {
        if (me.hp <= 2) return 'Defensive';
        if (opponent.hp <= 2) return 'Aggressive';
        if (me.hp > opponent.hp) return 'Stable';
        return 'Stable';
    }

    chooseFateCardTarget(gameState, myIndex) {
        // 如果知道下一张是增益，对自己用；如果是减益，对对手用
        if (this.knownNextFateCard) {
            if (['THE_VOID', 'DIVINE_BOON'].includes(this.knownNextFateCard)) return 'self';
            return 'opponent';
        }
        // 默认逻辑
        return Math.random() < 0.9 ? 'opponent' : 'self';
    }

    chooseSpiritToSteal(opponentSpirits) {
        const priority = ["CONTRACT", "RED_POTION", "PILLOW", "ERASER", "REMOTE_CONTROL", "RADIO", "MIRROR", "AMULET", "GREEN_POTION", "MAGNIFYING_GLASS", "HANDCUFFS", "CREATION", "SHUFFLER", "WHITE_POTION", "MUSHROOM"];
        // 过滤掉不可偷取的 (GLOVES)
        const stealable = opponentSpirits.map((s, i) => ({ s, i })).filter(item => item.s !== 'GLOVES');

        if (stealable.length === 0) return 0; // Should not happen if checked before

        for (let p of priority) {
            const match = stealable.find(item => item.s === p);
            if (match) return match.i;
        }
        return stealable[Math.floor(Math.random() * stealable.length)].i;
    }

    chooseSpiritToForceUse(opponentSpirits, opponent) {
        // 简单的评分
        let bestIdx = -1;
        let maxScore = -Infinity;

        opponentSpirits.forEach((spirit, i) => {
            let score = 0;
            if (spirit === "CONTRACT") score = 200;
            else if (spirit === "PILLOW") score = 150;
            else if (spirit === "WHITE_POTION") score = opponent.hp <= 2 ? 120 : 30;
            else if (spirit === "GREEN_POTION" && opponent.hp >= opponent.maxHp) score = 80; // 满血喝药浪费
            else if (spirit === "CREATION" && opponent.spirits.length >= MAX_SPIRITS) score = 70; // 爆牌
            else if (spirit === "GLOVES") score = -100; // 偷我？不行
            else if (HIDDEN_SPIRITS.includes(spirit)) score = -50;
            else if (["ERASER", "HANDCUFFS", "REMOTE_CONTROL", "RADIO"].includes(spirit)) score = -200; // 对我用？不行
            else score = 10;

            if (score > maxScore) {
                maxScore = score;
                bestIdx = i;
            }
        });

        return maxScore > 20 ? bestIdx : null;
    }

    // Hell AI 功能：更新记牌
    updateDeckKnowledge(deck) {
        // 简化：只记录剩余的牌
        // 实际逻辑需要更复杂的追踪，这里简化为每次洗牌后重置
    }
}

module.exports = AIPlayer;
