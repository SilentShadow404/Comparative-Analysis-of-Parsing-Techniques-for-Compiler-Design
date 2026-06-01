"""
slr1.py — SLR(1) parser.

Reuses the LR(0) canonical automaton but restricts reduce actions:
  Reduce A->α is added to ACTION[s, a] only when a ∈ FOLLOW(A).
This resolves many LR(0) conflicts.
"""

from src.grammar import Grammar, EPSILON, EOF
from src.lr_base import canonical_collection
from src.lr0 import _conflict_type


class SLR1Parser:

    def __init__(self, grammar: Grammar):
        self.grammar    = grammar
        self.states, self.transitions, self.aug_start = canonical_collection(grammar, lr1=False)
        self.follow     = grammar.compute_follow()
        self.action     = {}
        self.goto_table = {}
        self.conflicts  = []
        self._build()

    def _add_action(self, state_idx, symbol, action_str):
        key = (state_idx, symbol)
        if key not in self.action:
            self.action[key] = []
        existing = self.action[key]
        if action_str in existing:
            return
        if existing:
            for prev in existing:
                ctype = _conflict_type(prev, action_str)
                self.conflicts.append((state_idx, symbol, prev, action_str, ctype))
        existing.append(action_str)

    def _build(self):
        for idx, state in enumerate(self.states):
            for item in state:
                if item.is_complete:
                    if item.lhs == self.aug_start:
                        self._add_action(idx, EOF, 'accept')
                    else:
                        # SLR(1): reduce only on FOLLOW(A)
                        reduce_act = f"r {item.lhs} -> {' '.join(item.rhs)}"
                        for t in self.follow.get(item.lhs, set()):
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

    @property
    def is_slr1(self) -> bool:
        return len(self.conflicts) == 0

    def conflict_summary(self):
        return self.conflicts
