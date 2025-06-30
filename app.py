from flask import Flask, render_template, request, jsonify
import random
import itertools
import math

class Card:
    def __init__(self, card_type, value, set_name=None):
        self.card_type = card_type
        self.value = value
        self.set_name = set_name
    def __repr__(self):
        if self.card_type == 'number':
            return f"{self.value}({self.set_name})"
        return str(self.value)

def build_deck():
    sets = ['Gold', 'Silver', 'Bronze', 'Dirt']
    deck = []
    for set_name in sets:
        for num in range(0, 11):
            deck.append(Card('number', num, set_name))
    for _ in range(4):
        deck.append(Card('special', '*'))
        deck.append(Card('special', '√'))
    random.shuffle(deck)
    return deck

def deal_hand(deck):
    hand = [deck.pop() for _ in range(4)]
    hand += [Card('operator', '+'), Card('operator', '-'), Card('operator', '/')]
    return hand

def draw_number_card(deck):
    while deck:
        card = deck.pop()
        if card.card_type == 'number':
            return card
    return None

def process_hand(hand, deck):
    hand = list(hand)
    sqrt_indices = [i for i, c in enumerate(hand) if c.card_type == 'special' and c.value == '√']
    star_indices = [i for i, c in enumerate(hand) if c.card_type == 'special' and c.value == '*']
    for sqrt_idx in sqrt_indices:
        if star_indices:
            star_idx = star_indices.pop(0)
            hand[star_idx] = draw_number_card(deck)
        else:
            other_sqrt_indices = [i for i in sqrt_indices if i != sqrt_idx]
            if other_sqrt_indices:
                other_idx = other_sqrt_indices[0]
                hand[other_idx] = draw_number_card(deck)
                sqrt_indices.remove(other_idx)
    for i, card in enumerate(hand):
        if card.card_type == 'special' and card.value == '*':
            for j, other in enumerate(hand):
                if j != i and (
                    (other.card_type == 'operator' and other.value in ['+', '-']) or
                    (other.card_type == 'special' and other.value == '*' and j != i)
                ):
                    hand[j] = draw_number_card(deck)
                    break
    return hand

def is_operator(card):
    return card.card_type == 'operator' or (card.card_type == 'special' and card.value == '*')

def is_number(card):
    return card.card_type == 'number'

def is_unary(card):
    return card.card_type == 'special' and card.value == '√'

def card_to_str(card):
    if card.card_type == 'special' and card.value == '*':
        return '*'
    if card.card_type == 'special' and card.value == '√':
        return '√'
    return str(card.value)

def safe_eval(expr):
    try:
        expr = expr.replace('√', 'math.sqrt')
        return eval(expr, {"__builtins__": None, "math": math})
    except Exception:
        return None

def cards_to_expression(cards):
    expr = ""
    i = 0
    while i < len(cards):
        card = cards[i]
        if card.card_type == 'number':
            expr += str(card.value)
            i += 1
        elif card.card_type == 'operator' or (card.card_type == 'special' and card.value == '*'):
            expr += card.value
            i += 1
        elif card.card_type == 'special' and card.value == '√':
            if i + 1 < len(cards) and cards[i+1].card_type == 'number':
                expr += f"math.sqrt({cards[i+1].value})"
                i += 2
            else:
                return None
        else:
            return None
    return expr

def safe_eval(expr):
    try:
        return eval(expr, {"__builtins__": None, "math": math})
    except Exception:
        return None

def build_expressions(cards):
    if len(cards) == 1:
        card = cards[0]
        if is_number(card):
            return [str(card.value)]
        return []
    expressions = []
    for i in range(1, len(cards)):
        left = cards[:i]
        right = cards[i:]
        if is_operator(cards[i-1]) and left and right:
            op = card_to_str(cards[i-1])
            left_exprs = build_expressions(left[:-1])
            right_exprs = build_expressions(right)
            for l in left_exprs:
                for r in right_exprs:
                    expressions.append(f"({l}{op}{r})")
        if is_unary(cards[i-1]) and right:
            right_exprs = build_expressions(right)
            for r in right_exprs:
                expressions.append(f"√({r})")
    return expressions

def generate_expressions(hand):
    expressions = set()
    for perm in set(itertools.permutations(hand)):
        exprs = build_expressions(list(perm))
        for expr in exprs:
            value = safe_eval(expr)
            if value is not None and not isinstance(value, complex):
                expressions.add((expr, value))
    return list(expressions)

def find_best_results(expressions, targets=[1, 20]):
    best = {target: (None, float('inf')) for target in targets}
    for expr, value in expressions:
        for target in targets:
            diff = abs(value - target)
            if diff < best[target][1]:
                best[target] = (expr, diff)
    return best

app = Flask(__name__)

@app.route("/")
def index():
    deck = build_deck()
    hand = deal_hand(deck)
    hand = process_hand(hand, deck)
    return render_template("index.html", hand=hand)

@app.route("/evaluate", methods=["POST"])
def evaluate():
    card_order = request.json["card_order"]
    hand = [Card(**c) for c in card_order]
    expr = cards_to_expression(hand)
    if expr:
        value = safe_eval(expr)
        return jsonify({"expr": expr, "value": value})
    else:
        return jsonify({"expr": "", "value": ""})
    
@app.route("/best", methods=["POST"])
def best():
    card_order = request.json["card_order"]
    hand = [Card(**c) for c in card_order]
    exprs = generate_expressions(hand)
    best_results = find_best_results(exprs)
    best_results = {k: list(v) if v[0] is not None else ["", ""] for k, v in best_results.items()}
    return jsonify(best_results)
if __name__ == "__main__":
    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
