"""
grammars.py — Definitions of G1–G5 (original and manually verified transformed variants).

Each grammar is provided as both an *original* Grammar object and a *transformed* one
(left-recursion removed + left-factored) suitable for LL(1) analysis.
"""

from src.grammar import Grammar, EPSILON

# ============================================================
# G1 — Boolean expression grammar (operator-precedence hierarchy)
#
# B → B or T | T
# T → T and F | F
# F → true | false | id
# ============================================================

G1 = Grammar("G1", [
    ("B", ["B", "or",  "T"]),
    ("B", ["T"]),
    ("T", ["T", "and", "F"]),
    ("T", ["F"]),
    ("F", ["true"]),
    ("F", ["false"]),
    ("F", ["id"]),
], start="B")

# G1 transformed: eliminate left recursion from B and T
#   B  → T B'
#   B' → or T B' | ε
#   T  → F T'
#   T' → and F T' | ε
#   F  → true | false | id
G1T = Grammar("G1 (transformed)", [
    ("B",  ["T",   "B'"]),
    ("B'", ["or",  "T", "B'"]),
    ("B'", [EPSILON]),
    ("T",  ["F",   "T'"]),
    ("T'", ["and", "F", "T'"]),
    ("T'", [EPSILON]),
    ("F",  ["true"]),
    ("F",  ["false"]),
    ("F",  ["id"]),
], start="B")

# ============================================================
# G2 — Dangling-else grammar (ambiguous)
#
# S → i E t S | i E t S e S | a
# E → b
# ============================================================

G2 = Grammar("G2 (dangling-else)", [
    ("S", ["i", "E", "t", "S", "e", "S"]),
    ("S", ["i", "E", "t", "S"]),
    ("S", ["a"]),
    ("E", ["b"]),
], start="S")

# G2 left-factored (common prefix 'i E t S'):
#   S  → i E t S S' | a
#   S' → e S | ε
#   E  → b
# NOTE: Still ambiguous after left-factoring — LL(1) conflict remains
# because FIRST(e S) ∩ FOLLOW(S') = {e} ≠ ∅
G2T = Grammar("G2 (left-factored)", [
    ("S",  ["i", "E", "t", "S", "S'"]),
    ("S",  ["a"]),
    ("S'", ["e", "S"]),
    ("S'", [EPSILON]),
    ("E",  ["b"]),
], start="S")

# ============================================================
# G3 — Comma-separated identifier list
#
# L → L , id | id
# ============================================================

G3 = Grammar("G3 (list grammar)", [
    ("L", ["L", ",", "id"]),
    ("L", ["id"]),
], start="L")

# G3 transformed: eliminate left recursion from L
#   L  → id L'
#   L' → , id L' | ε
G3T = Grammar("G3 (transformed)", [
    ("L",  ["id", "L'"]),
    ("L'", [",", "id", "L'"]),
    ("L'", [EPSILON]),
], start="L")

# ============================================================
# G4 — Function call with argument list
#
# S    → id ( Args )
# Args → Args , id | id | ε
# ============================================================

G4 = Grammar("G4 (function call)", [
    ("S",    ["id", "(", "Args", ")"]),
    ("Args", ["Args", ",", "id"]),
    ("Args", ["id"]),
    ("Args", [EPSILON]),
], start="S")

# G4 transformed: eliminate left recursion from Args
#   S     → id ( Args )
#   Args  → id Args' | ε
#   Args' → , id Args' | ε
G4T = Grammar("G4 (transformed)", [
    ("S",     ["id", "(", "Args", ")"]),
    ("Args",  ["id", "Args'"]),
    ("Args",  [EPSILON]),
    ("Args'", [",", "id", "Args'"]),
    ("Args'", [EPSILON]),
], start="S")

# ============================================================
# G5 — Mini assignment-language grammar
#
# S        → StmtList
# StmtList → Stmt StmtList | ε
# Stmt     → id = E ;
# E        → E + T | T
# T        → id | num
# ============================================================

G5 = Grammar("G5 (statement list)", [
    ("S",        ["StmtList"]),
    ("StmtList", ["Stmt", "StmtList"]),
    ("StmtList", [EPSILON]),
    ("Stmt",     ["id", "=", "E", ";"]),
    ("E",        ["E", "+", "T"]),
    ("E",        ["T"]),
    ("T",        ["id"]),
    ("T",        ["num"]),
], start="S")

# G5 transformed: eliminate left recursion from E
#   S        → StmtList
#   StmtList → Stmt StmtList | ε
#   Stmt     → id = E ;
#   E        → T E'
#   E'       → + T E' | ε
#   T        → id | num
G5T = Grammar("G5 (transformed)", [
    ("S",        ["StmtList"]),
    ("StmtList", ["Stmt", "StmtList"]),
    ("StmtList", [EPSILON]),
    ("Stmt",     ["id", "=", "E", ";"]),
    ("E",        ["T", "E'"]),
    ("E'",       ["+", "T", "E'"]),
    ("E'",       [EPSILON]),
    ("T",        ["id"]),
    ("T",        ["num"]),
], start="S")

# ============================================================
# Convenient collections
# ============================================================

GRAMMARS_ORIGINAL    = [G1, G2, G3, G4, G5]
GRAMMARS_TRANSFORMED = [G1T, G2T, G3T, G4T, G5T]
GRAMMAR_PAIRS        = list(zip(GRAMMARS_ORIGINAL, GRAMMARS_TRANSFORMED))
