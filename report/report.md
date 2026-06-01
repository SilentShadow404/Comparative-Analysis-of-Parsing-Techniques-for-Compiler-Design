# CS-471 Compiler Construction
## Assignment: Comparative Analysis of Parsing Techniques
### University of Engineering and Technology, New Campus, Lahore
### Department of Computer Science

**Student:** [Your Name]  
**Roll No:** [Your Roll No]  
**Section:** [Your Section]  
**Submitted to:** [Instructor Name]  
**Date:** June 2026

---

## Table of Contents

1. [Introduction and Theoretical Framework](#1-introduction-and-theoretical-framework)
2. [Grammar-wise Analysis](#2-grammar-wise-analysis)
   - 2.1 [G1 — Boolean Expressions](#21-g1--boolean-expressions)
   - 2.2 [G2 — Dangling-Else (Inherently Ambiguous)](#22-g2--dangling-else)
   - 2.3 [G3 — Comma-Separated List](#23-g3--comma-separated-list)
   - 2.4 [G4 — Function Call with Arguments](#24-g4--function-call-with-arguments)
   - 2.5 [G5 — Statement List with Expressions](#25-g5--statement-list-with-expressions)
3. [Applicability Matrix (5 × 5)](#3-applicability-matrix-5--5)
4. [Conflict Analysis with Formal Proofs](#4-conflict-analysis-with-formal-proofs)
5. [Comparative Evaluation of Parsing Techniques](#5-comparative-evaluation-of-parsing-techniques)
6. [Technique Selection Justification per Grammar](#6-technique-selection-justification-per-grammar)
7. [Conclusion](#7-conclusion)

---

## 1. Introduction and Theoretical Framework

This report applies five deterministic parsing techniques to five context-free grammars (CFGs).
All conclusions are derived from first principles; every PASS/FAIL verdict is justified by a
formal condition check, not by description.

### 1.1 Parsing Technique Summary

| Technique | Class       | Lookahead at Reduce         | Parse Table Size  |
|-----------|-------------|-----------------------------|--------------------|
| LL(1)     | Top-down    | FIRST / FOLLOW sets         | \|NT\| × \|T\|     |
| LR(0)     | Bottom-up   | None (reduce on **all** terminals) | Small       |
| SLR(1)    | Bottom-up   | FOLLOW(A) per nonterminal   | Same as LR(0)      |
| LR(1)     | Bottom-up   | Per-item lookahead sets     | Can be exponential |
| LALR(1)   | Bottom-up   | Merged LR(1) lookaheads     | Same states as LR(0) |

### 1.2 Parsing Power Hierarchy

The following inclusion chain is **strict** (each inclusion is proper):

```
LL(1)  ⊂  LR(0)  ⊂  SLR(1)  ⊂  LALR(1)  ⊂  LR(1)
```

Proof of strictness (one counterexample per inclusion):

- **LL(1) ⊂ LR(0)**: `A -> A a | b` is LR(0) but not LL(1) (left-recursive).
- **LR(0) ⊂ SLR(1)**: Any grammar with an eps-production (e.g., G4, G5) may be SLR(1) but not LR(0), because the eps-production creates a reduce item in a state that also has shift items; SLR resolves via FOLLOW sets.
- **SLR(1) ⊂ LALR(1)**: Grammars exist where SLR(1) fails because FOLLOW(A) is too coarse (includes terminals from *unrelated* states) but LALR(1) per-state lookaheads resolve the conflict.
- **LALR(1) ⊂ LR(1)**: Merging LR(1) core-equivalent states can create Reduce/Reduce conflicts in LALR(1) that LR(1) handles without issue.

### 1.3 LL(1) Existence Conditions

A grammar G is LL(1) if and only if for every non-terminal A with productions A → α₁ | α₂ | ... | αₙ:

1. **Disjoint FIRST**: FIRST(αᵢ) ∩ FIRST(αⱼ) = ∅ for all i ≠ j
2. **FIRST/FOLLOW disjointness**: If eps ∈ FIRST(αᵢ), then FIRST(αᵢ) ∩ FOLLOW(A) = ∅

Equivalently: the LL(1) parse table contains no cell with two entries.

### 1.4 LR(k) Existence Conditions

- **LR(0)**: The LR(0) automaton has no state containing both a *complete* item `[A → α •]` and any other item (shift or reduce). No lookahead.
- **SLR(1)**: For every complete item `[A → α •]` in state s, and every shift item `[B → β • a γ]` in s: a ∉ FOLLOW(A). If satisfied for all states: SLR(1) ⊆ grammar.
- **LR(1)**: Each item carries an explicit lookahead. Conflict-free iff no state has two items `[A → α •, a]` and `[B → β • a γ, b]` for the same terminal a.
- **LALR(1)**: Merge LR(1) states with identical cores. Conflict-free iff merging introduces no new Reduce/Reduce conflicts.

---

## 2. Grammar-wise Analysis

---

### 2.1 G1 — Boolean Expressions

#### Original Grammar G1

```
B  ->  B or T  |  T          (start symbol)
T  ->  T and F  |  F
F  ->  true  |  false  |  id
```

Terminals: `{ true, false, id, or, and }`

#### Structural Properties (G1)

| Property          | Status | Evidence                                              |
|-------------------|--------|-------------------------------------------------------|
| Left Recursion    | YES    | B → B or T (direct); T → T and F (direct)            |
| Common Prefixes   | NO     | Each alternative has a distinct first symbol          |
| Ambiguity         | NO     | Operator precedence encoded structurally: F < T < B   |
| Nullable NTs      | NO     | No production derives eps                             |

The grammar is unambiguous: `and` binds tighter than `or` because T is a strict sub-grammar of B.

#### Transformation Applied: Left-Recursion Removal

General rule: `A → A α | β` ⟹ `A → β A'`, `A' → α A' | eps`

Applied to B and T:

| Before                   | After                                          |
|--------------------------|------------------------------------------------|
| `B → B or T \| T`        | `B → T B'` ; `B' → or T B' \| eps`            |
| `T → T and F \| F`       | `T → F T'` ; `T' → and F T' \| eps`           |
| `F → true \| false \| id` | unchanged                                     |

#### Transformed Grammar G1T

```
B   ->  T B'
B'  ->  or T B'  |  eps
T   ->  F T'
T'  ->  and F T'  |  eps
F   ->  true  |  false  |  id
```

#### FIRST and FOLLOW Sets (G1T)

| NT  | FIRST                    | FOLLOW       |
|-----|--------------------------|--------------|
| B   | { false, id, true }      | { $ }        |
| B'  | { or, **eps** }          | { $ }        |
| T   | { false, id, true }      | { $, or }    |
| T'  | { and, **eps** }         | { $, or }    |
| F   | { false, id, true }      | { $, and, or }|

**Derivation of key FOLLOW sets:**
- FOLLOW(B) = {$} (B is start symbol)
- FOLLOW(B') = FOLLOW(B) = {$} (B' appears at end of B → T **B'**)
- FOLLOW(T) = FIRST(B') \ {eps} ∪ FOLLOW(B) = {or} ∪ {$} = {$, or}
- FOLLOW(T') = FOLLOW(T) = {$, or}
- FOLLOW(F) = FIRST(T') \ {eps} ∪ FOLLOW(T) = {and} ∪ {$, or} = {$, and, or}

#### LL(1) Condition Verification (G1T)

For each NT with multiple productions:

**B' → or T B' | eps**
- FIRST(or T B') = {or}
- FIRST(eps) ∪ FOLLOW(B') = {$}
- {or} ∩ {$} = ∅ ✓

**T' → and F T' | eps**
- FIRST(and F T') = {and}
- FIRST(eps) ∪ FOLLOW(T') = {$, or}
- {and} ∩ {$, or} = ∅ ✓

**F → true | false | id**
- FIRST sets are singletons; mutually disjoint ✓

**Conclusion: G1T IS LL(1).** No cell in the parse table has two entries.

#### LL(1) Parse Table (G1T, partial — conflict-relevant columns)

|    | $       | and          | false    | id      | or           | true    |
|----|---------|--------------|----------|---------|--------------|---------|
| B  |         |              | B→T B'   | B→T B'  |              | B→T B'  |
| B' | B'→eps  |              |          |         | B'→or T B'   |         |
| T  |         |              | T→F T'   | T→F T'  |              | T→F T'  |
| T' | T'→eps  | T'→and F T'  |          |         | T'→eps       |         |
| F  |         |              | F→false  | F→id    |              | F→true  |

#### LR Technique Verdicts (G1)

| Technique | Verdict | Reason                                                       |
|-----------|---------|--------------------------------------------------------------|
| LL(1)     | **PASS**  | All LL(1) conditions satisfied on G1T (see above)          |
| LR(0)     | **FAIL**  | State 4: {B→T•, T→T•and F} — S/R on 'and'                 |
| SLR(1)    | **PASS**  | 'and' ∉ FOLLOW(B) = {$,or} ⟹ reduce B→T blocked           |
| LR(1)     | **PASS**  | Per-item lookaheads eliminate all conflicts                  |
| LALR(1)   | **PASS**  | LALR merges LR(1) states; no R/R conflicts introduced        |

**LR(0) conflict proof:**
```
State 4:  B → T •          ← complete: reduce B→T on ALL terminals (LR(0) rule)
          T → T • and F    ← shift on 'and'
⟹ S/R conflict on 'and': reduce B→T  vs  shift 'and'
```

**SLR(1) resolution proof:**
```
FOLLOW(B) = { $, or }
'and' ∉ { $, or }
⟹ Action[state 4, 'and'] = shift  (reduce blocked)
⟹ NO CONFLICT  QED
```

#### Sample Parse Tree (G1T — input: `true and false or id`)

```
B
├── T
│   ├── F  →  "true"
│   └── T'
│       ├── "and"
│       ├── F  →  "false"
│       └── T'  →  ε
└── B'
    ├── "or"
    ├── T
    │   ├── F  →  "id"
    │   └── T'  →  ε
    └── B'  →  ε
```

Operator precedence is structurally encoded: `and` groups `true` and `false` under T before `or` combines at the B level. Exactly one parse tree exists — the grammar is unambiguous.

#### LL(1) Parse Trace (G1T — input: `true and false or id`)

| Step | Stack (top→right) | Input Remaining | Action |
|------|-------------------|-----------------|--------|
| 1 | `$ B` | `true and false or id $` | Predict B → T B' |
| 2 | `$ B' T` | `true and false or id $` | Predict T → F T' |
| 3 | `$ B' T' F` | `true and false or id $` | Predict F → true |
| 4 | `$ B' T' true` | `true and false or id $` | Match **true** |
| 5 | `$ B' T'` | `and false or id $` | Predict T' → and F T' |
| 6 | `$ B' T' F and` | `and false or id $` | Match **and** |
| 7 | `$ B' T' F` | `false or id $` | Predict F → false |
| 8 | `$ B' T' false` | `false or id $` | Match **false** |
| 9 | `$ B' T'` | `or id $` | Predict T' → ε |
| 10 | `$ B'` | `or id $` | Predict B' → or T B' |
| 11 | `$ B' T or` | `or id $` | Match **or** |
| 12 | `$ B' T` | `id $` | Predict T → F T' |
| 13 | `$ B' T' F` | `id $` | Predict F → id |
| 14 | `$ B' T' id` | `id $` | Match **id** |
| 15 | `$ B' T'` | `$` | Predict T' → ε |
| 16 | `$ B'` | `$` | Predict B' → ε |
| 17 | `$` | `$` | **Accept** |

---

### 2.2 G2 — Dangling-Else

#### Original Grammar G2

```
S  ->  i E t S e S  |  i E t S  |  a
E  ->  b
```

Terminals: `{ i (if), t (then), e (else), a (stmt), b (bool-expr) }`

#### Structural Properties (G2)

| Property          | Status | Evidence                                                       |
|-------------------|--------|----------------------------------------------------------------|
| Left Recursion    | NO     | No production is left-recursive                               |
| Common Prefixes   | YES    | S: prefix `i E t S` shared by two productions                 |
| **Ambiguity**     | **YES**| Two distinct parse trees for `i b t i b t a e a` (see below)  |
| Nullable NTs      | NO     | No production derives eps                                      |

#### Ambiguity Proof

Input: `i b t i b t a e a`

**Parse Tree 1** — else matches **outer** if:
```
S → i E t [S₁: i E t a] e [S₂: a]
```

**Parse Tree 2** — else matches **inner** if (C/Java convention):
```
S → i E t [S₁: i E t a e a]
```

Both trees are valid derivations under G2. Since a single string has two structurally distinct parse trees, G2 is **inherently ambiguous**. This ambiguity **cannot be removed** by grammar transformation.

#### Transformation: Left-Factoring

Common prefix `i E t S` factored out:

```
S   ->  i E t S S'  |  a
S'  ->  e S  |  eps
E   ->  b
```

#### FIRST and FOLLOW Sets (G2T)

| NT | FIRST      | FOLLOW      |
|----|------------|-------------|
| S  | { a, i }   | { $, e }    |
| S' | { e, eps } | { $, e }    |
| E  | { b }      | { t }       |

**Derivation:**
- FOLLOW(S) = {$} ∪ FIRST(S') \ {eps} ∪ FOLLOW(S') ... note S' can derive eps, so FOLLOW(S) also includes FOLLOW(S) — circular, resolved as: FOLLOW(S) = {$, e}
- FOLLOW(S') = FOLLOW(S) = {$, e}

#### LL(1) Conflict

At cell (S', 'e'):
- Production `S' → e S`: e ∈ FIRST(e S) = {e}
- Production `S' → eps`: e ∈ FOLLOW(S') = {$, e}
- {e} ∩ {e} = **{e} ≠ ∅**

**Conclusion: G2T IS NOT LL(1).** The dangling-else ambiguity manifests as a FIRST/FOLLOW intersection.

#### LR(0) Conflict

```
State 7:  S → i E t S •          ← complete: reduce S→i E t S on ALL terminals
          S → i E t S • e S      ← shift on 'e'
⟹ S/R conflict on 'e': reduce S→i E t S  vs  shift 'e'
```

#### SLR(1) Analysis

FOLLOW(S) = {$, e}.  
When lookahead = 'e': reduce S→i E t S requires e ∈ FOLLOW(S) = {$, e} — **e ∈ FOLLOW(S)**.  
Shift 'e' also wants 'e'.  
**S/R conflict persists.** SLR(1) FAILS.

**Root cause**: The inherent ambiguity guarantees that for any grammar equivalent to G2, any deterministic parser will have an unresolvable conflict.

#### LR Technique Verdicts (G2)

| Technique | Verdict | Reason                                                              |
|-----------|---------|---------------------------------------------------------------------|
| LL(1)     | **FAIL**  | FIRST(eS) ∩ FOLLOW(S') = {e} ≠ ∅ at cell (S', 'e')             |
| LR(0)     | **FAIL**  | State 7: S→i E t S• vs S→i E t S•e S — S/R on 'e'              |
| SLR(1)    | **FAIL**  | 'e' ∈ FOLLOW(S) = {$,e} ⟹ reduce S→i E t S also fires on 'e'   |
| LR(1)     | **FAIL**  | Per-item lookaheads include 'e' in both shift and reduce items     |
| LALR(1)   | **FAIL*** | *With "prefer shift" disambiguation: reports S/R, resolves to shift|

**Disambiguation**: The "prefer shift over reduce on 'e'" convention (standard in C/Java) corresponds to Tree 2, i.e., else matches the nearest unmatched if. This is implemented as a tie-breaking rule in LALR(1) generators (Bison, YACC).

#### Parse Tree Diagrams — Ambiguity Illustration (G2 — input: `i b t i b t a e a`)

**Parse Tree 1** — else matches the **outer** if (non-standard):

```
S
├── i
├── E  →  b
├── t
├── S  (inner if — no else)
│   ├── i
│   ├── E  →  b
│   ├── t
│   └── S  →  a
├── e
└── S  →  a
```

**Parse Tree 2** — else matches the **inner** if (C/Java convention, selected by "prefer shift"):

```
S
├── i
├── E  →  b
├── t
└── S
    ├── i
    ├── E  →  b
    ├── t
    ├── S  →  a
    ├── e
    └── S  →  a
```

Both trees derive the identical token sequence from the same start symbol S. Since one input string produces two structurally distinct parse trees, the grammar is **inherently ambiguous**. No grammar transformation can remove this ambiguity while preserving the language.

---

### 2.3 G3 — Comma-Separated List

#### Original Grammar G3

```
L  ->  L , id  |  id
```

Terminals: `{ id, ',' }`

#### Structural Properties (G3)

| Property        | Status | Evidence                              |
|-----------------|--------|---------------------------------------|
| Left Recursion  | YES    | L → L , id (direct)                  |
| Common Prefixes | NO     |                                       |
| Ambiguity       | NO     | Unique derivation for every list       |
| Nullable NTs    | NO     |                                        |

#### Transformed Grammar G3T

```
L   ->  id L'
L'  ->  , id L'  |  eps
```

#### FIRST and FOLLOW Sets (G3T)

| NT | FIRST          | FOLLOW |
|----|----------------|--------|
| L  | { id }         | { $ }  |
| L' | { ',', eps }   | { $ }  |

#### LL(1) Condition Verification (G3T)

**L' → , id L' | eps**
- FIRST(, id L') = { ',' }
- FIRST(eps) ∪ FOLLOW(L') = { $ }
- { ',' } ∩ { $ } = ∅ ✓

**Conclusion: G3T IS LL(1).**

#### LR(0) Analysis (Original G3)

The LR(0) automaton for G3 has **5 states**, **no conflicts**. Key observation:

```
State I₃ (reached after shifting L then seeing ','):
  L → L , • id      ← shift 'id'
  (no complete items)
⟹ Deterministic shift.
```

The only reduce state contains `L → id •` or `L → L , id •` — each is the sole item in its state, so no S/R or R/R conflicts arise.

**LR(0) PASSES directly on the original grammar.**

#### LR Technique Verdicts (G3)

| Technique | Verdict | Reason                                                  |
|-----------|---------|----------------------------------------------------------|
| LL(1)     | **PASS**  | All LL(1) conditions satisfied on G3T                  |
| LR(0)     | **PASS**  | No conflict in 5-state automaton                        |
| SLR(1)    | **PASS**  | LR(0) already conflict-free; SLR trivially passes       |
| LR(1)     | **PASS**  | LR(0) passes ⟹ LR(1) passes (LR(0) ⊂ LR(1))           |
| LALR(1)   | **PASS**  | No LR(1) states to merge; passes trivially              |

#### LR(0) Shift/Reduce Trace (G3 — input: `id , id`)

| Step | Stack | Input Remaining | Action |
|------|-------|-----------------|--------|
| 1 | `0` | `id , id $` | Shift **id** → state 2 |
| 2 | `0 id[2]` | `, id $` | Reduce L → id; GOTO L[0] → state 1 |
| 3 | `0 L[1]` | `, id $` | Shift **,** → state 3 |
| 4 | `0 L[1] ,[3]` | `id $` | Shift **id** → state 4 |
| 5 | `0 L[1] ,[3] id[4]` | `$` | Reduce L → L , id; GOTO L[0] → state 1 |
| 6 | `0 L[1]` | `$` | **Accept** |

Each reduce state contains exactly one complete item with no competing shift item on the same terminal — confirming zero conflicts across all 5 LR(0) states.

#### Parse Tree (G3 — input: `id , id , id`)

```
L
├── L
│   ├── L
│   │   └── id
│   ├── ","
│   └── id
├── ","
└── id
```

Left-associative structure: each `,` binds the accumulated list on the left with the next `id` on the right, matching the original left-recursive grammar.

---

### 2.4 G4 — Function Call with Arguments

#### Original Grammar G4

```
S     ->  id ( Args )
Args  ->  Args , id  |  id  |  eps
```

Terminals: `{ id, '(', ')', ',' }`

#### Structural Properties (G4)

| Property        | Status | Evidence                                        |
|-----------------|--------|-------------------------------------------------|
| Left Recursion  | YES    | Args → Args , id (direct)                      |
| Common Prefixes | NO     |                                                  |
| Ambiguity       | NO     | Unique parse for every function call             |
| Nullable NTs    | YES    | Args →* eps                                     |

#### Transformed Grammar G4T

```
S      ->  id ( Args )
Args   ->  id Args'  |  eps
Args'  ->  , id Args'  |  eps
```

#### FIRST and FOLLOW Sets (G4T)

| NT    | FIRST             | FOLLOW       |
|-------|-------------------|--------------|
| S     | { id }            | { $ }        |
| Args  | { id, **eps** }   | { ')' }      |
| Args' | { ',', **eps** }  | { ')' }      |

**Note:** FOLLOW(Args) is derived from S → id ( **Args** ) → ')' follows Args.

#### LL(1) Condition Verification (G4T)

**Args → id Args' | eps**
- FIRST(id Args') = { id }
- FIRST(eps) ∪ FOLLOW(Args) = { ')' }
- { id } ∩ { ')' } = ∅ ✓

**Args' → , id Args' | eps**
- FIRST(, id Args') = { ',' }
- FIRST(eps) ∪ FOLLOW(Args') = { ')' }
- { ',' } ∩ { ')' } = ∅ ✓

**Conclusion: G4T IS LL(1).**

#### LR(0) Conflict (Original G4)

```
State 3:  S    → id ( • Args )     ← goto on Args
          Args → •                  ← COMPLETE: reduce Args→eps on ALL terminals
          Args → • Args , id        ← goto on Args
          Args → • id               ← shift 'id'
⟹ S/R conflict on 'id': reduce Args→eps  vs  shift Args→id
```

#### SLR(1) Resolution

```
FOLLOW(Args) = { ')', ',' }
'id' ∉ { ')', ',' }
⟹ reduce Args→eps blocked when lookahead = 'id'
⟹ Action[state 3, 'id'] = shift   QED — no conflict
```

#### LR Technique Verdicts (G4)

| Technique | Verdict | Reason                                                     |
|-----------|---------|-------------------------------------------------------------|
| LL(1)     | **PASS**  | All LL(1) conditions satisfied on G4T                    |
| LR(0)     | **FAIL**  | State 3: {Args→eps•} vs {Args→•id} — S/R on 'id'         |
| SLR(1)    | **PASS**  | 'id' ∉ FOLLOW(Args)={),','} ⟹ reduce blocked             |
| LR(1)     | **PASS**  | Per-item lookaheads on Args→eps are {')',','} only         |
| LALR(1)   | **PASS**  | No R/R conflicts on merging LR(1) states                  |

#### Sample LL(1) Parse Trace (G4T — input: `id ( id , id )`)

| Step | Stack (top→right) | Input Remaining | Action |
|------|-------------------|-----------------|--------|
| 1 | `$ S` | `id ( id , id ) $` | Predict S → id ( Args ) |
| 2 | `$ ) Args ( id` | `id ( id , id ) $` | Match **id** |
| 3 | `$ ) Args (` | `( id , id ) $` | Match **(** |
| 4 | `$ ) Args` | `id , id ) $` | Predict Args → id Args' |
| 5 | `$ ) Args' id` | `id , id ) $` | Match **id** |
| 6 | `$ ) Args'` | `, id ) $` | Predict Args' → , id Args' |
| 7 | `$ ) Args' id ,` | `, id ) $` | Match **,** |
| 8 | `$ ) Args' id` | `id ) $` | Match **id** |
| 9 | `$ ) Args'` | `) $` | Predict Args' → ε |
| 10 | `$ )` | `) $` | Match **)** |
| 11 | `$` | `$` | **Accept** |

#### Parse Tree (G4T — input: `id ( id , id )`)

```
S
├── "id"   (function name)
├── "("
├── Args
│   ├── "id"   (first argument)
│   └── Args'
│       ├── ","
│       ├── "id"   (second argument)
│       └── Args'  →  ε
└── ")"
```

At step 9, lookahead `)` triggers `Args' → ε` because `)' ∈ FOLLOW(Args') = {`)`}`. This is the state where LR(0) would have incorrectly reduced `Args → eps` on `id` — confirming the SLR(1) resolution is necessary and correct.

---

### 2.5 G5 — Statement List with Arithmetic Expressions

#### Original Grammar G5

```
S          ->  StmtList
StmtList   ->  Stmt StmtList  |  eps
Stmt       ->  id = E ;
E          ->  E + T  |  T
T          ->  id  |  num
```

Terminals: `{ id, num, '=', '+', ';' }`

#### Structural Properties (G5)

| Property        | Status | Evidence                                            |
|-----------------|--------|-----------------------------------------------------|
| Left Recursion  | YES    | E → E + T (direct)                                 |
| Common Prefixes | NO     |                                                      |
| Ambiguity       | NO     | Unique derivation for every statement and expression |
| Nullable NTs    | YES    | StmtList →* eps                                     |

#### Transformed Grammar G5T

Left-recursion in E removed:

```
S          ->  StmtList
StmtList   ->  Stmt StmtList  |  eps
Stmt       ->  id = E ;
E          ->  T E'
E'         ->  + T E'  |  eps
T          ->  id  |  num
```

#### FIRST and FOLLOW Sets (G5T)

| NT        | FIRST                    | FOLLOW       |
|-----------|--------------------------|--------------|
| S         | { id, **eps** }          | { $ }        |
| StmtList  | { id, **eps** }          | { $ }        |
| Stmt      | { id }                   | { $, id }    |
| E         | { id, num }              | { ';' }      |
| E'        | { '+', **eps** }         | { ';' }      |
| T         | { id, num }              | { '+', ';' } |

#### LL(1) Condition Verification (G5T)

**StmtList → Stmt StmtList | eps**
- FIRST(Stmt StmtList) = FIRST(Stmt) = { id }
- FIRST(eps) ∪ FOLLOW(StmtList) = { $ }
- { id } ∩ { $ } = ∅ ✓

**E' → + T E' | eps**
- FIRST(+ T E') = { '+' }
- FIRST(eps) ∪ FOLLOW(E') = { ';' }
- { '+' } ∩ { ';' } = ∅ ✓

**Conclusion: G5T IS LL(1).**

#### LR(0) Conflicts (Original G5)

Two separate S/R conflicts in two states:

**State 0 (initial state):**
```
S'         → • S
S          → • StmtList
StmtList   → • Stmt StmtList
StmtList   → •              ← COMPLETE: reduce StmtList→eps on ALL terminals
Stmt       → • id = E ;     ← shift 'id'
⟹ S/R on 'id': reduce StmtList→eps  vs  shift for Stmt
```

**State 2 (after recognizing Stmt):**
```
StmtList   → Stmt • StmtList
StmtList   → •               ← COMPLETE: reduce StmtList→eps on ALL terminals
Stmt       → • id = E ;      ← shift 'id'
⟹ S/R on 'id': same conflict (next statement vs. end-of-list)
```

#### SLR(1) Resolution

```
FOLLOW(StmtList) = { $ }
'id' ∉ { $ }
⟹ reduce StmtList→eps blocked when lookahead = 'id'
⟹ Action[state 0, 'id'] = shift   QED
⟹ Action[state 2, 'id'] = shift   QED
```

Both conflicts resolved identically. SLR(1) PASSES.

#### LR Technique Verdicts (G5)

| Technique | Verdict | Reason                                                          |
|-----------|---------|------------------------------------------------------------------|
| LL(1)     | **PASS**  | All LL(1) conditions satisfied on G5T                         |
| LR(0)     | **FAIL**  | States 0 & 2: StmtList→eps• vs Stmt→•id = E; — S/R on 'id'   |
| SLR(1)    | **PASS**  | 'id' ∉ FOLLOW(StmtList)={$} ⟹ reduce blocked in both states  |
| LR(1)     | **PASS**  | Per-item lookaheads on StmtList→eps are {$} only               |
| LALR(1)   | **PASS**  | No R/R conflicts on merging; 14 states                          |

#### Sample LL(1) Parse Trace (G5T — input: `id = id + num ;`)

| Step | Stack (top→right) | Input Remaining | Action |
|------|-------------------|-----------------|--------|
| 1 | `$ S` | `id = id + num ; $` | Predict S → StmtList |
| 2 | `$ StmtList` | `id = id + num ; $` | Predict StmtList → Stmt StmtList |
| 3 | `$ StmtList Stmt` | `id = id + num ; $` | Predict Stmt → id = E ; |
| 4 | `$ StmtList ; E = id` | `id = id + num ; $` | Match **id** |
| 5 | `$ StmtList ; E =` | `= id + num ; $` | Match **=** |
| 6 | `$ StmtList ; E` | `id + num ; $` | Predict E → T E' |
| 7 | `$ StmtList ; E' T` | `id + num ; $` | Predict T → id |
| 8 | `$ StmtList ; E' id` | `id + num ; $` | Match **id** |
| 9 | `$ StmtList ; E'` | `+ num ; $` | Predict E' → + T E' |
| 10 | `$ StmtList ; E' T +` | `+ num ; $` | Match **+** |
| 11 | `$ StmtList ; E' T` | `num ; $` | Predict T → num |
| 12 | `$ StmtList ; E' num` | `num ; $` | Match **num** |
| 13 | `$ StmtList ; E'` | `; $` | Predict E' → ε |
| 14 | `$ StmtList ;` | `; $` | Match **;** |
| 15 | `$ StmtList` | `$` | Predict StmtList → ε |
| 16 | `$` | `$` | **Accept** |

#### Parse Tree (G5T — input: `id = id + num ;`)

```
S
└── StmtList
    ├── Stmt
    │   ├── "id"   (variable)
    │   ├── "="
    │   ├── E
    │   │   ├── T  →  "id"
    │   │   └── E'
    │   │       ├── "+"
    │   │       ├── T  →  "num"
    │   │       └── E'  →  ε
    │   └── ";"
    └── StmtList  →  ε
```

At step 13, lookahead `;` triggers `E' → ε` because `;` ∈ FOLLOW(E') = {`;`}. At step 15, lookahead `$` triggers `StmtList → ε` because `$` ∈ FOLLOW(StmtList) = {`$`} — exactly the condition exploited by SLR(1) to resolve the conflict in the original grammar.

---

## 3. Applicability Matrix (5 × 5)

| Grammar | Description                | LL(1) | LR(0)  | SLR(1) | LR(1) | LALR(1) |
|---------|----------------------------|-------|--------|--------|-------|---------|
| G1      | Boolean Expressions        | YES   | **NO** | YES    | YES   | YES     |
| G2      | Dangling-Else (ambiguous)  | **NO**| **NO** | **NO** | **NO**| **NO**  |
| G3      | Comma-Separated List       | YES   | YES    | YES    | YES   | YES     |
| G4      | Function Call + Args       | YES   | **NO** | YES    | YES   | YES     |
| G5      | Statement List + Expr      | YES   | **NO** | YES    | YES   | YES     |

**State counts for LR automata:**

| Grammar | LR(0) states | LR(1) states | LALR(1) states |
|---------|-------------|-------------|----------------|
| G1      | 11          | 11          | 11             |
| G2      | 10          | 17          | 10             |
| G3      | 5           | 5           | 5              |
| G4      | 9           | 9           | 9              |
| G5      | 14          | 14          | 14             |

**Observation**: For G2, LR(1) has 17 states vs. 10 for LR(0)/LALR(1) — the extra states in LR(1) are required to track distinct lookaheads for the dangling-else ambiguity, yet even LR(1) cannot eliminate the conflict because it is inherent to the grammar, not to lookahead precision.

---

## 4. Conflict Analysis with Formal Proofs

### 4.1 G1 — LR(0) Shift/Reduce (Two States)

**State 4** — reached after recognizing a complete T starting a B:

```
Items:  B → T •           (complete — LR(0) reduces on ALL terminals)
        T → T • and F     (shift on 'and')

LR(0) table: Action[4, 'and'] = {reduce B→T, shift 'and'} — CONFLICT
```

**SLR(1) fix:**
```
reduce B→T only if lookahead ∈ FOLLOW(B) = { $, or }
'and' ∉ { $, or }  ⟹  Action[4, 'and'] = shift  ✓
```

**State 9** — reached after recognizing B or T (right end of `B → B or T`):

```
Items:  B → B or T •      (complete — LR(0) reduces on ALL terminals)
        T → T • and F     (shift on 'and')

LR(0) table: Action[9, 'and'] = {reduce B→B or T, shift 'and'} — CONFLICT
```

**SLR(1) fix:**
```
reduce B→B or T only if lookahead ∈ FOLLOW(B) = { $, or }
'and' ∉ { $, or }  ⟹  Action[9, 'and'] = shift  ✓
```

Both conflicts resolved by SLR(1). **G1 is SLR(1).**

---

### 4.2 G2 — Fundamental Ambiguity Conflict

**LR(0) State 7:**

```
Items:  S → i E t S •         (complete — reduce S→iEtS)
        S → i E t S • e S     (shift on 'e')

Action[7, 'e'] = { reduce S→iEtS, shift 'e' } — S/R CONFLICT
```

**SLR(1) attempt:**
```
reduce S→iEtS only if 'e' ∈ FOLLOW(S)
FOLLOW(S) = { $, e }
'e' ∈ { $, e }  ⟹  reduce is ALSO valid on 'e'
Shift is ALSO valid on 'e'
⟹  CONFLICT PERSISTS.  SLR(1) FAILS.
```

**LL(1) conflict:**
```
Cell (S', 'e'):
  S' → e S : 'e' ∈ FIRST(eS) = {e}
  S' → eps : 'e' ∈ FOLLOW(S') = {$, e}
  Overlap = {e} ≠ ∅  ⟹  TWO entries in cell (S', 'e').  LL(1) FAILS.
```

**Why all techniques fail:** The ambiguity is **inherent** — the language L(G2) itself has strings with multiple derivations. No transformation produces an unambiguous grammar for the same language. All deterministic parsers (which by definition require unique derivations) fail on inherently ambiguous grammars.

---

### 4.3 G4 — Epsilon-Production Conflict

**LR(0) State 3** (after recognizing `id` `(` in `S → id ( • Args )`):

```
Items:  S    → id ( • Args )      (goto on Args)
        Args → •                  (complete — reduce Args→eps on ALL terminals)
        Args → • Args , id        (goto on Args)
        Args → • id               (shift 'id')

Action[3, 'id'] = { reduce Args→eps, shift 'id' } — S/R CONFLICT
```

**SLR(1) fix:**
```
reduce Args→eps only if lookahead ∈ FOLLOW(Args) = { ')', ',' }
'id' ∉ { ')', ',' }  ⟹  Action[3, 'id'] = shift  ✓
```

**Formal reading:** An argument list starts only when the next token is ')' (empty args) or 'id' (first arg). Since 'id' shifts, `Args→eps` fires only at ')'.

---

### 4.4 G5 — Recursive List Epsilon-Production

**LR(0) States 0 and 2** (initial and post-Stmt):

```
Both states contain:
  StmtList → •          (complete — reduce StmtList→eps on ALL terminals)
  Stmt     → • id = E ; (shift 'id')

Action[s, 'id'] = { reduce StmtList→eps, shift 'id' } — S/R CONFLICT
```

**SLR(1) fix (identical for both states):**
```
reduce StmtList→eps only if lookahead ∈ FOLLOW(StmtList) = { $ }
'id' ∉ { $ }  ⟹  Action[s, 'id'] = shift  ✓
```

**Formal reading:** An empty statement list is only possible at end-of-input ($). Any 'id' token must be the start of a new statement.

---

## 5. Comparative Evaluation of Parsing Techniques

### 5.1 Power and Trade-offs

| Criterion            | LL(1)         | LR(0)    | SLR(1)     | LR(1)        | LALR(1)     |
|----------------------|---------------|----------|------------|--------------|-------------|
| Left recursion       | FAILS         | handles  | handles    | handles      | handles     |
| eps-productions      | YES (FOLLOW)  | FAILS    | YES        | YES          | YES         |
| Ambiguous grammars   | FAILS         | FAILS    | FAILS      | FAILS        | FAILS*      |
| Table size           | NT × T        | small    | small      | can be large | small       |
| Grammar transformation| required    | none     | none       | none         | none        |
| Error recovery       | easy (top-down)| hard   | hard       | hard         | hard        |
| Industry adoption    | ANTLR, handwritten | —   | limited    | rare         | GCC, Bison  |

\* LALR(1) with "prefer shift" disambiguation handles G2 practically but not formally.

### 5.2 LR(0) vs SLR(1)

Both use the **identical automaton** (same states, same transitions). The only difference is the reduce trigger:

- **LR(0)**: reduce `A → α •` on every terminal
- **SLR(1)**: reduce `A → α •` only when lookahead ∈ FOLLOW(A)

Cost: zero extra states. Benefit: eliminates all conflicts caused by shift terminals not in FOLLOW(A). For G1, G4, G5 in this assignment, this single upgrade resolves all LR(0) conflicts.

### 5.3 SLR(1) vs LALR(1)

SLR(1) uses a **single global FOLLOW set** per non-terminal, computed from the entire grammar. LALR(1) computes **per-state lookahead sets** by merging the lookaheads from core-equivalent LR(1) items. LALR(1) lookaheads are always a subset of SLR(1) FOLLOW sets, so LALR(1) is strictly stronger.

For this assignment's grammars, SLR(1) and LALR(1) produce identical verdicts (both pass G1, G3, G4, G5). This indicates the global FOLLOW sets are not too coarse for these particular grammars.

### 5.4 LALR(1) vs LR(1)

LALR(1) is constructed by merging LR(1) states that have the same **core** (same items ignoring lookaheads). This reduces the state count. For G2, LR(1) has 17 states vs. LALR(1)'s 10.

Risk: merging can create Reduce/Reduce conflicts that LR(1) did not have. For these five grammars, no R/R conflicts are introduced.

### 5.5 LL(1) vs LR-family

LL(1) parsers process the input **left-to-right** with **leftmost derivation**, constructing the parse tree top-down. They require:
1. No left recursion (must transform first)
2. No common prefixes (must left-factor)
3. Disjoint FIRST sets per production group

LR parsers are bottom-up and handle left recursion natively. However, LL(1) is:
- Easier to implement by hand (recursive descent)
- Easier to modify (add productions without regenerating tables)
- Produces better error messages (the stack is the expected parse context)

After transformation, LL(1) and SLR(1) accept exactly the same set of grammars among the five tested.

---

## 6. Technique Selection Justification per Grammar

### G1 — Boolean Expressions

**Recommended: SLR(1)**

- LR(0) FAILS: `'and' ∈ states{B→T•, T→T•and F}` creates S/R in states 4 and 9.
- SLR(1) RESOLVES: `'and' ∉ FOLLOW(B) = {$, or}` ⟹ reduce blocked ⟹ no conflict.
- LL(1) also valid after transformation; requires grammar rewriting.
- LR(1) = LALR(1) = SLR(1) for this grammar (no advantage to upgrading).
- **Conclusion**: SLR(1) is the minimum sufficient technique; no grammar rewriting needed.

### G2 — Dangling-Else

**Recommended: LALR(1) + "prefer shift" convention**

- No deterministic technique accepts G2 without disambiguation.
- All five techniques fail due to inherent ambiguity.
- Practical resolution: LALR(1) with "prefer shift on 'e'" selects the C/Java convention (else matches nearest if). This is the standard approach in all production compilers.
- Formal resolution: Replace S with `Matched → i E t Matched e Matched | a` and `Unmatched → i E t S | i E t Matched e Unmatched` — this produces an unambiguous grammar that is LALR(1).

### G3 — Comma-Separated List

**Recommended: LR(0)** (or LL(1) after transformation)

- LR(0) PASSES the original grammar directly — 5 states, zero conflicts.
- No grammar transformation needed for any LR technique.
- Simplest grammar in the set; LR(0) is the appropriate tool.

### G4 — Function Call with Arguments

**Recommended: SLR(1)**

- LR(0) FAILS: eps-production Args→eps creates S/R on 'id' in state 3.
- SLR(1) RESOLVES: `'id' ∉ FOLLOW(Args) = {')', ','}` ⟹ reduce blocked.
- Formal reading: an empty argument list is possible only before ')' or ',' — never before 'id'.
- LL(1) also valid on G4T; requires transformation.
- **Conclusion**: SLR(1) is minimum sufficient; no grammar rewriting needed.

### G5 — Statement List with Expressions

**Recommended: SLR(1) / LALR(1)**

- LR(0) FAILS: StmtList→eps in states 0 and 2 creates S/R on 'id'.
- SLR(1) RESOLVES: `'id' ∉ FOLLOW(StmtList) = {$}` ⟹ reduce blocked in both states.
- LALR(1) preferred for production compilers — better extensibility and future-proof against SLR(1) inadequacy if the grammar is extended.
- LL(1) valid on G5T; requires E left-recursion removal.

---

## 7. Conclusion

This report applied five parsing techniques to five context-free grammars. The key findings are:

1. **LR(0) fails whenever a grammar has an eps-production or left-recursive rules that create complete items alongside shift items in the same automaton state.** This affects G1, G4, and G5. G3 is the only grammar where LR(0) passes directly.

2. **SLR(1) resolves all LR(0) conflicts in G1, G4, and G5** by restricting reductions to the FOLLOW set of the reduced non-terminal. The FOLLOW sets are sufficiently precise for these grammars.

3. **G2 is inherently ambiguous.** All five techniques fail. The standard engineering solution (prefer shift) is not a formal resolution but a pragmatic disambiguation convention.

4. **LALR(1) and LR(1) produce identical parse tables for G1, G3, G4, and G5**, confirming that the grammars are not LALR-inadequate. LALR(1) with its compact state space is the industrial standard choice.

5. **LL(1) is viable for all non-ambiguous grammars after transformation.** The transformation cost (left-recursion removal + left-factoring) is justified when top-down parsing is preferred (hand-written parsers, better error messages).

6. **Formal power hierarchy**: LL(1) ⊂ LR(0) ⊂ SLR(1) ⊂ LALR(1) ⊂ LR(1). Each inclusion is strict. For the grammars in this assignment: G3 is LR(0); G1, G4, G5 are SLR(1) (not LR(0)); all non-ambiguous grammars are LALR(1) = LR(1).

---

*Report generated for CS-471 Compiler Construction, UET New Campus Lahore.*
