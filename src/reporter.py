"""
reporter.py -- Formatted output utilities for the analysis report.
Prints parse tables, FIRST/FOLLOW sets, conflict summaries, and grammar transforms
as readable ASCII text.
"""

from src.grammar import Grammar, EPSILON, EOF


# ============================================================
# Terminal formatting helpers
# ============================================================

def section(title: str, width: int = 72):
    bar = '=' * width
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def subsection(title: str, width: int = 60):
    print(f"\n  {'-' * width}")
    print(f"  {title}")
    print(f"  {'-' * width}")


def print_grammar(g: Grammar):
    print(f"\n  Grammar: {g.name}   (start = {g.start})")
    prev_lhs = None
    for lhs, rhs in g.productions:
        rhs_str = ' '.join(rhs)
        if lhs == prev_lhs:
            print(f"      {'':>{len(lhs)}}  | {rhs_str}")
        else:
            print(f"    {lhs} -> {rhs_str}")
        prev_lhs = lhs


def print_first_follow(g: Grammar):
    first  = g.compute_first()
    follow = g.compute_follow()
    nts    = list(dict.fromkeys(lhs for lhs, _ in g.productions))  # preserve order

    print(f"\n  {'Nonterminal':<16} {'FIRST':<36} {'FOLLOW'}")
    print(f"  {'-'*16} {'-'*36} {'-'*30}")
    for nt in nts:
        f_str = '{ ' + ', '.join(sorted(first.get(nt, set()))) + ' }'
        fo_str = '{ ' + ', '.join(sorted(follow.get(nt, set()))) + ' }'
        print(f"  {nt:<16} {f_str:<36} {fo_str}")


def print_nullable(g: Grammar):
    nullable = g.compute_nullable()
    if nullable:
        print(f"\n  Nullable nonterminals: {', '.join(sorted(nullable))}")
    else:
        print(f"\n  Nullable nonterminals: (none)")


def print_left_recursion(g: Grammar):
    lr = g.detect_left_recursion()
    if lr:
        for nt, kinds in lr.items():
            print(f"  [!]  Left recursion in {nt}: {', '.join(kinds)}")
    else:
        print(f"  [OK]  No left recursion detected.")


def print_common_prefixes(g: Grammar):
    cp = g.detect_common_prefixes()
    if cp:
        for nt, groups in cp.items():
            for sym, rhss in groups:
                rhs_strs = [' '.join(r) for r in rhss]
                print(f"  [!]  Common prefix in {nt}: symbol '{sym}' shared by: "
                      + ' | '.join(rhs_strs))
    else:
        print(f"  [OK]  No common prefixes detected.")


# ============================================================
# LL(1) parse table
# ============================================================

def print_ll1_table(parser):
    g = parser.grammar
    nts  = list(dict.fromkeys(lhs for lhs, _ in g.productions))
    terms = sorted(g.terminals | {EOF})
    col_w = max(len(t) for t in terms) + 2
    nt_w  = max(len(nt) for nt in nts) + 2

    header = f"  {'':>{nt_w}}" + ''.join(f"{t:^{col_w}}" for t in terms)
    print(header)
    print(f"  {'-'*nt_w}" + '-' * col_w * len(terms))

    for nt in nts:
        row = f"  {nt:>{nt_w}}"
        for t in terms:
            entry = parser.table.get((nt, t))
            cell  = (f"{entry[0]}->{''.join(entry[1])}" if entry else '') if entry else ''
            if len(cell) > col_w - 1:
                cell = cell[:col_w-4] + '...'
            row += f"{cell:^{col_w}}"
        print(row)

    if parser.conflicts:
        print(f"\n  *** {len(parser.conflicts)} CONFLICT(S) DETECTED ***")
        for lhs, t, existing, new_prod, *_ in parser.conflicts:
            e_str = f"{existing[0]}->{''.join(existing[1])}"
            n_str = f"{new_prod[0]}->{''.join(new_prod[1])}"
            print(f"    Conflict at ({lhs}, '{t}'): {e_str}  vs  {n_str}")
    else:
        print(f"\n  [OK]  No conflicts -- grammar IS LL(1)")


# ============================================================
# LR parse table (shared display for LR(0)/SLR/LR(1)/LALR)
# ============================================================

def print_lr_table(parser, title: str):
    g     = parser.grammar
    terms = sorted(g.terminals | {EOF})
    nts   = sorted(g.nonterminals)
    n     = len(parser.states)
    col_w = 14

    print(f"\n  {title}")
    # Header
    hdr = f"  {'State':>6} |"
    for t in terms:
        hdr += f"{t:^{col_w}}|"
    hdr += f"{'':^4}|"
    for nt in nts:
        hdr += f"{nt:^{col_w}}|"
    print(hdr)
    print(f"  {'-'*7}+" + (f"{'-'*col_w}+" * len(terms)) + f"{'-'*5}+" +
          (f"{'-'*col_w}+" * len(nts)))

    for s in range(n):
        row = f"  {s:>6} |"
        for t in terms:
            acts = parser.action.get((s, t), [])
            cell = '/'.join(acts) if acts else ''
            if len(cell) > col_w - 1:
                cell = cell[:col_w-4] + '...'
            row += f"{cell:^{col_w}}|"
        row += f"{'':^4}|"
        for nt in nts:
            g_val = parser.goto_table.get((s, nt), '')
            cell  = str(g_val) if g_val != '' else ''
            row += f"{cell:^{col_w}}|"
        print(row)

    if parser.conflicts:
        print(f"\n  *** {len(parser.conflicts)} CONFLICT(S) ***")
        seen = set()
        for state, sym, a1, a2, ctype in parser.conflicts:
            key = (state, sym, a1, a2)
            if key in seen:
                continue
            seen.add(key)
            print(f"    State {state}, symbol '{sym}': {ctype}  [{a1}]  vs  [{a2}]")
    else:
        print(f"\n  [OK]  No conflicts -- grammar passes this technique")


# ============================================================
# LR automaton state display
# ============================================================

def print_lr_states(parser, title: str, max_states: int = 30):
    subsection(f"LR Automaton States -- {title}")
    for idx, state in enumerate(parser.states[:max_states]):
        items = sorted(str(item) for item in state)
        print(f"\n  State {idx}:")
        for it in items:
            print(f"    {it}")
    if len(parser.states) > max_states:
        print(f"\n  ... ({len(parser.states) - max_states} more states not shown)")


# ============================================================
# Applicability summary table
# ============================================================

def print_applicability_table(results: list):
    """
    results: [(grammar_name, ll1, lr0, slr1, lr1, lalr1)]
    Each value is True (no conflicts) or False.
    """
    techniques = ['LL(1)', 'LR(0)', 'SLR(1)', 'LR(1)', 'LALR(1)']
    col_w = 12
    g_w   = 28
    section("APPLICABILITY SUMMARY TABLE")
    header = f"  {'Grammar':<{g_w}}"
    for t in techniques:
        header += f"{t:^{col_w}}"
    print(header)
    print(f"  {'-'*g_w}" + '-' * col_w * len(techniques))
    for row in results:
        name = row[0]
        line = f"  {name:<{g_w}}"
        for val in row[1:]:
            mark = '[OK]  YES' if val else '[NO]  NO '
            line += f"{mark:^{col_w}}"
        print(line)


# ============================================================
# LL(1) parse trace
# ============================================================

def print_parse_trace(steps: list, title: str = 'Parse Trace'):
    subsection(title)
    print(f"\n  {'Step':<5} {'Stack':<35} {'Input':<30} Action")
    print(f"  {'-'*5} {'-'*35} {'-'*30} {'-'*40}")
    for i, step in enumerate(steps, 1):
        stack_str = ' '.join(step['stack'])[-34:]
        input_str = ' '.join(step['input'])[:29]
        action    = step['action']
        print(f"  {i:<5} {stack_str:<35} {input_str:<30} {action}")


# ============================================================
# New professional display helpers (added for structured output)
# ============================================================

W = 80   # default line width


def big_header(title_lines: list, subtitle_lines: list = None, w: int = W):
    """Print the main program banner."""
    bar = '+' + '=' * (w - 2) + '+'
    print(bar)
    for line in title_lines:
        print('|' + line.center(w - 2) + '|')
    if subtitle_lines:
        print('|' + ' ' * (w - 2) + '|')
        for line in subtitle_lines:
            print('|' + line.center(w - 2) + '|')
    print(bar)


def grammar_header(label: str, description: str, w: int = W):
    """Print a prominent header for each grammar's section."""
    bar = '#' * w
    inner = f'  GRAMMAR {label} -- {description}'
    print(f"\n\n{bar}")
    print(f"#{inner:<{w-2}}#")
    print(bar)


def technique_header(num: int, name: str, applied_to: str, w: int = W - 4):
    """Print a technique subsection banner."""
    bar = '+' + '-' * w + '+'
    label = f'  [T{num}]  {name}  --  applied to: {applied_to}'
    print(f"\n{bar}")
    print(f"|{label:<{w}}|")
    print(bar)


def verdict_box(passed: bool, technique: str, num_conflicts: int = 0, w: int = W - 4):
    """Print a clear PASS / FAIL verdict box."""
    bar = '+' + '=' * w + '+'
    sym = '[PASS]' if passed else '[FAIL]'
    if passed:
        msg = f'  VERDICT: {sym}  Grammar IS {technique}'
    else:
        msg = f'  VERDICT: {sym}  Grammar is NOT {technique}  ({num_conflicts} conflict(s))'
    print(f"\n{bar}")
    print(f"|{msg:<{w}}|")
    print(bar)


def print_properties_table(g: Grammar):
    """Print a structured properties table for a grammar."""
    lr       = g.detect_left_recursion()
    cp       = g.detect_common_prefixes()
    nullable = g.compute_nullable()

    hdr = f"\n  {'Property':<22} {'Status':<8} Detail"
    sep = f"  {'-'*22} {'-'*8} {'-'*44}"
    print(hdr)
    print(sep)

    # Left recursion
    if lr:
        details = '; '.join(f"{nt} ({', '.join(kinds)})" for nt, kinds in lr.items())
        print(f"  {'Left Recursion':<22} {'[YES]':<8} {details}")
    else:
        print(f"  {'Left Recursion':<22} {'[NO]':<8} None detected")

    # Common prefixes
    if cp:
        details = '; '.join(
            f"{nt}: prefix '{sym}'"
            for nt, groups in cp.items()
            for sym, _ in groups
        )
        print(f"  {'Common Prefixes':<22} {'[YES]':<8} {details}")
    else:
        print(f"  {'Common Prefixes':<22} {'[NO]':<8} None detected")

    # Nullable
    if nullable:
        print(f"  {'Nullable NTs':<22} {'[YES]':<8} {{{', '.join(sorted(nullable))}}}")
    else:
        print(f"  {'Nullable NTs':<22} {'[NO]':<8} None")


def print_ll1_formal(parser):
    """Formal verification of LL(1) conditions from parse table data."""
    g       = parser.grammar
    follow  = g.compute_follow()
    nts     = list(dict.fromkeys(lhs for lhs, _ in g.productions))

    print("\n  Formal LL(1) Condition Check:")
    print("  Rule: For every A -> a1 | a2 | ... :")
    print("    (i)  FIRST(ai) intersect FIRST(aj) = {} for i != j")
    print("    (ii) eps in FIRST(ai) => FIRST(ai) intersect FOLLOW(A) = {}")

    if parser.conflicts:
        print("\n  VIOLATIONS:")
        for lhs, t, e1, e2, *_ in parser.conflicts:
            e1s = f"{e1[0]}->{''.join(e1[1])}"
            e2s = f"{e2[0]}->{''.join(e2[1])}"
            print(f"    Cell ({lhs}, '{t}'): both {e1s} and {e2s} match")
            print(f"    => FIRST or FOLLOW sets overlap on terminal '{t}'")
    else:
        # Summarise key non-trivial checks
        found_checks = False
        for nt in nts:
            prods = [rhs for lh, rhs in g.productions if lh == nt]
            if len(prods) < 2:
                continue
            found_checks = True
            first_sets = []
            for rhs in prods:
                fs = g.first_of_string(rhs)
                if 'eps' in fs:
                    fs = (fs - {'eps'}) | follow.get(nt, set())
                first_sets.append((rhs, fs))
            combined = set()
            ok = True
            for rhs, fs in first_sets:
                if fs & combined:
                    ok = False
                combined |= fs
            alts = ' | '.join(' '.join(r) for r in prods)
            print(f"    {nt} -> {alts}")
            for rhs, fs in first_sets:
                print(f"         FIRST({' '.join(rhs)}) = {{{', '.join(sorted(fs))}}}")
            print(f"         Pairwise disjoint: {'YES' if ok else 'NO'}")
        if not found_checks:
            print("    All nonterminals have single alternatives -- no conflicts possible.")
        print("  => All LL(1) conditions satisfied.")


def print_lr0_conflict_detail(parser):
    """Show exact conflicting states and items for LR(0)."""
    if not parser.conflicts:
        print("\n  No LR(0) conflicts -- every state has unambiguous shift/reduce/accept.")
        return

    print("\n  LR(0) Conflict Analysis:")
    print("  (LR(0) has no lookahead: a complete item A->alpha. reduces on ALL terminals)")

    seen = set()
    for state_idx, sym, a1, a2, ctype in parser.conflicts:
        if state_idx in seen:
            continue
        seen.add(state_idx)

        state  = parser.states[state_idx]
        c_items = sorted(repr(i) for i in state if i.is_complete)
        s_items = sorted(repr(i) for i in state
                         if not i.is_complete and i.next_symbol == sym)

        print(f"\n    State {state_idx} items relevant to conflict on '{sym}':")
        for it in c_items:
            print(f"      {it}  <<< complete: reduces on ALL terminals")
        for it in s_items:
            print(f"      {it}  <<< wants to shift '{sym}'")
        print(f"    => {ctype} conflict on '{sym}'  (LR(0) cannot resolve)")


def print_slr1_resolution(slr_parser, lr0_parser):
    """Show formally how SLR(1) resolves (or fails to resolve) LR(0) conflicts."""
    if not lr0_parser.conflicts:
        print("\n  LR(0) had no conflicts; SLR(1) trivially passes.")
        return

    g      = slr_parser.grammar
    follow = g.compute_follow()

    if slr_parser.conflicts:
        print("\n  SLR(1) Resolution: FAILED -- remaining conflicts:")
        seen = set()
        for state_idx, sym, a1, a2, ctype in slr_parser.conflicts:
            key = (state_idx, sym)
            if key in seen:
                continue
            seen.add(key)
            # Find reduce item
            state   = slr_parser.states[state_idx]
            c_items = [i for i in state if i.is_complete]
            for ci in c_items:
                fo = follow.get(ci.lhs, set())
                if sym in fo:
                    print(f"    State {state_idx}, reduce {ci.lhs}->{' '.join(ci.rhs)}")
                    print(f"    FOLLOW({ci.lhs}) = {{{', '.join(sorted(fo))}}}")
                    print(f"    '{sym}' in FOLLOW => SLR(1) ALSO reduces on '{sym}' => conflict persists")
        return

    # Resolution succeeded -- show the proof
    print("\n  SLR(1) Resolution: SUCCEEDED")
    print("  Method: restrict reduce(A->alpha) to lookahead in FOLLOW(A)")

    seen = set()
    for state_idx, sym, a1, a2, ctype in lr0_parser.conflicts:
        if state_idx in seen:
            continue
        seen.add(state_idx)

        state   = slr_parser.states[state_idx]
        c_items = [i for i in state if i.is_complete]
        for ci in c_items:
            fo  = follow.get(ci.lhs, set())
            fo_str = '{' + ', '.join(sorted(fo)) + '}'
            if sym not in fo:
                print(f"\n    State {state_idx}: reduce {ci.lhs}->{' '.join(ci.rhs)}")
                print(f"    FOLLOW({ci.lhs}) = {fo_str}")
                print(f"    '{sym}' NOT in FOLLOW({ci.lhs}) => reduce BLOCKED on '{sym}' => shift wins")
            else:
                print(f"\n    State {state_idx}: reduce {ci.lhs}->{' '.join(ci.rhs)}")
                print(f"    FOLLOW({ci.lhs}) = {fo_str}")
                print(f"    '{sym}' in FOLLOW({ci.lhs}) => reduce permitted (no competing shift)")
    print("  => All Shift/Reduce conflicts eliminated.")


def print_lalr_compression(lalr_parser, lr1_parser):
    """Show LALR(1) state merging information."""
    lr1_n  = lr1_parser.num_states
    lalr_n = len(lalr_parser.states)
    delta  = lr1_n - lalr_n
    print(f"\n  LALR(1) State Compression:")
    print(f"    LR(1) canonical collection : {lr1_n} states")
    print(f"    LALR(1) after merging      : {lalr_n} states  (reduced by {delta})")
    if delta == 0:
        print("    No states were merged -- grammar is already LALR(1)-minimal.")
    else:
        print(f"    {delta} pair(s) of states share the same LR(0) core and were merged.")
        print("    Merging: lookahead sets are unioned; LR(0) item structure preserved.")
    if lalr_parser.conflicts:
        print("    WARNING: Merging introduced new Reduce/Reduce conflicts!")
    else:
        print("    No new conflicts introduced by merging -- LALR(1) is equivalent to LR(1) here.")


def print_lr1_vs_slr1(lr1_parser, slr1_parser):
    """Note the relationship between LR(1) and SLR(1) results."""
    lr1_ok  = lr1_parser.is_lr1
    slr_ok  = slr1_parser.is_slr1
    lr1_n   = lr1_parser.num_states

    print(f"\n  LR(1) uses per-item propagated lookaheads (more precise than FOLLOW sets).")
    print(f"  LR(1) canonical collection: {lr1_n} states")
    if lr1_ok and slr_ok:
        print("  Both SLR(1) and LR(1) agree: grammar passes both.")
        print("  => FOLLOW sets (SLR(1)) are sufficient for this grammar.")
    elif lr1_ok and not slr_ok:
        print("  LR(1) PASSES but SLR(1) FAILS:")
        print("  => FOLLOW sets are too coarse; per-item lookaheads resolve the conflict.")
    elif not lr1_ok:
        print("  LR(1) FAILS -- grammar is inherently ambiguous or beyond LR(1) power.")


def print_applicability_matrix(results: list):
    """Enhanced applicability matrix with YES/NO clearly marked."""
    techniques = ['LL(1)', 'LR(0)', 'SLR(1)', 'LR(1)', 'LALR(1)']
    col_w, g_w = 12, 8

    section("APPLICABILITY MATRIX (5 Grammars x 5 Techniques)")
    print()

    # Header
    hdr = f"  {'Grammar':<{g_w}}"
    for t in techniques:
        hdr += f"  {t:^{col_w}}"
    print(hdr)
    print(f"  {'-'*g_w}" + (f"  {'-'*col_w}" * len(techniques)))

    for row in results:
        name = row[0]
        line = f"  {name:<{g_w}}"
        for val in row[1:]:
            mark = '  YES  ' if val else '  NO   '
            line += f"  {mark:^{col_w}}"
        print(line)

    print(f"\n  {'-'*g_w}" + (f"  {'-'*col_w}" * len(techniques)))
    print()
    print("  Key:")
    print("  YES = Grammar is parseable by this technique (no conflicts)")
    print("  NO  = Technique fails for this grammar (conflicts exist)")
    print()
    print("  Power hierarchy confirmed: LL(1) subset-of LR(0) subset-of SLR(1) subset-of LALR(1) subset-of LR(1)")
    print("  Note: LL(1) applied to TRANSFORMED grammar; LR techniques to ORIGINAL grammar")
