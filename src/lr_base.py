"""
lr_base.py — Shared infrastructure for all LR parsers:
  Item, ItemSet, closure(), goto(), and canonical collection builders
  for both LR(0) and LR(1).
"""

from collections import defaultdict
from src.grammar import Grammar, EPSILON, EOF


# ============================================================
# LR Item
# ============================================================

class Item:
    """
    An LR item.
    For LR(0): lookaheads = frozenset()
    For LR(1): lookaheads = frozenset({terminal, ...})
    """
    __slots__ = ('lhs', 'rhs', 'dot', 'lookaheads')

    def __init__(self, lhs: str, rhs: tuple, dot: int, lookaheads=frozenset()):
        self.lhs       = lhs
        self.rhs       = rhs          # tuple of symbols
        self.dot       = dot
        self.lookaheads = frozenset(lookaheads)

    @property
    def is_complete(self) -> bool:
        return self.dot >= len(self.rhs) or self.rhs == (EPSILON,)

    @property
    def next_symbol(self):
        if self.is_complete:
            return None
        return self.rhs[self.dot]

    def advance(self) -> 'Item':
        return Item(self.lhs, self.rhs, self.dot + 1, self.lookaheads)

    # Core = (lhs, rhs, dot) — used for LALR merging
    @property
    def core(self):
        return (self.lhs, self.rhs, self.dot)

    def __eq__(self, other):
        return (self.lhs == other.lhs and self.rhs == other.rhs
                and self.dot == other.dot and self.lookaheads == other.lookaheads)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.dot, self.lookaheads))

    def __repr__(self):
        rhs_str = list(self.rhs)
        rhs_str.insert(self.dot, '•')
        la = ', '.join(sorted(self.lookaheads)) if self.lookaheads else ''
        la_str = f'  [{la}]' if la else ''
        return f"{self.lhs} -> {' '.join(rhs_str)}{la_str}"


# ============================================================
# Closure and Goto
# ============================================================

def closure(items: frozenset, grammar: Grammar, lr1: bool = False) -> frozenset:
    """
    Compute the closure of a set of items.
    lr1=False -> LR(0) closure (ignore lookaheads)
    lr1=True  -> LR(1) closure (propagate lookaheads)
    """
    if lr1:
        # Use a dict: core -> merged_lookaheads, to avoid duplicates
        core_la = {}
        for item in items:
            core_la.setdefault(item.core, set()).update(item.lookaheads)

        worklist = list(items)
        while worklist:
            item = worklist.pop()
            B = item.next_symbol
            if B is None or B not in grammar.nonterminals:
                continue
            beta = item.rhs[item.dot + 1:]
            for lhs2, rhs2 in grammar.productions_for(B):
                core2 = (lhs2, tuple(rhs2), 0)
                new_las = set()
                for la in item.lookaheads:
                    first_beta_a = grammar.first_of_string(list(beta) + [la])
                    new_las |= (first_beta_a - {EPSILON})
                if not new_las:
                    continue
                existing = core_la.get(core2, set())
                added = new_las - existing
                if added:
                    core_la.setdefault(core2, set()).update(added)
                    new_item = Item(lhs2, tuple(rhs2), 0,
                                   frozenset(core_la[core2]))
                    worklist.append(new_item)

        return frozenset(
            Item(lhs, rhs, dot, frozenset(las))
            for (lhs, rhs, dot), las in core_la.items()
        )
    else:
        result = set(items)
        worklist = list(items)
        while worklist:
            item = worklist.pop()
            B = item.next_symbol
            if B is None or B not in grammar.nonterminals:
                continue
            for lhs2, rhs2 in grammar.productions_for(B):
                new_item = Item(lhs2, tuple(rhs2), 0)
                if new_item not in result:
                    result.add(new_item)
                    worklist.append(new_item)
        return frozenset(result)


def goto(items: frozenset, symbol: str, grammar: Grammar, lr1: bool = False) -> frozenset:
    """
    GOTO(I, X) — advance all items in I whose dot is before X.
    """
    kernel = frozenset(
        item.advance()
        for item in items
        if item.next_symbol == symbol
    )
    if not kernel:
        return frozenset()
    return closure(kernel, grammar, lr1=lr1)


# ============================================================
# Canonical Collection
# ============================================================

def canonical_collection(grammar: Grammar, lr1: bool = False):
    """
    Build the canonical collection of LR(0) or LR(1) item sets.
    Returns:
        states: list of frozenset[Item]
        transitions: dict[(state_idx, symbol) -> state_idx]
    """
    # Augment grammar: add S' → S
    aug_start  = grammar.start + "'"
    aug_prod   = (aug_start, (grammar.start,))
    start_la   = frozenset([EOF]) if lr1 else frozenset()
    start_item = Item(aug_start, (grammar.start,), 0, start_la)
    init_state = closure(frozenset([start_item]), grammar, lr1=lr1)

    states      = [init_state]
    state_index = {init_state: 0}
    transitions = {}
    worklist    = [0]

    all_symbols = grammar.terminals | grammar.nonterminals

    while worklist:
        idx = worklist.pop(0)
        state = states[idx]
        for sym in all_symbols:
            nxt = goto(state, sym, grammar, lr1=lr1)
            if not nxt:
                continue
            if nxt not in state_index:
                state_index[nxt] = len(states)
                states.append(nxt)
                worklist.append(state_index[nxt])
            transitions[(idx, sym)] = state_index[nxt]

    return states, transitions, aug_start
