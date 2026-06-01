
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.grammars import G1, G1T, G2, G2T, G3, G3T, G4, G4T, G5, G5T, GRAMMAR_PAIRS
from src.ll1    import LL1Parser
from src.lr0    import LR0Parser
from src.slr1   import SLR1Parser
from src.lr1    import LR1Parser
from src.lalr1  import LALR1Parser
from src.grammar import EPSILON, EOF
from src.reporter import (
    section, subsection, print_grammar, print_first_follow,
    print_ll1_table, print_lr_table, print_lr_states, print_parse_trace,
    big_header, grammar_header, technique_header, verdict_box,
    print_properties_table, print_ll1_formal, print_lr0_conflict_detail,
    print_slr1_resolution, print_lalr_compression, print_lr1_vs_slr1,
    print_applicability_matrix,
)


# ──────────────────────────────────────────────────────────────────────
#  Terminal / UI helpers
# ──────────────────────────────────────────────────────────────────────

def clr():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause(msg="  Press  Enter  to continue..."):
    print()
    print("  " + chr(0x2500) * 60)
    input(msg + " ")


def _w():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def _top(w):
    return "  " + chr(0x2554) + chr(0x2550) * (w - 4) + chr(0x2557)

def _bot(w):
    return "  " + chr(0x255A) + chr(0x2550) * (w - 4) + chr(0x255D)

def _mid(w):
    return "  " + chr(0x2560) + chr(0x2550) * (w - 4) + chr(0x2563)

def _vbar():
    return chr(0x2551)

def _thin():
    return "  " + chr(0x2500) * 62


def _center(text, w):
    inner = w - 4
    return "  " + _vbar() + text.center(inner) + _vbar()


def banner(lines, subtitle=None, w=None):
    w = w or min(_w(), 78)
    print()
    print(_top(w))
    for ln in lines:
        print(_center(ln, w))
    if subtitle:
        print(_mid(w))
        for ln in subtitle:
            print(_center(ln, w))
    print(_bot(w))
    print()


# ──────────────────────────────────────────────────────────────────────
#  Grammar metadata
# ──────────────────────────────────────────────────────────────────────

GRAMMAR_META = {
    'G1': {
        'title': 'Boolean Expressions',
        'desc':  'BOOLEAN EXPRESSION GRAMMAR',
        'transform_rule': "Left-Recursion Removal:  A -> A a | b  =>  A -> b A',  A' -> a A' | eps",
        'transform_detail': [
            "B -> B or T | T    =>    B -> T B',   B' -> or T B' | eps",
            "T -> T and F | F   =>    T -> F T',   T' -> and F T' | eps",
            'F unchanged',
        ],
        'ambiguity': 'No ambiguity -- operator precedence explicit in hierarchy (F, T, B).',
        'sample': ['true', 'and', 'false', 'or', 'id'],
    },
    'G2': {
        'title': 'Dangling-Else  (Ambiguous)',
        'desc':  'DANGLING-ELSE GRAMMAR  (inherently ambiguous)',
        'transform_rule': "Left-Factoring:  A -> a b1 | a b2  =>  A -> a A',  A' -> b1 | b2",
        'transform_detail': [
            "S -> i E t S e S | i E t S   =>   S -> i E t S S',   S' -> e S | eps",
            'E unchanged',
        ],
        'ambiguity': (
            'INHERENTLY AMBIGUOUS -- the dangling-else problem.\n'
            '  Input "i b t i b t a e a" admits two valid parse trees:\n'
            '  Tree 1: else -> OUTER if  =>  S -> i E t [S->i E t a] e a\n'
            '  Tree 2: else -> INNER if  =>  S -> i E t [S->i E t a e a]   (C convention)\n'
            '  Resolution: prefer-shift on e in LALR(1).'
        ),
        'sample': ['i', 'b', 't', 'i', 'b', 't', 'a', 'e', 'a'],
    },
    'G3': {
        'title': 'Comma-Separated ID List',
        'desc':  'COMMA-SEPARATED ID LIST',
        'transform_rule': "Left-Recursion Removal:  L -> L , id | id  =>  L -> id L',  L' -> , id L' | eps",
        'transform_detail': [
            "L -> L , id | id   =>   L -> id L',   L' -> , id L' | eps",
        ],
        'ambiguity': 'No ambiguity -- single unambiguous list structure.',
        'sample': ['id', ',', 'id', ',', 'id'],
    },
    'G4': {
        'title': 'Function Call with Arguments',
        'desc':  'FUNCTION CALL WITH ARGUMENTS',
        'transform_rule': 'Left-Recursion Removal + eps-production restructuring',
        'transform_detail': [
            'Args -> Args , id | id | eps',
            "  =>  Args -> id Args' | eps,   Args' -> , id Args' | eps",
            'S unchanged',
        ],
        'ambiguity': 'No ambiguity -- unique syntactic form for function call.',
        'sample': ['id', '(', 'id', ',', 'id', ')'],
    },
    'G5': {
        'title': 'Statement List with Arithmetic',
        'desc':  'STATEMENT LIST WITH ARITHMETIC EXPRESSIONS',
        'transform_rule': "Left-Recursion Removal (E):  E -> E + T | T  =>  E -> T E',  E' -> + T E' | eps",
        'transform_detail': [
            "E -> E + T | T   =>   E -> T E',   E' -> + T E' | eps",
            'StmtList -> Stmt StmtList | eps  (right-recursive, unchanged)',
            'Stmt, T, S unchanged',
        ],
        'ambiguity': 'No ambiguity -- unique derivation for each statement and expression.',
        'sample': ['id', '=', 'id', '+', 'num', ';'],
    },
}

GRAMMAR_LABELS   = ['G1', 'G2', 'G3', 'G4', 'G5']
_GRAMMAR_OBJECTS = [(G1, G1T), (G2, G2T), (G3, G3T), (G4, G4T), (G5, G5T)]


# ──────────────────────────────────────────────────────────────────────
#  Parser cache  (build once, reuse across menu selections)
# ──────────────────────────────────────────────────────────────────────

_cache = {}

def get_parsers(label):
    if label not in _cache:
        idx  = GRAMMAR_LABELS.index(label)
        orig, trans = _GRAMMAR_OBJECTS[idx]
        _cache[label] = {
            'orig':  orig,
            'trans': trans,
            'll1':   LL1Parser(trans),
            'lr0':   LR0Parser(orig),
            'slr':   SLR1Parser(orig),
            'lr1':   LR1Parser(orig),
            'lalr':  LALR1Parser(orig),
        }
    return _cache[label]


# ──────────────────────────────────────────────────────────────────────
#  Section renderers
# ──────────────────────────────────────────────────────────────────────

def show_original(p, label):
    section('[1]  ORIGINAL GRAMMAR')
    print_grammar(p['orig'])


def show_properties(p, label):
    meta = GRAMMAR_META[label]
    section('[2]  STRUCTURAL PROPERTIES ANALYSIS')
    print_properties_table(p['orig'])
    print()
    ambig = meta['ambiguity']
    for i, ln in enumerate(ambig.split('\n')):
        prefix = '  Ambiguity: ' if i == 0 else '  '
        print(prefix + ln)


def show_transformation(p, label):
    meta = GRAMMAR_META[label]
    section('[3]  GRAMMAR TRANSFORMATION')
    print('\n  Technique applied: ' + meta['transform_rule'])
    print()
    print('  Before / After:')
    for line in meta['transform_detail']:
        print('    ' + line)
    print()
    print('  Resulting transformed grammar:')
    print_grammar(p['trans'])


def show_first_follow(p, label):
    section('[4]  FIRST / FOLLOW SETS  (transformed grammar)')
    print_first_follow(p['trans'])


def show_ll1(p, label):
    technique_header(1, 'LL(1)', 'transformed grammar -- ' + p['trans'].name)
    print()
    print_ll1_table(p['ll1'])
    verdict_box(p['ll1'].is_ll1, 'LL(1)', len(p['ll1'].conflicts))
    print_ll1_formal(p['ll1'])


def show_lr0(p, label):
    technique_header(2, 'LR(0)', 'original grammar -- ' + p['orig'].name)
    print()
    print_lr_table(p['lr0'], 'LR(0) ACTION / GOTO Table')
    n = len(set((s, sym) for s, sym, *_ in p['lr0'].conflicts))
    verdict_box(p['lr0'].is_lr0, 'LR(0)', n)
    print_lr0_conflict_detail(p['lr0'])
    print()
    subsection('LR(0) Automaton Item Sets  --  ' + label)
    print_lr_states(p['lr0'], 'LR(0) ' + label, max_states=20)


def show_slr1(p, label):
    technique_header(3, 'SLR(1)', 'original grammar -- ' + p['orig'].name)
    print()
    print_lr_table(p['slr'], 'SLR(1) ACTION / GOTO Table')
    n = len(set((s, sym) for s, sym, *_ in p['slr'].conflicts))
    verdict_box(p['slr'].is_slr1, 'SLR(1)', n)
    print_slr1_resolution(p['slr'], p['lr0'])


def show_lr1(p, label):
    technique_header(4, 'LR(1)', 'original grammar -- ' + p['orig'].name)
    print()
    print_lr_table(p['lr1'], 'LR(1) ACTION / GOTO Table')
    n = len(set((s, sym) for s, sym, *_ in p['lr1'].conflicts))
    verdict_box(p['lr1'].is_lr1, 'LR(1)', n)
    print_lr1_vs_slr1(p['lr1'], p['slr'])


def show_lalr1(p, label):
    technique_header(5, 'LALR(1)', 'original grammar -- ' + p['orig'].name)
    print()
    print_lr_table(p['lalr'], 'LALR(1) ACTION / GOTO Table')
    n = len(set((s, sym) for s, sym, *_ in p['lalr'].conflicts))
    verdict_box(p['lalr'].is_lalr1, 'LALR(1)', n)
    print_lalr_compression(p['lalr'], p['lr1'])


def show_trace(p, label):
    meta   = GRAMMAR_META[label]
    tokens = meta['sample']
    section('[5]  SAMPLE PARSE TRACE  (LL(1) on transformed grammar)')
    print('\n  Input: ' + ' '.join(tokens))
    if p['ll1'].is_ll1:
        try:
            steps = p['ll1'].parse_trace(tokens)
            print_parse_trace(steps, title='LL(1) Trace -- ' + label)
        except Exception as e:
            print('  Parse error on sample input: ' + str(e))
    elif label == 'G2':
        _print_g2_ambiguity()
    else:
        print('  (grammar not LL(1) after transformation -- no trace available)')


def _print_g2_ambiguity():
    print()
    print('  G2 is INHERENTLY AMBIGUOUS -- two parse trees for the same input:')
    print()
    print('  INPUT: i b t i b t a e a')
    print()
    print('  PARSE TREE 1  (else -> outer if):')
    print('    S -> i E t S1 e S2    where S1 = [i E t a],  S2 = a')
    print()
    print('  PARSE TREE 2  (else -> inner if -- C/Java convention):')
    print('    S -> i E t S1          where S1 = [i E t a e a]')
    print()
    print('  Two structurally distinct parse trees for identical input = AMBIGUOUS.')
    print("  CONVENTION: Prefer shift over reduce on 'e' -> Tree 2 selected.")


def show_all_grammar(label):
    p    = get_parsers(label)
    meta = GRAMMAR_META[label]
    grammar_header(label, meta['desc'])
    show_original(p, label)
    show_properties(p, label)
    show_transformation(p, label)
    show_first_follow(p, label)
    print('\n\n  ' + '~' * 74)
    print('  TECHNIQUE EVALUATION -- All 5 techniques applied to Grammar ' + label)
    print('  ' + '~' * 74)
    show_ll1(p, label)
    show_lr0(p, label)
    show_slr1(p, label)
    show_lr1(p, label)
    show_lalr1(p, label)
    show_trace(p, label)


# ──────────────────────────────────────────────────────────────────────
#  Global views (matrix + comparative)
# ──────────────────────────────────────────────────────────────────────

def _build_results():
    rows = []
    for lbl in GRAMMAR_LABELS:
        p = get_parsers(lbl)
        rows.append((lbl,
                     p['ll1'].is_ll1,  p['lr0'].is_lr0,
                     p['slr'].is_slr1, p['lr1'].is_lr1,
                     p['lalr'].is_lalr1))
    return rows


def show_matrix():
    section('APPLICABILITY MATRIX  (5 Grammars x 5 Techniques)')
    print('  Building parsers for all grammars -- please wait...\n')
    rows = _build_results()
    print_applicability_matrix(rows)


def show_comparative():
    section('COMPARATIVE EVALUATION OF PARSING TECHNIQUES')

    print("""
  POWER HIERARCHY (each inclusion is STRICT):

    LL(1)  C  LR(0)  C  SLR(1)  C  LALR(1)  C  LR(1)

  Proof sketch:
    LL(1) C LR(0):    A -> A a | b  is LR(0) but NOT LL(1)  (left recursion).
    LR(0) C SLR(1):   G4 original is SLR(1) but NOT LR(0)  (eps S/R conflict).
    SLR(1) C LALR(1): FOLLOW sets too coarse in some grammars; LALR(1) uses
                      per-state lookaheads to resolve where SLR(1) cannot.
    LALR(1) C LR(1):  Merging LR(1) states can introduce R/R conflicts unseen
                      by full LR(1); LR(1) is strictly more powerful.""")

    print()
    print('  TECHNIQUE COMPARISON TABLE:')
    print()
    rows = [
        ('Technique',  'Reduce Trigger',       'State Count',        'eps', 'Industry Use'),
        ('---------',  '--------------',       '------------',       '----', '------------'),
        ('LL(1)',      'FIRST/FOLLOW predict',  '|NT| x |T|',         'YES', 'Recursive descent, ANTLR'),
        ('LR(0)',      'ALL terminals',         'Small',              'NO',  'Pedagogical only'),
        ('SLR(1)',     'FOLLOW(A)',              'Small (= LR(0))',    'YES', 'Simple compilers, YACC-SLR'),
        ('LR(1)',      'Per-item lookahead',    'Large (can explode)', 'YES', 'Rarely used in practice'),
        ('LALR(1)',    'Merged per-item LA',    'Medium (~LR(0))',     'YES', 'GCC, Bison, YACC'),
    ]
    col_w = [12, 22, 22, 5, 28]
    for row in rows:
        line = '  '
        for cell, cw in zip(row, col_w):
            line += (cell + ' ' * cw)[:cw]
        print(line)
    print()

    section('JUSTIFICATION: BEST TECHNIQUE PER GRAMMAR')
    jlist = [
        ('G1', 'SLR(1) or LL(1)',
         ['Left recursion in orig -> LR(0) fails (S/R conflict).',
          'SLR(1): FOLLOW(B)={$,or} -- "and" not in set => shift wins.',
          'LL(1) passes on transformed grammar (after left-recursion removal).']),
        ('G2', 'LALR(1) + prefer-shift',
         ['Inherently ambiguous -- all 5 techniques produce conflicts.',
          'LALR(1) + prefer-shift implements "else->nearest if" convention.']),
        ('G3', 'LR(0) or LL(1)',
         ['LR(0) passes on ORIGINAL grammar (no eps-production).',
          'LL(1) passes on transformed grammar.',
          'BEST: LR(0) -- no grammar transformation required.']),
        ('G4', 'SLR(1) or LL(1)',
         ['eps-production in Args -> LR(0) S/R on "id".',
          'SLR(1): FOLLOW(Args)={)} excludes "id" => shift wins. Conflict resolved.']),
        ('G5', 'SLR(1) or LALR(1)',
         ['Left recursion in E + eps in StmtList -> LR(0) fails on 2 conflicts.',
          'SLR(1) resolves both via FOLLOW sets.',
          'LALR(1) preferred for production use.']),
    ]
    for lbl, best, lines in jlist:
        print('\n  ' + lbl + '  --  Best: ' + best)
        print('  ' + '-' * 70)
        for ln in lines:
            print('    ' + ln)


# ──────────────────────────────────────────────────────────────────────
#  Menu drawing helpers
# ──────────────────────────────────────────────────────────────────────

def _vtag(flag):
    return 'PASS' if flag else 'FAIL'


def draw_main_menu():
    clr()
    w = min(_w(), 78)
    banner(
        ['COMPILER CONSTRUCTION',
         'Comparative Analysis of Parsing Techniques'],
        subtitle=[
            'University of Engineering & Technology  --  New Campus, Lahore',
            'Department of Computer Science',
            '5 Grammars   x   5 Techniques :  LL(1)  LR(0)  SLR(1)  LR(1)  LALR(1)',
        ],
        w=w,
    )
    print('  SELECT A GRAMMAR  or  a GLOBAL VIEW')
    print()
    print(_thin())
    grammars = [
        ('1', 'G1', 'Boolean Expressions'),
        ('2', 'G2', 'Dangling-Else  (Ambiguous)'),
        ('3', 'G3', 'Comma-Separated ID List'),
        ('4', 'G4', 'Function Call with Arguments'),
        ('5', 'G5', 'Statement List with Arithmetic'),
    ]
    for key, lbl, title in grammars:
        print('   [' + key + ']  ' + lbl + '  --  ' + title)
    print()
    print(_thin())
    print('   [6]  View All Grammars  (full analysis, all 5)')
    print('   [7]  Applicability Matrix')
    print('   [8]  Comparative Evaluation')
    print()
    print(_thin())
    print('   [0]  Exit')
    print()


def draw_grammar_menu(label):
    clr()
    meta = GRAMMAR_META[label]
    p    = get_parsers(label)
    w    = min(_w(), 78)

    banner(
        ['Grammar  ' + label + '  --  ' + meta['title']],
        subtitle=['Select a section to view  |  [B] Back to Main Menu'],
        w=w,
    )

    tags = [
        ('LL(1)',   p['ll1'].is_ll1),
        ('LR(0)',   p['lr0'].is_lr0),
        ('SLR(1)',  p['slr'].is_slr1),
        ('LR(1)',   p['lr1'].is_lr1),
        ('LALR(1)', p['lalr'].is_lalr1),
    ]
    parts = [k + ' ' + _vtag(v) for k, v in tags]
    print('  Status:  ' + '   '.join(parts))
    print()
    print(_thin())
    print('   [1]  Original Grammar')
    print('   [2]  Structural Properties Analysis')
    print('   [3]  Grammar Transformation')
    print('   [4]  FIRST / FOLLOW Sets')
    print()
    print(_thin())
    print('   [5]  LL(1)   Analysis')
    print('   [6]  LR(0)   Analysis')
    print('   [7]  SLR(1)  Analysis')
    print('   [8]  LR(1)   Analysis')
    print('   [9]  LALR(1) Analysis')
    print()
    print(_thin())
    print('   [T]  Sample Parse Trace  (LL(1))')
    print('   [A]  All  --  complete analysis of this grammar')
    print()
    print(_thin())
    print('   [B]  Back to Main Menu')
    print()


# ──────────────────────────────────────────────────────────────────────
#  Grammar sub-menu loop
# ──────────────────────────────────────────────────────────────────────

def grammar_menu(label):
    p    = get_parsers(label)
    meta = GRAMMAR_META[label]

    while True:
        draw_grammar_menu(label)
        choice = input('   Enter choice: ').strip().upper()

        if choice == '':
            continue
        if choice == 'B':
            return

        clr()
        if choice != 'A':
            grammar_header(label, meta['desc'])

        if   choice == '1':  show_original(p, label)
        elif choice == '2':  show_properties(p, label)
        elif choice == '3':  show_transformation(p, label)
        elif choice == '4':  show_first_follow(p, label)
        elif choice == '5':  show_ll1(p, label)
        elif choice == '6':  show_lr0(p, label)
        elif choice == '7':  show_slr1(p, label)
        elif choice == '8':  show_lr1(p, label)
        elif choice == '9':  show_lalr1(p, label)
        elif choice == 'T':  show_trace(p, label)
        elif choice == 'A':  show_all_grammar(label)
        else:
            print('   *** Invalid choice: ' + repr(choice) + '  -- try again ***')

        pause()


# ──────────────────────────────────────────────────────────────────────
#  Main menu loop
# ──────────────────────────────────────────────────────────────────────

def main():
    while True:
        draw_main_menu()
        choice = input('   Enter choice: ').strip().upper()

        if choice == '0':
            clr()
            banner(
                ['Thank you for using the Parsing Techniques Analyser'],
                subtitle=['Compiler Construction CCP'],
            )
            break

        elif choice in ('1', '2', '3', '4', '5'):
            grammar_menu('G' + choice)

        elif choice == '6':
            for lbl in GRAMMAR_LABELS:
                clr()
                show_all_grammar(lbl)
                pause('  Grammar ' + lbl + ' done -- Press Enter for next...')
            pause('  All grammars shown -- Press Enter to return to menu...')

        elif choice == '7':
            clr()
            show_matrix()
            pause()

        elif choice == '8':
            clr()
            show_comparative()
            pause()

        elif choice == '':
            continue

        else:
            draw_main_menu()
            print('   *** Invalid choice: ' + repr(choice) + '  -- try again ***')
            input('   Press Enter... ')


if __name__ == '__main__':
    main()
