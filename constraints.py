from z3 import (EnumSort, Const, Solver, Implies, Not, sat, And, Function,
                ForAll, Or, BoolSort, Exists, IntSort, Int, Array, BoolVal, Sum, If)
import random

# Constants
MAX_ONSET     = 3
MAX_CODA      = 5
MAX_SYLLABLES = 4
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 8

Graphemes, (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, th, ch, sh, ng) = \
    EnumSort('Letters', ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
                         's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'th', 'ch', 'sh', 'ng'])
gr = Const('gr', Graphemes)

# -------------------------------------------------------------------------------------

# Classifier functions
is_vowel     = Function('is_vowel',     Graphemes, BoolSort())
is_glide     = Function('is_glide',     Graphemes, BoolSort())
is_liquid    = Function('is_liquid',    Graphemes, BoolSort())
is_nasal     = Function('is_nasal',     Graphemes, BoolSort())
is_fricative = Function('is_fricative', Graphemes, BoolSort())
is_affricate = Function('is_affricate', Graphemes, BoolSort())
is_stop      = Function('is_stop',      Graphemes, BoolSort())

# Grouping functions
is_obstruent = Function('is_obstruent', Graphemes, BoolSort())
is_sonorant  = Function('is_sonorant',  Graphemes, BoolSort())
is_consonant = Function('is_consonant', Graphemes, BoolSort())

all_graphemes = [a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,th,ch,sh,ng]

def is_in_set(fn, members):
    """Assert fn(l) == True iff l is in `members`."""
    member_set = set(members)
    return [fn(l) == BoolVal(l in member_set) for l in all_graphemes]

# Phonological classes
VOWELS     = [a, e, i, o, u]
GLIDES     = [w, y]
LIQUIDS    = [l, r]
NASALS     = [m, n, ng]
FRICATIVES = [f, v, s, z, h, th, sh]
AFFRICATES = [ch, j]
STOPS      = [b, d, g, k, p, t]

solver = Solver()
solver.add(is_in_set(is_vowel,     VOWELS))
solver.add(is_in_set(is_glide,     GLIDES))
solver.add(is_in_set(is_liquid,    LIQUIDS))
solver.add(is_in_set(is_nasal,     NASALS))
solver.add(is_in_set(is_fricative, FRICATIVES))
solver.add(is_in_set(is_affricate, AFFRICATES))
solver.add(is_in_set(is_stop,      STOPS))

# Obstruent = stop | fricative | affricate
solver.add(ForAll([gr], is_obstruent(gr) == Or(is_stop(gr), is_fricative(gr), is_affricate(gr))))
# Sonorant = vowel | glide | liquid | nasal
solver.add(ForAll([gr], is_sonorant(gr) == Or(is_vowel(gr), is_glide(gr), is_liquid(gr), is_nasal(gr))))
# Consonant = anything that isn't a vowel
solver.add(ForAll([gr], is_consonant(gr) == Not(is_vowel(gr))))

# -------------------------------------------------------------------------------------

# onset_letters[syl * MAX_ONSET + i] = i-th consonant of onset of syllable syl
# coda_letters[syl * MAX_CODA + i]   = i-th consonant of coda of syllable syl
# nucleus_letter[syl]                = vowel of syllable syl
onset_letters  = Array('onset_letters',  IntSort(), Graphemes)
coda_letters   = Array('coda_letters',   IntSort(), Graphemes)
nucleus_letter = Array('nucleus_letter', IntSort(), Graphemes)
onset_length   = Array('onset_length',   IntSort(), IntSort())
coda_length    = Array('coda_length',    IntSort(), IntSort())
num_syllables  = Int('num_syllables')
s_idx = Int('s_idx')
c_idx = Int('c_idx')

# Number of syllables in bounds
solver.add(num_syllables >= 1)
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

# -------------------------------------------------------------------------------------

# OUR SYLLABLE-LEVEL RULES!

word        = Array('word', IntSort(), Graphemes)
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

# MORE RULES WE ADDED!

# No a's, u's, or i's in a row.
ind = Int('ind')
solver.add(ForAll([ind], Implies(
    And(ind >= 0, ind < word_length - 1),
    Not(And(word[ind] == word[ind+1], Or(word[ind] == a, word[ind] == i, word[ind] == u)))
)))

# Each grapheme appears at most once in a single onset
for syl in range(MAX_SYLLABLES):
    for ci in range(MAX_ONSET):
        for cj in range(ci + 1, MAX_ONSET):
            solver.add(Implies(
                And(syl < num_syllables, ci < onset_length[syl], cj < onset_length[syl]),
                onset_letters[syl * MAX_ONSET + ci] != onset_letters[syl * MAX_ONSET + cj]
            ))

# Each grapheme appears at most once in a single coda
for syl in range(MAX_SYLLABLES):
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

# -------------------------------------------------------------------------------------

# HARLEY'S RULES!

# Phonotactic Rule #1: All phonological words must contain at least
# one syllable, and hence must contain at least one vowel.
# --- Guaranteed structurally by num_syllables >= 1 and nucleus must be a vowel. --

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

# Phonotactic Rule #6: The first consonant in a two-consonant onset
# must be an obstruent.

# Phonotactic Rule #7: The second consonant in a two-consonant onset
# must not be a voiced obstruent.

# Phonotactic Rule #8: If the first consonant of a two-consonant onset
# is not an /s/, the second consonant must be a liquid or a glide—the
# second consonant must be /l/, /®/, /w/, or /j/.

# Phonotactic Rule #9: The Substring Rule: Every subsequence
# contained within a sequence of consonants must obey all the
# relevant phonotactic rules.

# Phonotactic Rule #10: No glides in syllable codas.

# Phonotactic Rule #11: The second consonant in a two-consonant
# coda cannot be /N/, /D/, /®/, or /Z/.

# Phonotactic Rule #12: If the second consonant in a complex coda is
# voiced, the first consonant in the coda must also be voiced.

# Phonotactic Rule #13: When a non-alveolar nasal is in a coda
# together with a non-alveolar obstruent, they must have the same
# place of articulation, and the obstruent must be a voiceless stop.

# Phonotactic Rule #14: Two obstruents in a coda together must have
# the same voicing.

# -------------------------------------------------------------------------------------

# GENERATE WORDS!

all_words = []

while len(all_words) < 5 and solver.check() == sat:
    # Pick a random target length for this word
    target_length = random.randint(MIN_WORD_LENGTH, MAX_WORD_LENGTH)
    solver.push()
    solver.add(word_length == target_length)

    if solver.check() == sat:
        m = solver.model()

        length = m.eval(word_length, model_completion=True).as_long()
        word_letters = [m.eval(word[i], model_completion=True) for i in range(length)]
        all_words.append(word_letters)

        # Block this exact word (added outside the push/pop scope so it persists)
        solver.pop()
        solver.add(Not(And(
            word_length == length,
            And([word[i] == word_letters[i] for i in range(length)])
        )))
    else:
        # This length was unsatisfiable, just discard and try again
        solver.pop()

for word_letters in all_words:
    print(''.join(str(l) for l in word_letters))