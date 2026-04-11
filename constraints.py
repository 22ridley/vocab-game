from z3 import EnumSort, Const, Solver, Implies, Not, sat, And

# Phonotactic Rule #1: All phonological words must contain at least
# one syllable, and hence must contain at least one vowel.

Letters, (A, B, C, D) = EnumSort('Letters', ['A', 'B', 'C', 'D'])

# Three separate variables
v1 = Const('v1', Letters)
v2 = Const('v2', Letters)
v3 = Const('v3', Letters)

s = Solver()

# Optional: ensure all three are distinct (no repeats)
s.add(Implies(v1 == A, v2 != A))

solutions = []

while s.check() == sat:
    m = s.model()
    sol = (m.eval(v1, model_completion=True), 
           m.eval(v2, model_completion=True), 
           m.eval(v3, model_completion=True))
    solutions.append(sol)
    # Block this exact combination
    s.add(Not(And(v1 == sol[0], v2 == sol[1], v3 == sol[2])))

print("Solutions:", solutions)