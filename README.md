# CS-471 Compiler Construction — Parsing Techniques Analysis
### UET Lahore

A complete Python implementation that constructs and compares five parsing techniques (LL(1), LR(0), SLR(1), LR(1), LALR(1)) across five context-free grammars, with full parse tables, conflict detection, and LL(1) parse traces.

---

## Project Structure

```
compiler_project/
├── main.py                 # Entry point — runs all 25 analyses
├── src/
│   ├── grammar.py          # Grammar engine (FIRST/FOLLOW/nullable, transforms)
│   ├── grammars.py         # G1–G5 original and transformed Grammar objects
│   ├── ll1.py              # LL(1) parse table builder + parse tracer
│   ├── lr_base.py          # Shared LR infrastructure (Item, closure, goto, canonical collection)
│   ├── lr0.py              # LR(0) ACTION/GOTO table builder
│   ├── slr1.py             # SLR(1) parser (reuses LR(0) automaton + FOLLOW sets)
│   ├── lr1.py              # Canonical LR(1) parser
│   ├── lalr1.py            # LALR(1) parser (merges LR(1) states by LR(0) core)
│   └── reporter.py         # All ASCII-safe print utilities
└── report/
    └── report.md           # Full academic report
```

---

## Grammars Analysed

| ID | Description              | Challenges                          |
|----|--------------------------|-------------------------------------|
| G1 | Boolean expressions      | Direct left recursion in B and T    |
| G2 | Dangling-else (if-then-else) | Inherent ambiguity               |
| G3 | Comma-separated id list  | Direct left recursion in L          |
| G4 | Function call with args  | Left recursion + epsilon-production |
| G5 | Statement list           | Left recursion (E) + epsilon (StmtList) |

---

## Techniques Implemented

| Technique | File       | Key Feature                                |
|-----------|------------|--------------------------------------------|
| LL(1)     | ll1.py     | Predictive parse table; top-down tracer    |
| LR(0)     | lr0.py     | Shift/reduce on all terminals (no lookahead) |
| SLR(1)    | slr1.py    | Reduce restricted to FOLLOW sets           |
| LR(1)     | lr1.py     | Per-item propagated lookaheads             |
| LALR(1)   | lalr1.py   | LR(1) states merged by LR(0) core         |

---

## Running the Project

**Requirements:** Python 3.10+, no external dependencies.

```bash
cd compiler_project
python main.py
```

Output covers:
1. **Part 1** — Grammar-wise analysis: properties, transformations, FIRST/FOLLOW tables for all 5 grammars
2. **Part 2** — Parse tables (LL(1) and all three LR variants) for each grammar
3. **Part 3** — Conflict identification and formal explanation
4. **Part 4** — Comparative evaluation and applicability summary table
5. **Part 5** — Sample LL(1) parse traces (G1, G3, G5)

---

## Quick Results Summary

```
+-------------+---------+---------+---------+---------+---------+
| Grammar     |  LL(1)  |  LR(0)  |  SLR(1) |  LR(1)  | LALR(1) |
+-------------+---------+---------+---------+---------+---------+
| G1 (bool)   |  YES*   |   NO    |   YES   |   YES   |   YES   |
| G2 (dangle) |   NO    |   NO    |   NO    |   NO    |   NO    |
| G3 (list)   |  YES*   |  YES    |   YES   |   YES   |   YES   |
| G4 (func)   |  YES*   |   NO    |   YES   |   YES   |   YES   |
| G5 (stmts)  |  YES*   |   NO    |   YES   |   YES   |   YES   |
+-------------+---------+---------+---------+---------+---------+
* After left-recursion removal / left-factoring
```

---

## Key Design Decisions

- **EPSILON** is represented as the string `'eps'` (ASCII-safe, avoids Windows cp1252 encoding issues).
- **EOF** marker is `'$'`.
- **LR(1) closure** uses a worklist + dict pattern (`core -> set_of_lookaheads`) to safely merge lookaheads without mutating the set during iteration.
- **LALR(1)** merges states by LR(0) core (items ignoring lookaheads), then rebuilds transitions on the compressed state set.
- All output is **strictly ASCII** for portability across terminal encodings.
