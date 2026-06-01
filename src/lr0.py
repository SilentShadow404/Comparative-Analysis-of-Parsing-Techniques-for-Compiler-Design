"""
lr0.py — LR(0) ACTION/GOTO table builder and conflict detector.
"""

from src.grammar import Grammar, EPSILON, EOF
from src.lr_base import canonical_collection, Item


class LR0Parser:
    """
    Builds the LR(0) ACTION/GOTO table.

    ACTION[s, a]:
      - shift s'   — if GOTO(I_s, a) = I_s'
      - reduce A->α — if A->α• ∈ I_s  (for EVERY terminal including $)
      - accept      — if S'->S• ∈ I_s and a = $

    Conflicts:
      - Shift/Reduce (S/R): both shift and reduce apply to same (state, terminal)
      - Reduce/Reduce (R/R): two different reduces apply to same (state, terminal)
    """

    def __init__(self, grammar: Grammar):
        self.grammar     = grammar
        self.states, self.transitions, self.aug_start = canonical_collection(grammar, lr1=False)
        self.action      = {}   # {(state_idx, terminal): [action_str, ...]}
        self.goto_table  = {}   # {(state_idx, nt): state_idx}
        self.conflicts   = []   # [(state_idx, symbol, action1, action2, type)]
        self._build()

    # ------------------------------------------------------------------

    def _add_action(self, state_idx, symbol, action_str):
        key = (state_idx, symbol)
        if key not in self.action:
            self.action[key] = []
        existing = self.action[key]
        if action_str in existing:
            return
        if existing:
            # Determine conflict type
            for prev in existing:
                ctype = _conflict_type(prev, action_str)
                self.conflicts.append((state_idx, symbol, prev, action_str, ctype))
        existing.append(action_str)

    def _build(self):
        all_terminals = self.grammar.terminals | {EOF}

        for idx, state in enumerate(self.states):
            for item in state:
                if item.is_complete:
                    if item.lhs == self.aug_start:
                        self._add_action(idx, EOF, 'accept')
                    else:
                        # Reduce on ALL terminals
                        rhs_str = ' '.join(item.rhs) if item.rhs != (EPSILON,) else EPSILON
                        reduce_act = f"r {item.lhs} -> {' '.join(item.rhs)}"
                        for t in all_terminals:
                            self._add_action(idx, t, reduce_act)
                else:
                    sym = item.next_symbol
                    if sym in self.grammar.terminals:
                        nxt = self.transitions.get((idx, sym))
                        if nxt is not None:
                            self._add_action(idx, sym, f's{nxt}')
                    elif sym in self.grammar.nonterminals:
                        nxt = self.transitions.get((idx, sym))
                        if nxt is not None:
                            self.goto_table[(idx, sym)] = nxt

    # ------------------------------------------------------------------

    @property
    def is_lr0(self) -> bool:
        return len(self.conflicts) == 0

    def conflict_summary(self) -> list:
        return self.conflicts

    def state_items_str(self) -> list:
        """Returns list of (state_idx, [item_str]) for display."""
        result = []
        for idx, state in enumerate(self.states):
            items = sorted(str(i) for i in state)
            result.append((idx, items))
        return result


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _conflict_type(a1: str, a2: str) -> str:
    kinds = {a1[0], a2[0]}
    if kinds == {'s', 'r'}:
        return 'Shift/Reduce'
    if kinds == {'r'}:
        return 'Reduce/Reduce'
    return 'Shift/Shift'
