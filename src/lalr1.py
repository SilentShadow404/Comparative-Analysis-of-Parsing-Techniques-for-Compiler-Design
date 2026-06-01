"""
lalr1.py — LALR(1) parser.

Builds the canonical LR(1) collection, then merges states that share the
same LR(0) core (i.e., same items ignoring lookaheads).  The resulting
automaton has the same state count as LR(0) but richer lookahead information
than SLR(1).

Merge can introduce NEW Reduce/Reduce conflicts that do not exist in LR(1).
"""

from collections import defaultdict
from src.grammar import Grammar, EPSILON, EOF
from src.lr_base import canonical_collection, closure, Item
from src.lr0 import _conflict_type


class LALR1Parser:

    def __init__(self, grammar: Grammar):
        self.grammar    = grammar
        lr1_states, lr1_transitions, aug_start = canonical_collection(grammar, lr1=True)
        self.aug_start  = aug_start

        # --- Merge LR(1) states by LR(0) core ---
        core_to_group = defaultdict(list)   # core_key -> [lr1_state_indices]
        for idx, state in enumerate(lr1_states):
            core_key = frozenset(item.core for item in state)
            core_to_group[core_key].append(idx)

        # Map: old LR(1) state index -> new LALR state index
        old_to_new = {}
        merged_states = []   # list of frozenset[Item] (merged)
        for new_idx, (core_key, old_indices) in enumerate(core_to_group.items()):
            for old_idx in old_indices:
                old_to_new[old_idx] = new_idx
            # Merge: union lookaheads for items with same core
            core_item_la = defaultdict(set)
            for old_idx in old_indices:
                for item in lr1_states[old_idx]:
                    core_item_la[item.core] |= item.lookaheads
            merged = frozenset(
                Item(lhs, rhs, dot, frozenset(las))
                for (lhs, rhs, dot), las in core_item_la.items()
            )
            merged_states.append(merged)

        # Rebuild transitions using new indices
        merged_transitions = {}
        for (old_idx, sym), old_tgt in lr1_transitions.items():
            new_src = old_to_new[old_idx]
            new_tgt = old_to_new[old_tgt]
            merged_transitions[(new_src, sym)] = new_tgt

        self.states      = merged_states
        self.transitions = merged_transitions
        self.action      = {}
        self.goto_table  = {}
        self.conflicts   = []
        self.lr1_num_states   = len(lr1_states)
        self.lalr_num_states  = len(merged_states)
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
                        reduce_act = f"r {item.lhs} -> {' '.join(item.rhs)}"
                        for la in item.lookaheads:
                            self._add_action(idx, la, reduce_act)
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
    def is_lalr1(self) -> bool:
        return len(self.conflicts) == 0

    def conflict_summary(self):
        return self.conflicts

    def state_reduction_info(self) -> str:
        return (f"LR(1) states: {self.lr1_num_states} -> "
                f"LALR(1) states: {self.lalr_num_states} "
                f"(reduced by {self.lr1_num_states - self.lalr_num_states})")
