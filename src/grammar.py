"""
grammar.py — Core grammar representation with FIRST/FOLLOW computation,
nullable detection, left-recursion detection/removal, and left-factoring.
"""

from collections import defaultdict
from copy import deepcopy


EPSILON = 'eps'
EOF     = '$'


class Grammar:
    """
    Represents a context-free grammar.

    Productions are stored as a list of (lhs: str, rhs: list[str]).
    The first production's LHS is the start symbol unless overridden.
    """

    def __init__(self, name: str, productions: list, start: str = None):
        self.name = name
        self.productions = productions          # [(lhs, [sym, ...]), ...]
        self.start = start or productions[0][0]

        # Derived sets — populated lazily
        self._nullable  = None
        self._first     = None
        self._follow    = None
        self._nonterminals = None
        self._terminals    = None

    # ------------------------------------------------------------------
    # Symbol classification
    # ------------------------------------------------------------------

    @property
    def nonterminals(self):
        if self._nonterminals is None:
            self._nonterminals = {lhs for lhs, _ in self.productions}
        return self._nonterminals

    @property
    def terminals(self):
        if self._terminals is None:
            syms = set()
            for _, rhs in self.productions:
                for s in rhs:
                    if s not in self.nonterminals and s != EPSILON:
                        syms.add(s)
            self._terminals = syms
        return self._terminals

    # ------------------------------------------------------------------
    # Nullable computation (fixed-point)
    # ------------------------------------------------------------------

    def compute_nullable(self):
        if self._nullable is not None:
            return self._nullable
        nullable = set()
        # Seed: A → ε
        for lhs, rhs in self.productions:
            if rhs == [EPSILON]:
                nullable.add(lhs)
        # Fixed-point
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                if lhs not in nullable and all(s in nullable for s in rhs):
                    nullable.add(lhs)
                    changed = True
        self._nullable = nullable
        return nullable

    # ------------------------------------------------------------------
    # FIRST sets
    # ------------------------------------------------------------------

    def compute_first(self):
        if self._first is not None:
            return self._first
        nullable = self.compute_nullable()
        first = defaultdict(set)
        # Terminals: FIRST(a) = {a}
        for t in self.terminals:
            first[t].add(t)
        # Fixed-point for nonterminals
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                if rhs == [EPSILON]:
                    continue
                for sym in rhs:
                    before = len(first[lhs])
                    first[lhs] |= (first[sym] - {EPSILON})
                    if len(first[lhs]) != before:
                        changed = True
                    if sym not in nullable:
                        break
                else:
                    # All symbols nullable → FIRST includes ε
                    if EPSILON not in first[lhs]:
                        first[lhs].add(EPSILON)
                        changed = True
        self._first = dict(first)
        return self._first

    def first_of_string(self, symbols: list) -> set:
        """FIRST of a sequence of symbols."""
        nullable = self.compute_nullable()
        first = self.compute_first()
        result = set()
        for sym in symbols:
            if sym == EPSILON:
                result.add(EPSILON)
                break
            result |= (first.get(sym, {sym}) - {EPSILON})
            if sym not in nullable:
                break
        else:
            result.add(EPSILON)
        return result

    # ------------------------------------------------------------------
    # FOLLOW sets
    # ------------------------------------------------------------------

    def compute_follow(self):
        if self._follow is not None:
            return self._follow
        nullable = self.compute_nullable()
        first = self.compute_first()
        follow = defaultdict(set)
        follow[self.start].add(EOF)

        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                if rhs == [EPSILON]:
                    continue
                for i, sym in enumerate(rhs):
                    if sym not in self.nonterminals:
                        continue
                    # Add FIRST of the suffix after sym
                    beta = rhs[i+1:]
                    first_beta = self.first_of_string(beta) if beta else {EPSILON}
                    before = len(follow[sym])
                    follow[sym] |= (first_beta - {EPSILON})
                    if EPSILON in first_beta:
                        follow[sym] |= follow[lhs]
                    if len(follow[sym]) != before:
                        changed = True
        self._follow = dict(follow)
        return follow

    # ------------------------------------------------------------------
    # Left recursion detection
    # ------------------------------------------------------------------

    def detect_left_recursion(self) -> dict:
        """
        Returns {nonterminal: ['direct'|'indirect']} for all left-recursive NTs.
        """
        result = {}
        for lhs, rhs in self.productions:
            if rhs and rhs[0] == lhs:
                result.setdefault(lhs, []).append('direct')
        return result

    # ------------------------------------------------------------------
    # Common prefix detection
    # ------------------------------------------------------------------

    def detect_common_prefixes(self) -> dict:
        """
        Returns {A: [(prefix, [prod1, prod2, ...]), ...]} for NTs with common prefixes.
        """
        from itertools import groupby
        conflicts = {}
        nt_prods = defaultdict(list)
        for lhs, rhs in self.productions:
            nt_prods[lhs].append(rhs)
        for nt, rhss in nt_prods.items():
            if len(rhss) < 2:
                continue
            first_sym = defaultdict(list)
            for rhs in rhss:
                sym = rhs[0] if rhs and rhs != [EPSILON] else EPSILON
                first_sym[sym].append(rhs)
            for sym, group in first_sym.items():
                if len(group) > 1:
                    conflicts.setdefault(nt, []).append((sym, group))
        return conflicts

    # ------------------------------------------------------------------
    # Left recursion removal (direct only, Paull's algorithm)
    # ------------------------------------------------------------------

    def remove_left_recursion(self) -> 'Grammar':
        """
        Eliminates direct left recursion.
        Returns a new Grammar with transformed productions.
        """
        new_prods = []
        for nt in sorted(self.nonterminals, key=lambda x: [p[0] for p in self.productions].index(x)):
            # Separate left-recursive and non-left-recursive alternatives
            alpha_list = []  # suffixes of left-recursive rules: nt → nt α
            beta_list  = []  # non-left-recursive rules: nt → β
            nt_prods = [(lhs, rhs) for lhs, rhs in self.productions if lhs == nt]
            for _, rhs in nt_prods:
                if rhs and rhs[0] == nt:
                    alpha_list.append(rhs[1:])  # α part
                else:
                    beta_list.append(rhs)

            if not alpha_list:
                for _, rhs in nt_prods:
                    new_prods.append((nt, rhs))
            else:
                nt_prime = nt + "'"
                for beta in beta_list:
                    new_prods.append((nt, beta + [nt_prime]))
                for alpha in alpha_list:
                    new_prods.append((nt_prime, alpha + [nt_prime]))
                new_prods.append((nt_prime, [EPSILON]))

        g = Grammar(self.name + " (no left recursion)", new_prods, self.start)
        return g

    # ------------------------------------------------------------------
    # Left factoring
    # ------------------------------------------------------------------

    def left_factor(self) -> 'Grammar':
        """
        Applies left factoring to remove common prefixes.
        Returns a new Grammar.
        """
        new_prods = list(self.productions)
        counter = {}
        changed = True
        while changed:
            changed = False
            result = []
            i = 0
            while i < len(new_prods):
                lhs, rhs = new_prods[i]
                # Find all productions for this lhs
                group = [(j, r) for j, (l, r) in enumerate(new_prods) if l == lhs]
                # Group by first symbol
                by_first = defaultdict(list)
                for j, r in group:
                    sym = r[0] if r and r != [EPSILON] else EPSILON
                    by_first[sym].append((j, r))
                added = False
                for sym, items in by_first.items():
                    if len(items) > 1 and sym != EPSILON:
                        # Find longest common prefix
                        seqs = [r for _, r in items]
                        prefix = []
                        for k in range(min(len(s) for s in seqs)):
                            if all(s[k] == seqs[0][k] for s in seqs):
                                prefix.append(seqs[0][k])
                            else:
                                break
                        if not prefix:
                            continue
                        # Create new NT
                        counter[lhs] = counter.get(lhs, 0) + 1
                        new_nt = lhs + "'" * counter[lhs]
                        # Remove old productions for these indices
                        rm_indices = {j for j, _ in items}
                        new_prods = [(l, r) for idx, (l, r) in enumerate(new_prods)
                                     if idx not in rm_indices]
                        # Add factored production
                        new_prods.append((lhs, prefix + [new_nt]))
                        # Add new NT productions
                        for _, r in items:
                            suffix = r[len(prefix):]
                            new_prods.append((new_nt, suffix if suffix else [EPSILON]))
                        changed = True
                        break
                if changed:
                    break
        return Grammar(self.name + " (left-factored)", new_prods, self.start)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def productions_for(self, nt: str):
        return [(lhs, rhs) for lhs, rhs in self.productions if lhs == nt]

    def __repr__(self):
        lines = [f"Grammar: {self.name}  (start={self.start})"]
        for lhs, rhs in self.productions:
            lines.append(f"  {lhs} → {' '.join(rhs)}")
        return '\n'.join(lines)
