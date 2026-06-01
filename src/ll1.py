"""
ll1.py — LL(1) predictive parse-table builder, conflict detector, and parse tracer.
"""

from collections import defaultdict
from src.grammar import Grammar, EPSILON, EOF


class LL1ConflictError(Exception):
    pass


class LL1Parser:
    """
    Constructs the LL(1) parse table for a grammar and optionally runs
    a parsing trace on an input string.
    """

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.table   = {}       # {(A, a): (lhs, rhs)}
        self.conflicts = []     # [(A, a, existing, new)]
        self._build()

    # ------------------------------------------------------------------
    # Build parse table
    # ------------------------------------------------------------------

    def _build(self):
        g = self.grammar
        first  = g.compute_first()
        follow = g.compute_follow()

        for lhs, rhs in g.productions:
            first_rhs = g.first_of_string(rhs)

            for terminal in first_rhs - {EPSILON}:
                key = (lhs, terminal)
                if key in self.table:
                    self.conflicts.append((lhs, terminal, self.table[key], (lhs, rhs)))
                else:
                    self.table[key] = (lhs, rhs)

            if EPSILON in first_rhs:
                for terminal in follow.get(lhs, set()):
                    key = (lhs, terminal)
                    if key in self.table:
                        self.conflicts.append((lhs, terminal, self.table[key], (lhs, rhs)))
                    else:
                        self.table[key] = (lhs, rhs)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def is_ll1(self) -> bool:
        return len(self.conflicts) == 0

    # ------------------------------------------------------------------
    # Parse trace
    # ------------------------------------------------------------------

    def parse_trace(self, tokens: list) -> list:
        """
        Simulate LL(1) parsing of `tokens` (list of terminal strings, no EOF).
        Returns a list of step dicts with 'stack', 'input', 'action'.
        Raises LL1ConflictError or ValueError on failure.
        """
        if not self.is_ll1:
            raise LL1ConflictError("Grammar is not LL(1); cannot parse.")

        input_tokens = tokens + [EOF]
        stack = [EOF, self.grammar.start]
        steps = []
        idx = 0

        while stack:
            top  = stack[-1]
            curr = input_tokens[idx]
            step = {
                'stack': list(reversed(stack)),
                'input': input_tokens[idx:],
                'action': None
            }
            if top == EOF and curr == EOF:
                step['action'] = 'ACCEPT'
                steps.append(step)
                break
            elif top == curr:
                step['action'] = f'MATCH {top}'
                stack.pop()
                idx += 1
            elif top in self.grammar.nonterminals:
                entry = self.table.get((top, curr))
                if entry is None:
                    step['action'] = f'ERROR — no entry for ({top}, {curr})'
                    steps.append(step)
                    break
                lhs, rhs = entry
                step['action'] = f'EXPAND {lhs} -> {" ".join(rhs)}'
                stack.pop()
                if rhs != [EPSILON]:
                    for sym in reversed(rhs):
                        stack.append(sym)
            else:
                step['action'] = f'ERROR — mismatch: top={top}, input={curr}'
                steps.append(step)
                break
            steps.append(step)
        return steps

    # ------------------------------------------------------------------
    # Pretty table (returns dict suitable for reporter)
    # ------------------------------------------------------------------

    def get_table_dict(self) -> dict:
        """Returns {(A, a): 'A -> rhs'} string representation."""
        return {k: f"{v[0]} -> {' '.join(v[1])}" for k, v in self.table.items()}
