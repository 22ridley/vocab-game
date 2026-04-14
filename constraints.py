from z3 import (EnumSort, Const, Solver, Implies, Not, sat, And, Function,
                ForAll, Or, BoolSort, Exists, IntSort, Int, Array, BoolVal, Sum, If)
import random

# Constants
MAX_ONSET     = 3
MAX_CODA      = 4 # Because we have x as one grapheme, so sixths is just 3 graphemes
MIN_SYLLABLES = 2 # To make things interesting
MAX_SYLLABLES = 3
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 8

Graphemes, (a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, qu, r, s, t, u, v, w, th, ch, sh, ph, ng, ck, tch, ea, ai, ou, oa, au) = \
    EnumSort('Letters', ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'l', 'm', 'n', 'o', 'p', 'qu', 'r',
                         's', 't', 'u', 'v', 'w', 'th', 'ch', 'sh', 'ph', 'ng', 'ck', 'tch', 'ea', 'ai', 'ou', 'oa', 'au'])
gr = Const('gr', Graphemes)

# -------------------------------------------------------------------------------------

# Classifier functions
is_vowel = Function('is_vowel',     Graphemes, BoolSort())
is_glide = Function('is_glide',     Graphemes, BoolSort())
is_liquid = Function('is_liquid',    Graphemes, BoolSort())
is_nasal = Function('is_nasal',     Graphemes, BoolSort())
is_fricative = Function('is_fricative', Graphemes, BoolSort())
is_affricate = Function('is_affricate', Graphemes, BoolSort())
is_stop = Function('is_stop',      Graphemes, BoolSort())
is_voiced = Function('is_voiced', Graphemes, BoolSort())
is_obstruent = Function('is_obstruent', Graphemes, BoolSort())
is_voiced_obstruent = Function('is_voiced_obstruent', Graphemes, BoolSort())
is_sonorant = Function('is_sonorant',  Graphemes, BoolSort())
is_consonant = Function('is_consonant', Graphemes, BoolSort())
is_coda_second_banned = Function('is_coda_second_banned', Graphemes, BoolSort())
is_alveolar = Function('is_alveolar', Graphemes, BoolSort())
is_bilabial = Function('is_bilabial', Graphemes, BoolSort())
is_velar = Function('is_velar', Graphemes, BoolSort())

all_graphemes = [a,b,c,d,e,f,g,h,i,j,l,m,n,o,p,qu,r,s,t,u,v,w,th,ch,sh,ph,ng,ck,tch,ea,ai,ou,oa,au]

def is_in_set(fn, members):
    """Assert fn(l) == True iff l is in `members`."""
    member_set = set(members)
    return [fn(l) == BoolVal(l in member_set) for l in all_graphemes]

# Phonological classes
VOWELS = [a, e, i, o, u, ea, ai, ou, oa, au]
GLIDES = [w]
LIQUIDS = [l, r]
NASALS = [m, n, ng]
FRICATIVES = [f, v, s, c, h, th, sh, ph]
AFFRICATES = [ch, j, tch]
STOPS = [b, d, g, p, t, ck, qu]
VOICED = [a, e, i, o, u, ea, ai, ou, oa, au, b, d, g, v, j, l, r, m, n, ng, w, th]
VOICED_OBSTRUENTS = [b, d, g, v, j]
CODA_SECOND_BANNED = [ng, th, r, sh]
ALVEOLARS = [t, d, s, n, l, r]
BILABIALS = [p, b, m]
VELARS = [g, ng, ck]

solver = Solver()
solver.add(is_in_set(is_vowel,     VOWELS))
solver.add(is_in_set(is_glide,     GLIDES))
solver.add(is_in_set(is_liquid,    LIQUIDS))
solver.add(is_in_set(is_nasal,     NASALS))
solver.add(is_in_set(is_fricative, FRICATIVES))
solver.add(is_in_set(is_affricate, AFFRICATES))
solver.add(is_in_set(is_stop,      STOPS))
solver.add(is_in_set(is_voiced_obstruent, VOICED_OBSTRUENTS))
solver.add(is_in_set(is_coda_second_banned, CODA_SECOND_BANNED))
solver.add(is_in_set(is_voiced, VOICED))
solver.add(is_in_set(is_alveolar, ALVEOLARS))
solver.add(is_in_set(is_bilabial, BILABIALS))
solver.add(is_in_set(is_velar,    VELARS))

# Obstruent = stop | fricative | affricate
solver.add(ForAll([gr], is_obstruent(gr) == Or(is_stop(gr), is_fricative(gr), is_affricate(gr))))
# Sonorant = vowel | glide | liquid | nasal
solver.add(ForAll([gr], is_sonorant(gr) == Or(is_vowel(gr), is_glide(gr), is_liquid(gr), is_nasal(gr))))
# Consonant = anything that isn't a vowel
solver.add(ForAll([gr], is_consonant(gr) == Not(is_vowel(gr))))

onset_letters  = Array('onset_letters',  IntSort(), Graphemes)
coda_letters   = Array('coda_letters',   IntSort(), Graphemes)
nucleus_letter = Array('nucleus_letter', IntSort(), Graphemes)
onset_length   = Array('onset_length',   IntSort(), IntSort())
coda_length    = Array('coda_length',    IntSort(), IntSort())
num_syllables  = Int('num_syllables')
s_idx = Int('s_idx')
c_idx = Int('c_idx')

# -------------------------------------------------------------------------------------

# OUR SYLLABLE-LEVEL RULES!

# Number of syllables in bounds
solver.add(num_syllables >= MIN_SYLLABLES)
solver.add(num_syllables <= MAX_SYLLABLES)

# Each syllable's onset/coda lengths are in bounds
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables),
    And(onset_length[s_idx] >= 0, onset_length[s_idx] <= MAX_ONSET,
        coda_length[s_idx]  >= 0, coda_length[s_idx]  <= MAX_CODA)
)))

# Nucleus must be a vowel
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables),
    is_vowel(nucleus_letter[s_idx])
)))

# Onset letters must be consonants
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx  >= 0, c_idx  < onset_length[s_idx]),
    is_consonant(onset_letters[s_idx * MAX_ONSET + c_idx])
)))

# Coda letters must be consonants
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx  >= 0, c_idx  < coda_length[s_idx]),
    is_consonant(coda_letters[s_idx * MAX_CODA + c_idx])
)))

word = Array('word', IntSort(), Graphemes)
word_length = Int('word_length')

# Word length = sum of all syllable lengths
solver.add(word_length == Sum([
    If(syl < num_syllables, onset_length[syl] + 1 + coda_length[syl], 0)
    for syl in range(MAX_SYLLABLES)
]))

# Assert that the flat word array matches the syllable structure
for syl in range(MAX_SYLLABLES):
    # Start position of this syllable in the flat word array
    start = Sum([onset_length[s2] + 1 + coda_length[s2] for s2 in range(syl)])

    for ci in range(MAX_ONSET):
        solver.add(Implies(
            And(syl < num_syllables, ci < onset_length[syl]),
            word[start + ci] == onset_letters[syl * MAX_ONSET + ci]
        ))

    solver.add(Implies(
        syl < num_syllables,
        word[start + onset_length[syl]] == nucleus_letter[syl]
    ))

    for ci in range(MAX_CODA):
        solver.add(Implies(
            And(syl < num_syllables, ci < coda_length[syl]),
            word[start + onset_length[syl] + 1 + ci] == coda_letters[syl * MAX_CODA + ci]
        ))

# -------------------------------------------------------------------------------------

# OUR SONORITY RULES!

# Sonority scale (higher = more sonorant)
# stops(1) < fricatives(2) < affricates(2) < nasals(3) < liquids(4) < glides(5) < vowels(6)
sonority = Function('sonority', Graphemes, IntSort())
solver.add(ForAll([gr], sonority(gr) == If(is_stop(gr), 1,
                                       If(is_fricative(gr), 2,
                                       If(is_affricate(gr), 2,
                                       If(is_nasal(gr), 3,
                                       If(is_liquid(gr), 4,
                                       If(is_glide(gr), 5,
                                       If(is_vowel(gr), 6,
                                       0)))))))))
# Rising sonority in onsets
for syl in range(MAX_SYLLABLES):
    for ci in range(MAX_ONSET - 1):
        solver.add(Implies(
            And(syl < num_syllables, ci + 1 < onset_length[syl]),
            Or(
                onset_letters[syl * MAX_ONSET + ci] == s,
                sonority(onset_letters[syl * MAX_ONSET + ci]) <
                sonority(onset_letters[syl * MAX_ONSET + ci + 1])
            )
        ))

    # Last onset consonant must be less sonorant than the nucleus
    for ci in range(MAX_ONSET):
        solver.add(Implies(
            And(syl < num_syllables, onset_length[syl] == ci + 1),
            Or(
                onset_letters[syl * MAX_ONSET + ci] == s,
                sonority(onset_letters[syl * MAX_ONSET + ci]) <
                sonority(nucleus_letter[syl])
            )
        ))

# Falling sonority in codas
# S must be at the beginning or end of a syllable (first onset or last coda position)
for syl in range(MAX_SYLLABLES):
    # First coda consonant must be less sonorant than the nucleus
    solver.add(Implies(
        And(syl < num_syllables, coda_length[syl] >= 1),
        Or(
            coda_letters[syl * MAX_CODA] == s,
            sonority(coda_letters[syl * MAX_CODA]) <
            sonority(nucleus_letter[syl])
        )
    ))
    for ci in range(MAX_CODA - 1):
        solver.add(Implies(
            And(syl < num_syllables, ci + 1 < coda_length[syl]),
            Or(
                coda_letters[syl * MAX_CODA + ci + 1] == s,
                sonority(coda_letters[syl * MAX_CODA + ci]) >
                sonority(coda_letters[syl * MAX_CODA + ci + 1])
            )
        ))
        solver.add(Implies(
            And(syl < num_syllables, ci < coda_length[syl] - 1),
            coda_letters[syl * MAX_CODA + ci] != ng
        )) # These must appear last in complex codas
    for ci in range(MAX_ONSET):
        solver.add(Implies(
            And(syl < num_syllables, ci < onset_length[syl],
                onset_letters[syl * MAX_ONSET + ci] == s),
            ci == 0  # s must be first in onset
        ))
        solver.add(Implies(
            And(syl < num_syllables, ci < onset_length[syl],
                onset_length[syl] > 1),
            And(
                onset_letters[syl * MAX_ONSET + ci] != v,
                onset_letters[syl * MAX_ONSET + ci] != w,
                onset_letters[syl * MAX_ONSET + ci] != qu,
                onset_letters[syl * MAX_ONSET + ci] != ck,
                onset_letters[syl * MAX_ONSET + ci] != j,
                onset_letters[syl * MAX_ONSET + ci] != tch
            ) # These cannot appear in complex onsets
        ))
        solver.add(Implies(
            And(syl < num_syllables, ci < onset_length[syl]),
            And(
                onset_letters[syl * MAX_ONSET + ci] != ck,
                onset_letters[syl * MAX_ONSET + ci] != tch,
            )
        )) # These cannot appear in onsets at all
    for ci in range(MAX_CODA):
        solver.add(Implies(
            And(syl < num_syllables, ci < coda_length[syl],
                coda_letters[syl * MAX_CODA + ci] == s),
            ci == coda_length[syl] - 1  # s must be last in coda
        ))
        solver.add(Implies(
            And(syl < num_syllables, ci < coda_length[syl],
                coda_length[syl] > 1),
            And(
                Not(is_fricative(coda_letters[syl * MAX_CODA + ci])),
                Not(is_affricate(coda_letters[syl * MAX_CODA + ci])),
                coda_letters[syl * MAX_CODA + ci] != qu,
                coda_letters[syl * MAX_CODA + ci] != ck,
                coda_letters[syl * MAX_CODA + ci] != tch,
            ) # These cannot appear in complex codas
        ))
        solver.add(Implies(
            And(syl < num_syllables, ci < coda_length[syl]),
            And(
                coda_letters[syl * MAX_CODA + ci] != j,
                coda_letters[syl * MAX_CODA + ci] != f,
                coda_letters[syl * MAX_CODA + ci] != b,
                coda_letters[syl * MAX_CODA + ci] != c,
                coda_letters[syl * MAX_CODA + ci] != qu,
                coda_letters[syl * MAX_CODA + ci] != v,
            )
        )) # These cannot appear in codas at all
    for ci in range(1, MAX_ONSET):
        solver.add(Implies(
            And(syl < num_syllables, ci < onset_length[syl]),
            And(
                onset_letters[syl * MAX_ONSET + ci] != th,
                onset_letters[syl * MAX_ONSET + ci] != sh,
                onset_letters[syl * MAX_ONSET + ci] != ch,
                onset_letters[syl * MAX_ONSET + ci] != ph,
            )
        )) # These must appear first in complex onsets

# -------------------------------------------------------------------------------------

# MORE RULES WE ADDED!

solver.add(is_consonant(word[0]))
solver.add(Or(is_consonant(word[word_length -1]), word[word_length -1] == e))

# No vowels in a row (except our vowel digraphs).
# Banning specific sequences of consonants
ind = Int('ind')
solver.add(ForAll([ind], Implies(
    And(ind >= 0, ind < word_length - 1),
    And(
        Not(And(is_vowel(word[ind]), is_vowel(word[ind + 1]))),
        Not(And(word[ind] == c, word[ind + 1] == m)),
        Not(And(word[ind] == c, word[ind + 1] == n)),
        Not(And(word[ind] == ch, word[ind + 1] == s)),
        Not(And(word[ind] == d, word[ind + 1] == l)),
        Not(And(word[ind] == d, word[ind + 1] == c)),
        Not(And(word[ind] == g, word[ind + 1] == t)),
        Not(And(word[ind] == l, word[ind + 1] == g)),
        Not(And(word[ind] == l, word[ind + 1] == b)),
        Not(And(word[ind] == m, word[ind + 1] == b)),
        Not(And(word[ind] == m, word[ind + 1] == t)),
        Not(And(word[ind] == m, word[ind + 1] == d)),
        Not(And(word[ind] == m, word[ind + 1] == l)),
        Not(And(word[ind] == m, word[ind + 1] == r)),
        Not(And(word[ind] == m, word[ind + 1] == f)),
        Not(And(word[ind] == m, word[ind + 1] == h)),
        Not(And(word[ind] == n, word[ind + 1] == b)),
        Not(And(word[ind] == n, word[ind + 1] == l)),
        Not(And(word[ind] == p, word[ind + 1] == c)),
        Not(And(word[ind] == p, word[ind + 1] == f)),
        Not(And(word[ind] == p, word[ind + 1] == m)),
        Not(And(word[ind] == p, word[ind + 1] == n)),
        Not(And(word[ind] == ph, word[ind + 1] == g)),
        Not(And(word[ind] == r, word[ind + 1] == ng)),
        Not(And(word[ind] == s, word[ind + 1] == f)),
        Not(And(word[ind] == t, word[ind + 1] == f)),
        Not(And(word[ind] == t, word[ind + 1] == l)),
        Not(And(word[ind] == t, word[ind + 1] == n)),
        Not(And(word[ind] == t, word[ind + 1] == m)),
        Not(And(word[ind] == t, word[ind + 1] == g)),
        Not(And(word[ind] == t, word[ind + 1] == c)),
        Not(And(word[ind] == t, word[ind + 1] == d)),
        Not(And(word[ind] == v, word[ind + 1] == s)),
    )
)))
solver.add(ForAll([ind], Implies(
    And(ind >= 0, ind < word_length - 2),
    And(
        Not(And(word[ind] == l, word[ind + 1] == n, word[ind + 2] == b)),
        Not(And(word[ind] == l, word[ind + 1] == n, word[ind + 2] == t)),
        Not(And(word[ind] == l, word[ind + 1] == n, word[ind + 2] == p)),
        Not(And(word[ind] == l, word[ind + 1] == m, word[ind + 2] == p)),
        Not(And(word[ind] == l, word[ind + 1] == n, word[ind + 2] == g)),
        Not(And(word[ind] == l, word[ind + 1] == n, word[ind + 2] == d)),
        Not(And(word[ind] == r, word[ind + 1] == m, word[ind + 2] == p)),
        Not(And(word[ind] == r, word[ind + 1] == n, word[ind + 2] == p)),
        Not(And(word[ind] == r, word[ind + 1] == n, word[ind + 2] == d)),
        Not(And(word[ind] == r, word[ind + 1] == n, word[ind + 2] == t)),
        Not(And(word[ind] == r, word[ind + 1] == n, word[ind + 2] == g)),
        Not(And(word[ind] == s, word[ind + 1] == c, word[ind + 2] == l)),
        Not(And(word[ind] == s, word[ind + 1] == n, word[ind + 2] == r))
    )
)))

# Each grapheme appears at most once in a single onset
# Each grapheme appears at most once in a single coda
for syl in range(MAX_SYLLABLES):
    for ci in range(MAX_ONSET):
        for cj in range(ci + 1, MAX_ONSET):
            solver.add(Implies(
                And(syl < num_syllables, ci < onset_length[syl], cj < onset_length[syl]),
                onset_letters[syl * MAX_ONSET + ci] != onset_letters[syl * MAX_ONSET + cj]
            ))
    for ci in range(MAX_CODA):
        for cj in range(ci + 1, MAX_CODA):
            solver.add(Implies(
                And(syl < num_syllables, ci < coda_length[syl], cj < coda_length[syl]),
                coda_letters[syl * MAX_CODA + ci] != coda_letters[syl * MAX_CODA + cj]
            ))

# Each syllable must have at least one coda or onset consonant
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables),
    Or(onset_length[s_idx] >= 1, coda_length[s_idx] >= 1)
)))

# w appears at most once per word
solver.add(Sum([
    If(And(syl < num_syllables, ci < onset_length[syl],
           onset_letters[syl * MAX_ONSET + ci] == w), 1, 0)
    for syl in range(MAX_SYLLABLES)
    for ci in range(MAX_ONSET)
]) <= 1)

# -------------------------------------------------------------------------------------

# HARLEY'S RULES!

# Phonotactic Rule #1: All phonological words must contain at least
# one syllable, and hence must contain at least one vowel.
# --- Guaranteed by num_syllables >= 1 and nucleus must be a vowel. ---

# Phonotactic Rule #2: Sequences of repeated consonants are not possible.
solver.add(ForAll([ind], Implies(
    And(ind >= 0, ind < word_length - 1),
    Not(And(word[ind] == word[ind+1], is_consonant(word[ind])))
)))

# Phonotactic Rule #3: The velar nasal /N/ (ng) never occurs in the onset of
# a syllable.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx  >= 0, c_idx  < onset_length[s_idx]),
    onset_letters[s_idx * MAX_ONSET + c_idx] != ng
)))

# Phonotactic Rule #4: The glottal fricative /h/ never occurs in the
# coda of a syllable.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx  >= 0, c_idx  < coda_length[s_idx]),
    coda_letters[s_idx * MAX_CODA + c_idx] != h
)))

# Phonotactic Rule #5: The affricates /tS/ and /dZ/, and the glottal
# fricative /h/, do not occur in complex onsets.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        onset_length[s_idx] > 1,
        c_idx >= 0, c_idx < onset_length[s_idx]),
    And(
        onset_letters[s_idx * MAX_ONSET + c_idx] != ch,
        onset_letters[s_idx * MAX_ONSET + c_idx] != j,
        onset_letters[s_idx * MAX_ONSET + c_idx] != h
    )
)))

# Phonotactic Rule #6: The first consonant in a two-consonant onset
# must be an obstruent.
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        onset_length[s_idx] >= 2),
    is_obstruent(onset_letters[s_idx * MAX_ONSET + 0])
)))

# Phonotactic Rule #7: The second consonant in a two-consonant onset
# must not be a voiced obstruent.
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        onset_length[s_idx] >= 2),
    Not(is_voiced_obstruent(onset_letters[s_idx * MAX_ONSET + 1]))
)))

# Phonotactic Rule #8: If the first consonant of a two-consonant onset
# is not an /s/, the second consonant must be a liquid or a glide—the
# second consonant must be /l/, /®/, /w/, or /j/.
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        onset_length[s_idx] >= 2,
        onset_letters[s_idx * MAX_ONSET + 0] != s),
    Or(is_liquid(onset_letters[s_idx * MAX_ONSET + 1]),
       is_glide(onset_letters[s_idx * MAX_ONSET + 1]))
)))

# Phonotactic Rule #9: The Substring Rule: Every subsequence
# contained within a sequence of consonants must obey all the
# relevant phonotactic rules.
# --- Guaranteed because constraints apply to every consonant at every position. ---

# Phonotactic Rule #10: No glides in syllable codas.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx  >= 0, c_idx  < coda_length[s_idx]),
    Not(is_glide(coda_letters[s_idx * MAX_CODA + c_idx]))
)))

# Phonotactic Rule #11: The second consonant in a two-consonant
# coda cannot be /N/, /D/, /®/, or /Z/.
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        coda_length[s_idx] >= 2),
    Not(is_coda_second_banned(coda_letters[s_idx * MAX_CODA + 1]))
)))

# Phonotactic Rule #12: If the second consonant in a complex coda is
# voiced, the first consonant in the coda must also be voiced.
solver.add(ForAll([s_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        coda_length[s_idx] >= 2,
        is_voiced(coda_letters[s_idx * MAX_CODA + 1])),
    is_voiced(coda_letters[s_idx * MAX_CODA + 0])
)))

# Phonotactic Rule #13: When a non-alveolar nasal is in a coda
# together with a non-alveolar obstruent, they must have the same
# place of articulation, and the obstruent must be a voiceless stop.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx >= 0, c_idx < coda_length[s_idx] - 1,
        is_nasal(coda_letters[s_idx * MAX_CODA + c_idx]),
        Not(is_alveolar(coda_letters[s_idx * MAX_CODA + c_idx])),
        is_obstruent(coda_letters[s_idx * MAX_CODA + c_idx + 1]),
        Not(is_alveolar(coda_letters[s_idx * MAX_CODA + c_idx + 1]))),
    And(
        # Same place of articulation
        is_bilabial(coda_letters[s_idx * MAX_CODA + c_idx]) ==
        is_bilabial(coda_letters[s_idx * MAX_CODA + c_idx + 1]),
        is_velar(coda_letters[s_idx * MAX_CODA + c_idx]) ==
        is_velar(coda_letters[s_idx * MAX_CODA + c_idx + 1]),
        # Obstruent must be a voiceless stop
        is_stop(coda_letters[s_idx * MAX_CODA + c_idx + 1]),
        Not(is_voiced(coda_letters[s_idx * MAX_CODA + c_idx + 1]))
    )
)))

# Phonotactic Rule #14: Two obstruents in a coda together must have
# the same voicing.
solver.add(ForAll([s_idx, c_idx], Implies(
    And(s_idx >= 0, s_idx < num_syllables,
        c_idx >= 0, c_idx < coda_length[s_idx] - 1,
        is_obstruent(coda_letters[s_idx * MAX_CODA + c_idx]),
        is_obstruent(coda_letters[s_idx * MAX_CODA + c_idx + 1])),
    is_voiced(coda_letters[s_idx * MAX_CODA + c_idx]) ==
    is_voiced(coda_letters[s_idx * MAX_CODA + c_idx + 1])
)))

# -------------------------------------------------------------------------------------

# GENERATE WORDS!

all_words = []
used_syllables = []  # track syllables across all words

while len(all_words) < 50 and solver.check() == sat:
    m = solver.model()

    length = m.eval(word_length, model_completion=True).as_long()
    num_syl = m.eval(num_syllables, model_completion=True).as_long()

    syllables = []
    for syl in range(num_syl):
        o_len = m.eval(onset_length[syl], model_completion=True).as_long()
        c_len = m.eval(coda_length[syl], model_completion=True).as_long()
        nucleus = str(m.eval(nucleus_letter[syl], model_completion=True))

        onset = ''.join(str(m.eval(onset_letters[syl * MAX_ONSET + ci], model_completion=True))
                        for ci in range(o_len))
        coda  = ''.join(str(m.eval(coda_letters[syl * MAX_CODA + ci], model_completion=True))
                        for ci in range(c_len))
        syllables.append(onset + nucleus + coda)

        # Block this syllable from appearing in any future word
        used_syllables.append((
            m.eval(onset_length[syl],   model_completion=True),
            m.eval(coda_length[syl],    model_completion=True),
            m.eval(nucleus_letter[syl], model_completion=True),
            [m.eval(onset_letters[syl * MAX_ONSET + ci], model_completion=True) for ci in range(o_len)],
            [m.eval(coda_letters[syl  * MAX_CODA  + ci], model_completion=True) for ci in range(c_len)],
        ))

    all_words.append(syllables)

    # Block every used syllable from appearing at any position in future words
    for (o_len, c_len, nuc, on_letters, co_letters) in used_syllables:
        for syl in range(MAX_SYLLABLES):
            solver.add(Not(And(
                onset_length[syl]   == o_len,
                coda_length[syl]    == c_len,
                nucleus_letter[syl] == nuc,
                And([onset_letters[syl * MAX_ONSET + ci] == on_letters[ci]
                     for ci in range(o_len.as_long())]),
                And([coda_letters[syl * MAX_CODA + ci] == co_letters[ci]
                     for ci in range(c_len.as_long())])
            )))

    # Block this exact word
    word_letters = [m.eval(word[i], model_completion=True) for i in range(length)]
    solver.add(Not(And(
        word_length == length,
        And([word[i] == word_letters[i] for i in range(length)])
    )))

    # Block this syllable count and shape to force structural variety
    solver.add(Not(And(
        num_syllables == num_syl,
        And([And(onset_length[syl] == m.eval(onset_length[syl], model_completion=True),
                 coda_length[syl]  == m.eval(coda_length[syl],  model_completion=True))
             for syl in range(num_syl)])
    )))

    # Force a different nucleus in each syllable next time
    solver.add(Or([
        nucleus_letter[syl] != m.eval(nucleus_letter[syl], model_completion=True)
        for syl in range(num_syl)
    ]))

with open('generated_words.txt', 'w') as f:
    for syllables in all_words:
        word_str = ''.join(syllables)
        print(word_str)
        f.write(word_str + '\n')