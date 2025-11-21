import random
import time
import os
import json
from collections import Counter
import msvcrt # 用于非阻塞输入检测
import sys

# --- 游戏常量定义 ---

# AI思考延迟（秒），可以设为0以获得最快速度
AI_THINK_DELAY = 0.5 

# 灵物名称 (混淆了护身符和镜子)
SPIRIT_NAMES = {
    "AMULET": "护身符",    
    "MIRROR": "镜子",    
    "REMOTE_CONTROL": "遥控器",
    "ERASER": "橡皮擦",
    "GLOVES": "手套",
    "GREEN_POTION": "绿药水",
    "CREATION": "无中生有",
    "MUSHROOM": "蘑菇",
    "WHITE_POTION": "白药水",
    "SHUFFLER": "洗牌器",
    "MAGNIFYING_GLASS": "放大镜",
    "RED_POTION": "红药水",
    "HANDCUFFS": "手铐",
    "TELEPHONE": "电话",
    "PILLOW": "枕头",
    "CONTRACT": "契约书",
    "RADIO": "无线电",
}

# 需要对玩家和对手隐藏真实身份的灵物
HIDDEN_SPIRITS = {"AMULET", "MIRROR"}
# NEW: 为隐藏灵物设置一个统一的显示名称
MYSTERIOUS_CHARM_NAME = "神秘护符"


# 命运卡牌名称
FATE_CARD_NAMES = {
    "DIVINE_PUNISHMENT": "天罚",
    "DIVINE_BOON": "恩赐",
    "THE_VOID": "虚无",
    "REINCARNATION": "轮回",
    "BACKLASH": "反噬",
}

# --- 规则和说明常量 ---

GAME_RULES = """
--- 游戏核心规则 ---
1. 游戏目标：将对手的生命值降至0或以下即可获胜。
2. 玩家回合：轮到你的回合时，你可以先使用任意数量的灵物（只要你没被【手铐】束缚）。
3. 结束回合：当你准备好后，选择“使用命运卡牌”。这会从命运牌堆顶抽一张牌，结算其效果，然后你的回合结束。
4. 生命与灵物：
   - 初始生命值为4，上限为5。
   - 每次失去生命值，你会获得2个灵物作为补偿。
   - 灵物持有上限为5个。
5. 额外回合：某些卡牌或效果可能会让你获得额外回合。
"""

SPIRIT_DESCRIPTIONS = {
    "AMULET": f"【{SPIRIT_NAMES['AMULET']}】：（隐藏灵物）使你在接下来的2个回合内，受到的第1点伤害无效。若单次受到超过1点的伤害，护符会破碎并使你受到双倍伤害。",
    "MIRROR": f"【{SPIRIT_NAMES['MIRROR']}】：（隐藏灵物）直到你的下个回合开始前，下一次指向你的命运卡牌效果将被反弹给对手。反弹的伤害+1。",
    "REMOTE_CONTROL": "【遥控器】：在你使用命运卡牌结束回合后，你的对手将立刻对自己使用牌堆顶的一张命运卡牌。无法连续使用。",
    "ERASER": "【橡皮擦】：随机移除对手最多2个灵物。",
    "GLOVES": "【手套】：选择并偷取对手一个灵物（无法偷取【手套】）。",
    "GREEN_POTION": "【绿药水】：恢复1点生命值。",
    "CREATION": "【无中生有】：从灵物牌堆中获得2个灵物。",
    "MUSHROOM": "【蘑菇】：你下一次抽取的命运卡牌，将被替换为一张完全随机的命运卡牌。",
    "WHITE_POTION": "【白药水】：49%概率恢复1点生命，49%概率失去1点生命，1%概率恢复2点生命，1%概率失去2点生命。",
    "SHUFFLER": "【洗牌器】：你下一次抽取的命运卡牌，将与牌堆中随机一张牌交换位置。",
    "MAGNIFYING_GLASS": "【放大镜】：查看命运牌堆顶的第一张牌。",
    "RED_POTION": "【红药水】：你的下一张造成伤害的命运卡牌，伤害+1。",
    "HANDCUFFS": "【手铐】：你的对手下个回合无法使用灵物，但他会获得1个灵物作为补偿。无法连续使用。",
    "TELEPHONE": "【电话】：查看命运牌堆中指定位置的一张牌。",
    "PILLOW": "【枕头】：立即获得3个灵物，但你会跳过你的下个回合。在接下来的2个回合内，你将免疫【手铐】。",
    "CONTRACT": "【契约书】：立即失去2点生命值。你下次生命值归零时，会以1点生命值存活，并获得一个最终回合和3个灵物。若最终回合内未能获胜，则直接落败。",
    "RADIO": "【无线电】：选择并强制你的对手使用他的一个灵物。该灵物的使用和目标选择由你决定。",
}

FATE_CARD_DESCRIPTIONS = {
    "DIVINE_PUNISHMENT": "【天罚】：对目标造成1点伤害。",
    "DIVINE_BOON": "【恩赐】：目标获得1个灵物。",
    "THE_VOID": "【虚无】：无事发生。若对自己使用，你将获得一个额外回合。",
    "REINCARNATION": "【轮回】：目标将立刻对自己使用牌堆顶的下一张命运卡牌。",
    "BACKLASH": "【反噬】：对目标造成1点伤害。若目标因此失去生命，目标将获得一个额外回合。",
}


# 游戏设置
INITIAL_HP = 4
MAX_HP = 5
MAX_SPIRITS = 5
INITIAL_SPIRITS = 2
HP_LOSS_SPIRIT_GAIN = 2
MIN_FATE_CARDS = 5
MAX_FATE_CARDS = 10

# --- 辅助函数 ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_slow(text, delay=0.03):
    for i, char in enumerate(text):
        print(char, end='', flush=True)
        if os.name == 'nt' and msvcrt.kbhit():
            msvcrt.getch()
            print(text[i+1:], end='')
            break
        time.sleep(delay)
    print()

def print_to_player(player, message):
    """只对人类玩家显示信息"""
    if not isinstance(player, BaseAIPlayer):
        print_slow(message)

# --- 数据统计类 ---
class GameStats:
    def __init__(self, filename="fate_game_stats.json"):
        self.filename = filename
        self.stats = {
            "wins": 0,
            "losses": 0,
            "total_damage_dealt": 0,
            "total_damage_taken": 0,
            "spirits_used": Counter(),
            "fate_cards_drawn": Counter(),
        }
        self.load()

    def load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                loaded_stats = json.load(f)
                self.stats["wins"] = loaded_stats.get("wins", 0)
                self.stats["losses"] = loaded_stats.get("losses", 0)
                self.stats["total_damage_dealt"] = loaded_stats.get("total_damage_dealt", 0)
                self.stats["total_damage_taken"] = loaded_stats.get("total_damage_taken", 0)
                self.stats["spirits_used"] = Counter(loaded_stats.get("spirits_used", {}))
                self.stats["fate_cards_drawn"] = Counter(loaded_stats.get("fate_cards_drawn", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            print_slow("未找到统计文件或文件损坏，将创建新的统计数据。")

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4, ensure_ascii=False)

    def record_win(self):
        self.stats["wins"] += 1

    def record_loss(self):
        self.stats["losses"] += 1

    def record_damage_dealt(self, amount):
        self.stats["total_damage_dealt"] += amount

    def record_damage_taken(self, amount):
        self.stats["total_damage_taken"] += amount

    def record_spirit_used(self, spirit_name):
        self.stats["spirits_used"][spirit_name] += 1

    def record_fate_card_drawn(self, card_name):
        self.stats["fate_cards_drawn"][card_name] += 1

    def display(self):
        clear_screen()
        print("--- 玩家战绩统计 ---")
        total_games = self.stats['wins'] + self.stats['losses']
        win_rate = (self.stats['wins'] / total_games * 100) if total_games > 0 else 0
        print(f"胜场: {self.stats['wins']} | 败场: {self.stats['losses']} | 胜率: {win_rate:.1f}%")
        print(f"累计造成伤害: {self.stats['total_damage_dealt']}")
        print(f"累计承受伤害: {self.stats['total_damage_taken']}")
        
        print("\n--- 灵物使用统计 ---")
        if self.stats['spirits_used']:
            for spirit, count in self.stats['spirits_used'].most_common():
                print(f"【{SPIRIT_NAMES.get(spirit, spirit)}】: {count} 次")
        else:
            print("暂无记录。")

        print("\n--- 命运卡牌抽取统计 ---")
        if self.stats['fate_cards_drawn']:
            for card, count in self.stats['fate_cards_drawn'].most_common():
                print(f"【{FATE_CARD_NAMES.get(card, card)}】: {count} 次")
        else:
            print("暂无记录。")
            
        input("\n--- 按回车键返回 ---")


# --- 核心类定义 ---

class Player:
    def __init__(self, name):
        self.name = name
        self.hp = INITIAL_HP
        self.max_hp = MAX_HP
        self.spirits = []
        self.status = {
            "amulet_turns": 0,
            "is_mirrored": False,
            "is_handcuffed": False,
            "pillow_immunity": 0,
            "skip_next_turn": False,
            "has_contract": False,
            "last_stand": False,
            "red_potion_bonus": 0,
            "remote_control_active": False,
            "mushroom_effect": False,
            "shuffler_effect": False,
        }

    def take_damage(self, amount, source_is_mirror=False):
        if amount <= 0:
            return 0
        
        final_damage = amount
        
        if self.status["amulet_turns"] > 0:
            # 触发时揭示身份
            if amount > 1:
                final_damage = amount * 2
                print_slow(f"💥 {self.name} 的【{MYSTERIOUS_CHARM_NAME}】({SPIRIT_NAMES['AMULET']})因巨大伤害而破碎，受到双倍伤害！")
                self.status["amulet_turns"] = 0
            else:
                final_damage = 0
                print_slow(f"🛡️ {self.name} 的【{MYSTERIOUS_CHARM_NAME}】({SPIRIT_NAMES['AMULET']})吸收了1点伤害。")
        
        if source_is_mirror:
            final_damage += 1
            print_slow(f"🪞 {SPIRIT_NAMES['MIRROR']}反弹的伤害+1！")
            
        if final_damage > 0:
            self.hp -= final_damage
            print_slow(f"💔 {self.name} 失去了 {final_damage} 点生命值，当前生命值: {self.hp}")
            return final_damage
        else:
            print_slow(f"{self.name} 没有受到伤害。")
            return 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        print_slow(f"💚 {self.name} 恢复了 {amount} 点生命值，当前生命值: {self.hp}")

    def add_spirit(self, spirit_name):
        if len(self.spirits) < MAX_SPIRITS:
            self.spirits.append(spirit_name)
            # CHANGED: 获得隐藏灵物时，不显示其真实名称
            display_name = f"【{MYSTERIOUS_CHARM_NAME}】" if spirit_name in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(spirit_name, spirit_name)}】"
            print_slow(f"✨ {self.name} 获得了灵物: {display_name}")
        else:
            print_slow(f"⚠️ {self.name} 的灵物已满（{MAX_SPIRITS}个），无法获得新的灵物。")

    def display_status(self, for_opponent=False): # for_opponent 参数现在只用于历史兼容，新逻辑不再需要
        print(f"--- {self.name} 的状态 ---")
        print(f"❤️  生命值: {self.hp}/{self.max_hp}")
        
        spirit_display = []
        if self.spirits:
            for s in self.spirits:
                # CHANGED: 隐藏灵物对所有人都显示为“神秘护符”
                if s in HIDDEN_SPIRITS:
                    spirit_display.append(f"【{MYSTERIOUS_CHARM_NAME}】")
                else:
                    spirit_display.append(f"【{SPIRIT_NAMES.get(s, s)}】")
        else:
            spirit_display.append("无")
            
        print(f"👻 灵物 ({len(self.spirits)}/{MAX_SPIRITS}): {' '.join(spirit_display)}")
        
        active_statuses = []
        # 状态效果的显示也使用模糊名称
        if self.status['amulet_turns'] > 0: active_statuses.append(f"屏障守护({self.status['amulet_turns']}回合)")
        if self.status['is_mirrored']: active_statuses.append("空间折射")
        if self.status['is_handcuffed']: active_statuses.append("被手铐")
        if self.status['pillow_immunity'] > 0: active_statuses.append(f"枕头免疫({self.status['pillow_immunity']}回合)")
        if self.status['has_contract']: active_statuses.append("契约书")
        if self.status['last_stand']: active_statuses.append("最终回合")
        if active_statuses:
            print(f"🌟 状态: {', '.join(active_statuses)}")
        print("-" * (len(self.name) + 12))

class BaseAIPlayer(Player):
    def __init__(self, name="AI"):
        super().__init__(name)
    def ai_choose_action(self, opponent, game): raise NotImplementedError
    def ai_choose_target(self, opponent): raise NotImplementedError
    def ai_choose_spirit_to_steal(self, stealable_spirits): raise NotImplementedError
    def ai_choose_spirit_to_force_use(self, opponent_spirits, opponent_player_object): raise NotImplementedError

class HardAIPlayer(BaseAIPlayer):
    def __init__(self, name="AI (困难)"):
        super().__init__(name)

    def ai_choose_action(self, opponent, game):
        time.sleep(AI_THINK_DELAY / 2)
        if self.spirits and not self.status["is_handcuffed"] and random.random() < 0.4:
            return f"spirit_index_{random.randint(0, len(self.spirits)-1)}"
        return "fate_card"

    def ai_choose_target(self, opponent):
        time.sleep(AI_THINK_DELAY / 4)
        return 'opponent' if random.random() < 0.9 else 'self'

    def ai_choose_spirit_to_steal(self, stealable_spirits):
        return random.choice(stealable_spirits)

    def ai_choose_spirit_to_force_use(self, opponent_spirits, opponent_player_object):
        return random.choice(opponent_spirits)

class ExpertAIPlayer(BaseAIPlayer):
    def __init__(self, name="AI (专家)"):
        super().__init__(name)
        self.known_next_fate_card = None
        self.intended_fate_card_target = 'opponent'

    def _determine_strategic_tendency(self, opponent):
        if self.hp <= 2: return "Defensive"
        if opponent.hp <= 2: return "Aggressive"
        if self.hp > opponent.hp: return "Stable"
        return "Stable"

    def _evaluate_spirit_use(self, opponent, game, tendency):
        best_spirit_index = -1
        highest_score = 0
        for i, spirit in enumerate(self.spirits):
            score = 0
            if spirit == "GREEN_POTION": score += (self.max_hp - self.hp) * 40
            elif spirit == "ERASER": score += len(opponent.spirits) * 25
            elif spirit == "GLOVES":
                stealable_count = len([s for s in opponent.spirits if s != "GLOVES"])
                if stealable_count > 0 and len(self.spirits) < MAX_SPIRITS: score += 35 + stealable_count * 5
            elif spirit == "CREATION": score += (MAX_SPIRITS - len(self.spirits)) * 15
            elif spirit == "MAGNIFYING_GLASS" and self.known_next_fate_card is None: score += 80
            elif spirit == "CONTRACT" and not self.status["has_contract"]:
                if self.hp <= 2: score += 150
                elif self.hp == 3: score += 50
            elif spirit == "WHITE_POTION": score += 15 if self.hp > 1 else -200
            elif spirit == "PILLOW" and len(self.spirits) <= 2: score += 80 - opponent.hp * 5
            elif spirit == "RADIO" and opponent.spirits: score += 50
            # NEW: AI now evaluates hidden spirits based on tendency
            elif spirit in HIDDEN_SPIRITS:
                if tendency == "Defensive": score += 90 # 赌它是防御性物品
                else: score += 40
            else: score += 30
            if self.known_next_fate_card in ["DIVINE_PUNISHMENT", "BACKLASH"]:
                if spirit == "RED_POTION": score += 120
                if spirit == "MIRROR": score += 60 # AI knows it has a mirror
            if tendency == "Aggressive":
                if spirit in ["RED_POTION", "ERASER", "HANDCUFFS", "REMOTE_CONTROL", "RADIO"]: score *= 1.5
            if tendency == "Defensive":
                if spirit in ["AMULET", "MIRROR", "GREEN_POTION"]: score *= 1.8
            if spirit in ["HANDCUFFS", "REMOTE_CONTROL"] and game.last_spirit_used_by_player[game.players.index(self)] == spirit:
                score = -1000
            if score > highest_score:
                highest_score = score
                best_spirit_index = i
        return best_spirit_index, highest_score

    def ai_choose_action(self, opponent, game):
        time.sleep(AI_THINK_DELAY)
        tendency = self._determine_strategic_tendency(opponent)
        if not self.status["is_handcuffed"]:
            best_index, score = self._evaluate_spirit_use(opponent, game, tendency)
            if score > 35:
                return f"spirit_index_{best_index}"
        return "fate_card"

    def ai_choose_target(self, opponent):
        time.sleep(AI_THINK_DELAY / 2)
        if self.known_next_fate_card in ["THE_VOID", "DIVINE_BOON"]:
            self.intended_fate_card_target = 'self'
            return 'self'
        self.intended_fate_card_target = 'opponent'
        return 'opponent'

    def ai_choose_spirit_to_steal(self, stealable_spirits):
        priority = ["CONTRACT", "RED_POTION", "PILLOW", "ERASER", "REMOTE_CONTROL", "RADIO", "MIRROR", "AMULET", "GREEN_POTION", "MAGNIFYING_GLASS", "HANDCUFFS", "CREATION", "SHUFFLER", "WHITE_POTION", "MUSHROOM"]
        for p_spirit in priority:
            if p_spirit in stealable_spirits: return p_spirit
        return random.choice(stealable_spirits)

    def ai_choose_spirit_to_force_use(self, opponent_spirits, opponent_player_object):
        scores = {}
        for spirit in opponent_spirits:
            score = 0
            if spirit == "CONTRACT": score = 200
            elif spirit == "PILLOW": score = 150
            elif spirit == "WHITE_POTION": score = 120 if opponent_player_object.hp <= 2 else 30
            elif spirit == "GREEN_POTION" and opponent_player_object.hp >= opponent_player_object.max_hp: score = 80
            elif spirit == "CREATION" and len(opponent_player_object.spirits) >= MAX_SPIRITS: score = 70
            elif spirit == "GLOVES" and not any(s != "GLOVES" for s in self.spirits): score = 60
            elif spirit in HIDDEN_SPIRITS: score = -50 # 赌一手这个隐藏物品对自己没好处
            elif spirit in ["ERASER", "HANDCUFFS", "REMOTE_CONTROL", "RADIO"]: score = -200
            elif spirit == "GLOVES": score = -100 * len([s for s in self.spirits if s != "GLOVES"])
            else: score = 10
            scores[spirit] = score
        if not scores or max(scores.values()) < 20: return None
        return max(scores, key=scores.get)

class HellAIPlayer(ExpertAIPlayer):
    def __init__(self, name="AI (地狱)"):
        super().__init__(name)
        self.known_fate_deck_composition = Counter()
    def update_deck_knowledge(self, deck): self.known_fate_deck_composition = Counter(deck)
    def see_card_draw(self, card):
        if card in self.known_fate_deck_composition:
            self.known_fate_deck_composition[card] -= 1
            if self.known_fate_deck_composition[card] == 0: del self.known_fate_deck_composition[card]
    def _determine_strategic_tendency(self, opponent):
        tendency = super()._determine_strategic_tendency(opponent)
        if not self.known_fate_deck_composition: return tendency
        total_cards = sum(self.known_fate_deck_composition.values())
        if total_cards == 0: return tendency
        damage_cards = self.known_fate_deck_composition.get("DIVINE_PUNISHMENT", 0) + self.known_fate_deck_composition.get("BACKLASH", 0)
        threat_ratio = damage_cards / total_cards
        if threat_ratio > 0.6 and tendency not in ["Desperate", "Aggressive"]: return "Defensive"
        if threat_ratio < 0.2 and tendency == "Stable": return "Aggressive"
        return tendency

# ==============================================================================
# --- 策略模式实现 (灵物) ---
# ==============================================================================
class SpiritStrategy:
    def apply(self, user: Player, opponent: Player, game: 'Game'): raise NotImplementedError

class AmuletStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["amulet_turns"] = 2
        # 使用时不揭示身份，只显示模糊信息
        print_slow(f"🛡️ 一道神秘的屏障笼罩了 {user.name}。")

class MirrorStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["is_mirrored"] = True
        # 使用时不揭示身份，只显示模糊信息
        print_slow(f"✨ {user.name} 周身的空间开始微微扭曲...")

class RemoteControlStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["remote_control_active"] = True
        print_slow("遥控器已设置，将在你的回合结束后对你的对手生效。")

class EraserStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        if not opponent.spirits:
            print_slow(f"但 {opponent.name} 没有任何灵物可以移除。")
            return
        num_to_remove = min(2, len(opponent.spirits))
        removed_spirits = random.sample(opponent.spirits, k=num_to_remove)
        print_slow(f"橡皮擦抹去了 {opponent.name} 的 {num_to_remove} 个随机灵物！")
        for s in removed_spirits:
            opponent.spirits.remove(s)
            # CHANGED: 移除时，即使是隐藏灵物，也会揭示其真实身份
            display_name = f"【{SPIRIT_NAMES.get(s, s)}】"
            print_slow(f" - {display_name} 已被移除。")

class GlovesStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        stealable = [s for s in opponent.spirits if s != "GLOVES"]
        if not stealable:
            print_slow(f"但 {opponent.name} 没有任何可以偷取的灵物。")
            return
        if len(user.spirits) >= MAX_SPIRITS:
            print_slow(f"但 {user.name} 的灵物已满，无法偷取！")
            return
        decision_maker = game.force_use_decision_maker if game.is_force_use_active else user
        stolen_spirit = game._get_opponent_spirit_choice(decision_maker, opponent, stealable)
        opponent.spirits.remove(stolen_spirit)
        
        # CHANGED: 偷取和获得时的描述保持一致性
        display_name_stolen = f"一个【{MYSTERIOUS_CHARM_NAME}】" if stolen_spirit in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(stolen_spirit, stolen_spirit)}】"
        print_slow(f"{decision_maker.name} 决定从 {opponent.name} 处偷取{display_name_stolen}!")
        
        user.add_spirit(stolen_spirit) # add_spirit内部会处理正确的打印信息

class GreenPotionStrategy(SpiritStrategy):
    def apply(self, user, opponent, game): user.heal(1)

class CreationStrategy(SpiritStrategy):
    def apply(self, user, opponent, game): game._draw_spirit_for_player(user, 2)

class MushroomStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["mushroom_effect"] = True
        print_to_player(user, "你的下一张抽取的牌将被替换成随机的另一张牌。")
        print_slow(f"{user.name} 的周围出现了奇妙的孢子...")

class WhitePotionStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        result = random.choices(['heal1', 'dmg1', 'heal2', 'dmg2'], weights=[49, 49, 1, 1], k=1)[0]
        if result == 'heal1':
            print_slow("白药水发出了温和的光芒...")
            user.heal(1)
        elif result == 'dmg1':
            print_slow("白药水变得浑浊并发出嘶嘶声...")
            dmg_done = user.take_damage(1)
            if dmg_done > 0: game._handle_hp_loss(user, dmg_done, attacker=user)
        elif result == 'heal2':
            print_slow("奇迹发生了！白药水散发出耀眼的光芒！")
            user.heal(2)
        elif result == 'dmg2':
            print_slow("灾难降临！白药水剧烈爆炸！")
            dmg_done = user.take_damage(2)
            if dmg_done > 0: game._handle_hp_loss(user, dmg_done, attacker=user)

class ShufflerStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["shuffler_effect"] = True
        print_to_player(user, "你的下一张抽取的牌将与牌堆中随机一张牌交换位置。")
        print_slow(f"{user.name} 面前的牌堆发生了小小的骚动...")

class MagnifyingGlassStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        print_slow(f"👁️ {user.name} 拿出了放大镜，仔细观察着牌堆...")
        # CHANGED: 牌堆为空的检查现在由 _draw_fate_card 统一处理，但这里只是查看，所以需要单独检查
        if not game.fate_deck:
            print_to_player(user, "牌堆是空的！")
            return

        next_card = game.fate_deck[0]
        # 信息只给使用者看
        print_to_player(user, f"你看清了下一张牌是: 【{FATE_CARD_NAMES.get(next_card, '未知')}】")
        if isinstance(user, ExpertAIPlayer):
            user.known_next_fate_card = next_card


class RedPotionStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        user.status["red_potion_bonus"] += 1
        print_slow(f"{user.name} 的身上泛起了不祥的红光...")
        print_to_player(user, "你的下一张伤害牌效果+1。")

class HandcuffsStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        if opponent.status["pillow_immunity"] > 0:
            print_slow(f"但 {opponent.name} 受到了【枕头】的保护，手铐无效！")
            return
        opponent.status["is_handcuffed"] = True
        game._draw_spirit_for_player(opponent, 1)
        print_slow(f"{opponent.name} 在下个回合将无法使用灵物，但他获得了一个灵物作为补偿。")

class TelephoneStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        if not game.fate_deck:
            print_to_player(user, "电话线是断的... 牌堆是空的！")
            return
        decision_maker = game.force_use_decision_maker if game.is_force_use_active else user
        print_slow(f"📞 {decision_maker.name} 拿起了电话，似乎在窃听着什么...")
        if isinstance(decision_maker, BaseAIPlayer):
            n = random.randint(1, len(game.fate_deck))
        else:
            while True:
                game._display_turn_interface(game.players[game.current_player_index], game.players[1 - game.current_player_index])
                try:
                    n_str = input(f"({decision_maker.name}) 你想看牌堆顶下方的第几张牌？(1-{len(game.fate_deck)}) -> ")
                    if not n_str: continue
                    n = int(n_str)
                    if 1 <= n <= len(game.fate_deck): break
                    else: print_slow("无效的数字。")
                except ValueError: print_slow("请输入一个数字。")
        # 信息只给使用者看
        print_to_player(decision_maker, f"你通过电话得知，牌堆的第 {n} 张牌是【{FATE_CARD_NAMES.get(game.fate_deck[n-1], '未知')}】。")

class PillowStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        game._draw_spirit_for_player(user, 3)
        user.status["skip_next_turn"] = True
        user.status["pillow_immunity"] = 3
        print_slow(f"{user.name} 获得了3个灵物，但会跳过下个回合，并在2回合内免疫【手铐】。")

class ContractStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        print_slow(f"{user.name} 划破手指，与命运签订了契约！立即扣除2点生命值。")
        dmg_done = user.take_damage(2)
        if dmg_done > 0: game._handle_hp_loss(user, dmg_done, attacker=user)
        if not game.game_over:
            user.status["has_contract"] = True
            print_slow("下次生命值归零时将获得最后的机会！")

class RadioStrategy(SpiritStrategy):
    def apply(self, user, opponent, game):
        if not opponent.spirits:
            print_slow(f"但 {opponent.name} 没有任何灵物可以被操控。")
            return
        if isinstance(user, BaseAIPlayer):
            spirit_to_force = user.ai_choose_spirit_to_force_use(opponent.spirits, opponent)
        else:
            spirit_to_force = game._get_spirit_choice_from_opponent(user, opponent)
        if spirit_to_force is None:
            print_slow(f"{user.name} 决定暂时不进行操控。")
            return
        
        # CHANGED: 描述保持一致性
        display_name = f"一个【{MYSTERIOUS_CHARM_NAME}】" if spirit_to_force in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(spirit_to_force, spirit_to_force)}】"
        print_slow(f"📡 {user.name} 使用无线电，锁定了 {opponent.name} 的{display_name}！")
        print_slow(f"{opponent.name} 不由自主地拿出了它...")
        time.sleep(AI_THINK_DELAY)
        
        # 使用被强制的灵物时，其所有者是opponent，但决策者是user
        # _use_spirit 方法现在不处理打印，所以我们在这里处理
        # 强制使用时，我们不打印 "xxx使用了灵物"，因为上面的文本已经很清楚了
        opponent.spirits.remove(spirit_to_force)
        forced_strategy = SPIRIT_STRATEGIES.get(spirit_to_force)
        if forced_strategy:
            game.is_force_use_active = True
            game.force_use_decision_maker = user
            # 注意这里的参数：灵物的“使用者”仍然是opponent，但后续决策（如偷窃目标）由user决定
            forced_strategy.apply(user=opponent, opponent=user, game=game)
            game.is_force_use_active = False
            game.force_use_decision_maker = None
        else:
            print_slow(f"警告：未找到灵物【{spirit_to_force}】的对应策略实现！")

# --- 策略注册表 ---
SPIRIT_STRATEGIES = {
    "AMULET": AmuletStrategy(), "MIRROR": MirrorStrategy(), "REMOTE_CONTROL": RemoteControlStrategy(),
    "ERASER": EraserStrategy(), "GLOVES": GlovesStrategy(), "GREEN_POTION": GreenPotionStrategy(),
    "CREATION": CreationStrategy(), "MUSHROOM": MushroomStrategy(), "WHITE_POTION": WhitePotionStrategy(),
    "SHUFFLER": ShufflerStrategy(), "MAGNIFYING_GLASS": MagnifyingGlassStrategy(), "RED_POTION": RedPotionStrategy(),
    "HANDCUFFS": HandcuffsStrategy(), "TELEPHONE": TelephoneStrategy(), "PILLOW": PillowStrategy(),
    "CONTRACT": ContractStrategy(), "RADIO": RadioStrategy(),
}

# ==============================================================================
# --- 游戏主控制器 ---
# ==============================================================================
class Game:
    def __init__(self):
        self.players = []
        self.spirit_deck = []
        self.fate_deck = []
        self.current_player_index = 0
        self.game_over = False
        self.winner = None
        self.extra_turn_player = None
        self.last_spirit_used_by_player = [None, None]
        self.is_force_use_active = False
        self.force_use_decision_maker = None
        self.difficulty_level = 0
        self.unlocked_level = 1
        self.PROGRESS_FILE = "fate_game_progress.dat"
        self.stats = GameStats() # 初始化统计系统

    def _show_rules(self):
        clear_screen()
        print(GAME_RULES)
        input("--- 按回车键查看灵物说明 ---")
        clear_screen()
        print("--- 灵物效果说明 ---")
        for spirit_key, description in SPIRIT_DESCRIPTIONS.items(): print(f"{description}\n")
        input("--- 按回车键查看命运卡牌说明 ---")
        clear_screen()
        print("--- 命运卡牌效果说明 ---")
        for card_key, description in FATE_CARD_DESCRIPTIONS.items(): print(f"{description}\n")
        input("--- 说明结束，按回车键返回 ---")

    def _setup(self):
        print_slow("--- 游戏准备中 ---")
        for name in SPIRIT_NAMES.keys(): self.spirit_deck.extend([name] * 2)
        random.shuffle(self.spirit_deck)
        self._create_fate_deck()
        for player in self.players:
            player.hp = INITIAL_HP
            player.spirits.clear() # 清空上一局的灵物
            for _ in range(INITIAL_SPIRITS): self._draw_spirit_for_player(player)
        self.current_player_index = random.randint(0, 1)
        second_player_index = 1 - self.current_player_index
        print_slow(f"{self.players[self.current_player_index].name} 成为先手玩家。")
        print_slow(f"{self.players[second_player_index].name} 作为后手，额外获得一个灵物。")
        self._draw_spirit_for_player(self.players[second_player_index])
        input("\n按回车键开始游戏...")

    def _create_fate_deck(self):
        self.fate_deck.clear()
        deck_size = random.randint(MIN_FATE_CARDS, MAX_FATE_CARDS)
        self.fate_deck = random.choices(list(FATE_CARD_NAMES.keys()), k=deck_size)
        print_slow(f"命运牌堆已重新生成，包含 {len(self.fate_deck)} 张卡牌。")
        for p in self.players:
            if isinstance(p, HellAIPlayer): p.update_deck_knowledge(self.fate_deck)

    def _draw_spirit_for_player(self, player, count=1):
        for _ in range(count):
            if not self.spirit_deck:
                print_slow("警告：灵物牌堆已空！正在重新生成...")
                for name in SPIRIT_NAMES.keys(): self.spirit_deck.extend([name] * 2)
                random.shuffle(self.spirit_deck)
            player.add_spirit(self.spirit_deck.pop())

    def _draw_fate_card(self, drawing_player):
        # CHANGED: 牌堆刷新逻辑被集中到这里，这是唯一的抽牌入口
        if not self.fate_deck:
            print_slow("命运牌堆已空，正在重新洗牌...")
            self._create_fate_deck()
            time.sleep(AI_THINK_DELAY) # 给玩家一个反应时间

        if drawing_player.status["shuffler_effect"]:
            drawing_player.status["shuffler_effect"] = False
            if len(self.fate_deck) > 1:
                swap_index = random.randint(1, len(self.fate_deck) - 1)
                self.fate_deck[0], self.fate_deck[swap_index] = self.fate_deck[swap_index], self.fate_deck[0]
                print_slow("⚙️【洗牌器】效果发动，牌堆发生了变化！")

        if drawing_player.status["mushroom_effect"]:
            drawing_player.status["mushroom_effect"] = False
            original_card = self.fate_deck.pop(0)
            print_slow(f"🍄【蘑菇】效果发动，将【{FATE_CARD_NAMES.get(original_card, original_card)}】变成了...")
            # 蘑菇效果后如果牌堆空了，也需要刷新
            if not self.fate_deck:
                self._create_fate_deck()
            new_card = random.choice(list(FATE_CARD_NAMES.keys()))
            self.fate_deck.insert(0, new_card)

        card = self.fate_deck.pop(0)
        if not isinstance(drawing_player, BaseAIPlayer): self.stats.record_fate_card_drawn(card)
        for p in self.players:
            if isinstance(p, HellAIPlayer): p.see_card_draw(card)
        if isinstance(drawing_player, ExpertAIPlayer): drawing_player.known_next_fate_card = None
        return card

    def load_progress(self):
        try:
            with open(self.PROGRESS_FILE, 'r') as f: self.unlocked_level = max(1, min(int(f.read()), 4))
        except (FileNotFoundError, ValueError): self.unlocked_level = 1

    def save_progress(self):
        with open(self.PROGRESS_FILE, 'w') as f: f.write(str(self.unlocked_level))

    def select_difficulty(self):
        DIFFICULTY_NAMES = {1: "困难", 2: "专家", 3: "地狱"}
        while True:
            clear_screen()
            print("--- 选择AI难度 ---")
            for i in range(1, 4):
                print(f"{i}. 【{DIFFICULTY_NAMES[i]}】" + (" (已解锁)" if i <= self.unlocked_level else f" (需战胜【{DIFFICULTY_NAMES[i-1]}】解锁)"))
            print("\n输入 'q' 返回主菜单。")
            choice = input("请输入你的选择: ").lower()
            if choice == 'q': return False
            try:
                level = int(choice)
                if 1 <= level <= 3:
                    if level <= self.unlocked_level:
                        self.difficulty_level = level
                        ai_name = f"AI ({DIFFICULTY_NAMES[level]})"
                        human_player = Player("玩家")
                        ai_player = {1: HardAIPlayer, 2: ExpertAIPlayer, 3: HellAIPlayer}[level](ai_name)
                        self.players = [human_player, ai_player]
                        return True
                    else: print_slow("该难度尚未解锁！")
                else: print_slow("无效的选择。")
            except ValueError: print_slow("无效的输入。")
            time.sleep(1.5)

    def main_menu(self):
        self.load_progress()
        while True:
            clear_screen()
            print("欢迎来到《命运轮盘》！")
            print("1. 开始新游戏 (AI对战)")
            print("2. 双人对战")
            print("3. 查看规则")
            print("4. 查看战绩")
            print("q. 退出游戏")
            choice = input("请输入选项: ").lower()
            if choice == '1':
                if self.select_difficulty(): self.run_game_loop()
            elif choice == '2':
                self.players = [Player("玩家1"), Player("玩家2")]
                self.difficulty_level = 0
                self.run_game_loop()
            elif choice == '3': self._show_rules()
            elif choice == '4': self.stats.display()
            elif choice == 'q':
                print_slow("感谢游玩！")
                break

    def run_game_loop(self):
        clear_screen()
        self._setup()
        self.game_over = False
        self.winner = None
        while not self.game_over:
            self._turn()
            self._check_game_over()
            if not self.game_over: self._switch_player()
        self._end_game()

    def _turn(self):
        player = self.players[self.current_player_index]
        opponent = self.players[1 - self.current_player_index]
        print_slow(f"\n轮到 {player.name} 的回合了。")
        self._update_player_status_start_of_turn(player)
        if player.status["skip_next_turn"]:
            player.status["skip_next_turn"] = False
            print_slow(f"由于【枕头】的效果，{player.name} 跳过本回合。")
            time.sleep(AI_THINK_DELAY * 2)
            return
        turn_ended = False
        while not turn_ended:
            action = self._get_player_action(player, opponent)
            if action == "fate_card":
                self.last_spirit_used_by_player[self.current_player_index] = None
                self._use_fate_card(player, opponent)
                turn_ended = True
            elif action.startswith("spirit_index_"):
                try:
                    spirit_index = int(action.split('_')[-1])
                    spirit_name = self._use_spirit(spirit_index, player, opponent)
                    self.last_spirit_used_by_player[self.current_player_index] = spirit_name
                    if spirit_name == "PILLOW": turn_ended = True
                    else:
                        if not isinstance(player, BaseAIPlayer): input("灵物已使用。按回车键继续...")
                        else: time.sleep(AI_THINK_DELAY)
                except (ValueError, IndexError): print_slow("内部错误：处理灵物选择时出现问题。")
            elif action == "back": continue
        print_slow(f"{player.name} 的回合结束。")
        time.sleep(AI_THINK_DELAY * 2)

    def _update_player_status_start_of_turn(self, player):
        if isinstance(player, ExpertAIPlayer):
            player.known_next_fate_card = None
            player.intended_fate_card_target = 'opponent'
        if player.status["amulet_turns"] > 0:
            player.status["amulet_turns"] -= 1
            if player.status["amulet_turns"] == 0: print_slow(f"{player.name} 的【{MYSTERIOUS_CHARM_NAME}】({SPIRIT_NAMES['AMULET']})效果已结束。")
        if player.status["pillow_immunity"] > 0:
            player.status["pillow_immunity"] -= 1
            if player.status["pillow_immunity"] == 0: print_slow(f"{player.name} 的【枕头】手铐免疫效果已结束。")
        
        # 镜子的效果只持续到自己回合开始，所以在这里重置
        if player.status["is_mirrored"]:
            player.status["is_mirrored"] = False
            print_slow(f"{player.name} 周身的【{MYSTERIOUS_CHARM_NAME}】({SPIRIT_NAMES['MIRROR']})效果消失了。")

        # 手铐效果在对方回合开始时解除
        self.players[1 - self.players.index(player)].status["is_handcuffed"] = False
        player.status["red_potion_bonus"] = 0

    def _display_turn_interface(self, player, opponent):
        clear_screen()
        print(f"--- 对手 ({opponent.name}) 状态 ---")
        opponent.display_status()
        print("\n" + "="*40 + "\n")
        print(f"--- 你的回合 ({player.name}) ---")
        player.display_status()

    def _get_player_action(self, player, opponent):
        if isinstance(player, BaseAIPlayer):
            self._display_turn_interface(player, opponent)
            return player.ai_choose_action(opponent, self)
        while True:
            self._display_turn_interface(player, opponent)
            print("\n请选择你的行动:")
            print("1. 使用命运卡牌 (结束回合)")
            can_use_spirit = player.spirits and not player.status["is_handcuffed"]
            if can_use_spirit: print("2. 使用灵物")
            elif player.status["is_handcuffed"]: print_slow("❌ 你被【手铐】束缚，无法使用灵物！")
            choice = input("输入选项编号: ")
            if choice == "1": return "fate_card"
            if choice == "2" and can_use_spirit: return self._get_spirit_choice(player, opponent)
            else: print_slow("无效的输入。")

    def _get_spirit_choice(self, player, opponent):
        while True:
            self._display_turn_interface(player, opponent)
            print("\n请选择要使用的灵物 (输入0返回):")
            for i, spirit in enumerate(player.spirits):
                # CHANGED: 列表也显示模糊名称
                display_name = f"【{MYSTERIOUS_CHARM_NAME}】" if spirit in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(spirit, spirit)}】"
                print(f"{i+1}. {display_name}")
            try:
                choice = int(input("输入灵物编号: "))
                if choice == 0: return "back"
                if 1 <= choice <= len(player.spirits):
                    selected_spirit = player.spirits[choice - 1]
                    if selected_spirit in ["HANDCUFFS", "REMOTE_CONTROL"] and self.last_spirit_used_by_player[self.current_player_index] == selected_spirit:
                        print_slow(f"❌ 【{SPIRIT_NAMES[selected_spirit]}】无法连续使用！")
                        time.sleep(1.5)
                        continue
                    return f"spirit_index_{choice - 1}"
                else: print_slow("无效的编号。")
            except (ValueError, TypeError): print_slow("请输入数字。")

    def _use_fate_card(self, user, opponent):
        print_slow(f"{user.name} 准备抽取命运卡牌...")
        target_choice = self._get_target_choice(user, opponent)
        target = user if target_choice == 'self' else opponent
        print_slow(f"{user.name} 决定将卡牌对 {target.name} 使用。")
        if not isinstance(user, BaseAIPlayer): input("按回车键抽取卡牌...")
        else: time.sleep(AI_THINK_DELAY)
        card = self._draw_fate_card(user)
        print_slow(f"抽出的卡牌是... 【{FATE_CARD_NAMES.get(card, card)}】!")
        time.sleep(AI_THINK_DELAY)
        self._apply_fate_card_effect(card, user, target)

    def _get_target_choice(self, user, opponent):
        if isinstance(user, BaseAIPlayer): return user.ai_choose_target(opponent)
        while True:
            choice = input(f"选择目标: 1. 自己 ({user.name})  2. 对方 ({opponent.name}) -> ")
            if choice in ['1', '2']: return 'self' if choice == '1' else 'opponent'
            print_slow("无效选择。")

    def _apply_fate_card_effect(self, card, user, target):
        print_slow(f"【{FATE_CARD_NAMES.get(card, card)}】的效果对 {target.name} 生效了。")
        damage_from_mirror = False
        if target.status["is_mirrored"]:
            # 触发时揭示身份
            print_slow(f"🪞 {target.name} 的【{MYSTERIOUS_CHARM_NAME}】({SPIRIT_NAMES['MIRROR']})生效了！效果被反弹！")
            target.status["is_mirrored"] = False
            new_target = user if target != user else self.players[1 - self.players.index(user)]
            print_slow(f"效果反弹给了 {new_target.name}！")
            target = new_target
            if card in ["DIVINE_PUNISHMENT", "BACKLASH"]: damage_from_mirror = True
        
        if card in ["DIVINE_PUNISHMENT", "BACKLASH"]:
            damage = 1 + user.status["red_potion_bonus"]
            actual_damage = target.take_damage(damage, source_is_mirror=damage_from_mirror)
            if actual_damage > 0: self._handle_hp_loss(target, actual_damage, attacker=user)
            if card == "BACKLASH" and actual_damage > 0:
                print_slow(f"【反噬】效果触发！失去生命值的 {target.name} 获得一个额外回合！")
                self.extra_turn_player = target
            user.status["red_potion_bonus"] = 0
        elif card == "DIVINE_BOON": self._draw_spirit_for_player(target)
        elif card == "THE_VOID":
            print_slow("虚无... 本回合无事发生。")
            if target == user:
                print_slow(f"由于对己使用，{user.name} 获得一个额外回合！")
                self.extra_turn_player = user
        elif card == "REINCARNATION":
            print_slow(f"【轮回】之力发动！{target.name} 将对自己使用下一张命运卡牌！")
            # REMOVED: 牌堆检查已移至 _draw_fate_card
            next_card = self._draw_fate_card(target)
            print_slow(f"下一张牌是... 【{FATE_CARD_NAMES.get(next_card, next_card)}】!")
            self._apply_fate_card_effect(next_card, target, target)

    def _use_spirit(self, spirit_index, user, opponent):
        spirit_name = user.spirits.pop(spirit_index)
        if not isinstance(user, BaseAIPlayer): self.stats.record_spirit_used(spirit_name)
        
        # CHANGED: 对隐藏物品，使用时显示统一的模糊信息
        if spirit_name in HIDDEN_SPIRITS:
            print_slow(f"{user.name} 使用了【{MYSTERIOUS_CHARM_NAME}】...")
        else:
            print_slow(f"{user.name} 使用了灵物: 【{SPIRIT_NAMES.get(spirit_name, spirit_name)}】")
        
        strategy = SPIRIT_STRATEGIES.get(spirit_name)
        if strategy: strategy.apply(user, opponent, self)
        else: print_slow(f"警告：未找到灵物【{spirit_name}】的对应策略实现！")
        return spirit_name

    def _get_spirit_choice_from_opponent(self, user, opponent):
        while True:
            self._display_turn_interface(user, opponent)
            print(f"\n请选择要强制 {opponent.name} 使用的灵物 (输入0取消):")
            for i, spirit in enumerate(opponent.spirits):
                # CHANGED: 强制使用时，也只能看到模糊名称
                display_name = f"【{MYSTERIOUS_CHARM_NAME}】" if spirit in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(spirit, spirit)}】"
                print(f"{i+1}. {display_name}")
            try:
                choice = int(input("输入灵物编号: "))
                if choice == 0: return None
                if 1 <= choice <= len(opponent.spirits): return opponent.spirits[choice - 1]
                else: print_slow("无效的编号。")
            except (ValueError, TypeError): print_slow("请输入数字。")

    def _get_opponent_spirit_choice(self, user, opponent, stealable_spirits):
        if isinstance(user, BaseAIPlayer): return user.ai_choose_spirit_to_steal(stealable_spirits)
        while True:
            self._display_turn_interface(self.players[self.current_player_index], self.players[1 - self.current_player_index])
            print(f"\n({user.name}) 请选择要从 {opponent.name} 处偷取的灵物:")
            for i, spirit in enumerate(stealable_spirits):
                # CHANGED: 偷取时，也只能看到模糊名称
                display_name = f"【{MYSTERIOUS_CHARM_NAME}】" if spirit in HIDDEN_SPIRITS else f"【{SPIRIT_NAMES.get(spirit, spirit)}】"
                print(f"{i+1}. {display_name}")
            try:
                choice = int(input("输入灵物编号: "))
                if 1 <= choice <= len(stealable_spirits): return stealable_spirits[choice - 1]
                else: print_slow("无效的编号。")
            except (ValueError, TypeError): print_slow("请输入数字。")

    def _handle_hp_loss(self, player, damage_dealt, attacker=None):
        if self.game_over or damage_dealt <= 0: return
        # 记录数据
        if not isinstance(player, BaseAIPlayer): self.stats.record_damage_taken(damage_dealt)
        if attacker and not isinstance(attacker, BaseAIPlayer): self.stats.record_damage_dealt(damage_dealt)
        
        gain_count = HP_LOSS_SPIRIT_GAIN * damage_dealt
        print_slow(f"作为失去生命的代价，{player.name} 获得了 {gain_count} 个灵物。")
        self._draw_spirit_for_player(player, gain_count)

    def _check_game_over(self):
        for player in self.players:
            if player.hp <= 0:
                if player.status["has_contract"] and not player.status["last_stand"]:
                    print_slow(f"✝️ {player.name} 的生命值归零，但【契约书】发动了！")
                    player.status["last_stand"] = True
                    player.hp = 1
                    print_slow(f"{player.name} 获得一个最终回合，并抽取3个灵物！")
                    self._draw_spirit_for_player(player, 3)
                    self.extra_turn_player = player
                    return
                self.game_over = True
                self.winner = self.players[1 - self.players.index(player)]
                break

    def _switch_player(self):
        current_player = self.players[self.current_player_index]
        current_player.red_potion_bonus = 0
        if current_player.status["last_stand"] and not self.game_over:
            print_slow(f"⏰ {current_player.name} 的最终回合结束，但未能击败对手。契约失败！")
            self.game_over = True
            self.winner = self.players[1 - self.current_player_index]
            return
        if self.extra_turn_player:
            self.current_player_index = self.players.index(self.extra_turn_player)
            self.extra_turn_player = None
        else:
            if current_player.status["remote_control_active"]:
                current_player.status["remote_control_active"] = False
                opponent = self.players[1 - self.current_player_index]
                print_slow(f"\n📡【遥控器】效果发动！{opponent.name} 将对自己使用牌堆顶的牌！")
                time.sleep(AI_THINK_DELAY)
                # REMOVED: 牌堆检查已移至 _draw_fate_card
                card = self._draw_fate_card(opponent)
                print_slow(f"{opponent.name} 抽到了... 【{FATE_CARD_NAMES.get(card, card)}】!")
                self._apply_fate_card_effect(card, opponent, opponent)
                self._check_game_over()
                if self.game_over: return
            self.current_player_index = 1 - self.current_player_index

    def _end_game(self):
        clear_screen()
        print_slow("="*30 + "\n          游戏结束！\n" + "="*30)
        if self.winner:
            print_slow(f"\n🏆 胜利者是: {self.winner.name}！ 🏆")
            human_player_won = not isinstance(self.winner, BaseAIPlayer)
            if self.difficulty_level > 0: # 是AI对战模式
                if human_player_won:
                    self.stats.record_win()
                    if self.difficulty_level >= self.unlocked_level and self.unlocked_level <= 3:
                        self.unlocked_level += 1
                        self.save_progress()
                        DIFFICULTY_NAMES = {2: "专家", 3: "地狱"}
                        if self.unlocked_level <= 3:
                            print_slow(f"\n🎉 恭喜！你已解锁【{DIFFICULTY_NAMES[self.unlocked_level]}】难度！🎉")
                        else:
                            print_slow("\n🎉 恭喜！你已征服所有难度！🎉")
                else:
                    self.stats.record_loss()
            self.stats.save() # 无论输赢都保存数据
        else:
            print_slow("游戏以平局结束... 这怎么可能？")
        input("\n--- 按回车键返回主菜单 ---")

# --- 游戏启动 ---
if __name__ == "__main__":
    game = Game()
    game.main_menu()