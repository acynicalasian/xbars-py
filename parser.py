import dictsearch
import re
from enum import Enum

class Rule:
    """
    Define a class to represent a phrase structure rule; non-terminal nodes take form XP -> X YP
    or XP -> X' YP, while terminal nodes take form X -> word. Constructions involving conjunctions
    form a parent node whose type is the same as its two constituents, i.e. X -> X conj X.
    """

    def __init__(self, root, lh, rh=None):
        self.root = root
        self.lh = lh
        self.rh = rh

class NTRule(Rule):
    def __init__(self, root, lh, rh=None, rh2=None):
        super().__init__(root, lh, rh)
        self.rh2 = rh2    # Ditransitive verbs; possibly for conjunction functions

class TRule(Rule):
    def __init__(self, root, lh):
        super().__init__(root, lh)
        
class Parser:
    """
    Parse an input sentence via left-corner parsing. Some notes about the parser output:
    
    > TP will be treated as the root domain of all non-Qs. CP will be treated
    as the root domain of questions.

    > ((wh-movement is targeted as a feature but not guaranteed)); other movements like
    topicalization, clefting, etc. will not be supported.

    > Syntactic rules that also rely on semantic content cannot be supported; the program will
    generate parses for verbs incorrectly used as ditransitives; PRO subjects in subject/object
    control structures cannot be represented; raising constructions will not properly demonstrate
    the EPP if it is implemented; (VP) ellipsis will not likely be supported

    > Lacking experience with gerund phrases, they will probably not be parsed.

    > I ((aim)) to demonstrate head movement from T to V, Aux to V, Aux to T, etc.

    > ((There may be issues distinguishing between genitive and object cases for pronouns))
    """
    
    # Populate each Parser instance with an initial list of PSRs.
    _rulelist = [
        # TP Rules
        NTRule("TP", "DP", "T'"), NTRule("TP", "CP", "T'"), NTRule("T'", "T", "VP"),
        # > Skip this rule for now; we're not sure if T to V and V to T will occur. There's also the
        # > problem of tense inflecting onto modals/auxiliaries.
        #     T -> V T
        #     T -> Aux T

        # CP Rules
        NTRule("CP", "C'"), NTRule("C'", "C", "TP"),
        # > Skip T to C movement unless we detect a question.

        # VP Rules
        # > These rules are going to be in a separate list; allow the parser to have surface
        # > structure and deep structure modes.
        #     VP -> V'
        #     VP -> CP V"
        #     VP -> t V'
        # > Skip these rules for now since we're not sure whether we'll implement T to V/V to T and
        # auxiliaries.
        #     V' -> T
        #     V' -> T DP PP   1. "gave a present to John"
        #     V' -> T TP
        #     V' -> T VP
        #     V' -> T DP CP   2. "told John that..."
        #     V' -> T DP DP   3. "gave John a present"       # This may not be the case, ask Nico
        #     V' -> V
        #     V' -> V DP PP   1.
        #     V' -> V TP
        #     V' -> V VP
        #     V' -> V DP CP   2.
        #     V' -> V DP DP   3.
        NTRule("VP", "VP", "PP"), NTRule("VP", "AdvP", "VP"), NTRule("VP", "NegP", "VP"),
        
                  
