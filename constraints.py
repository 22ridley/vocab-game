from z3 import EnumSort, Const, Solver, Implies, Not, sat, And, Function, ForAll, Or, BoolSort, Exists, IntSort, Int, Array, BoolVal

Graphemes, (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, th, ch, sh, ng) = EnumSort('Letters', ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'th', 'ch', 'sh', 'ng'])
gr = Const('gr', Graphemes)

# Classifier functions ---
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

all_letters = [a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,th,ch,ng]

def is_in_set(fn, members):
    """Assert fn(l) == True iff l is in `members`."""
    member_set = set(members)
    return [fn(l) == BoolVal(l in member_set) for l in all_letters]

# --- Phonological classes (English approximations) ---
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

# OUR RULES!

word = Array('word', IntSort(), Graphemes)
word_length = Int('word_length')
# We want to generate interesting words, but not too long or too short.
solver.add(word_length >= 4)
solver.add(word_length <= 8)
# No a's, u's, or i's in a row.
ind = Int('ind')
solver.add(ForAll([ind], Implies(
    And(ind >= 0, ind < word_length - 1),
    Not(And(word[ind] == word[ind+1], Or(word[ind] == a, word[ind] == i, word[ind] == u)))
)))

# -------------------------------------------------------------------------------------

# HARLEY'S RULES!

# Phonotactic Rule #1: All phonological words must contain at least
# one syllable, and hence must contain at least one vowel.
vowel_ind = Int('vowel_index')
solver.add(Exists([vowel_ind], And(vowel_ind >= 0, vowel_ind < word_length, is_vowel(word[vowel_ind]))))

# Phonotactic Rule #2: Sequences of repeated consonants are not possible.

# Phonotactic Rule #3: The velar nasal /N/ never occurs in the onset of
# a syllable.

# Phonotactic Rule #4: The glottal fricative /h/ never occurs in the
# coda of a syllable.

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
    m = solver.model()
    
    length = m.eval(word_length, model_completion=True).as_long()
    word_letters = [m.eval(word[i], model_completion=True) for i in range(length)]
    all_words.append(word_letters)
    
    # Block this exact word
    solver.add(Not(And(
        word_length == length,
        And([word[i] == word_letters[i] for i in range(length)])
    )))

for word_letters in all_words:
    print(''.join(str(l) for l in word_letters))