# Prior

1. If $H(X) = 10$ bits and $H(X \mid Y) = 4$ bits, what is $I(X; Y)$?
   - [ ] 14 bits
   - [ ] 4 bits
   - [x] 6 bits
   - [ ] 2.5 bits
2. Evaluate these statements about a function $f$:
   - [F] The value $f(X)$ can depend on information that is not in $X$.
   - [T] If $Z = f(X)$, knowing $X$ determines $Z$.

# Learned

1. In the coding-agent example, why can the notes $f(X)$ not know more about the fix $Y$ than the log $X$?
   - [x] The notes are computed from the log, so they only see the fix through the log
   - [ ] The notes are shorter than the log
   - [ ] The fix does not depend on the log
   - [ ] The agent's context window is too small
2. Evaluate these statements:
   - [T] Why computation still helps us extract information is an open problem, in part because we lack a good definition of accessible information.
   - [T] $I(f(X); Y) \le I(X; Y)$ for any processing $f$ of $X$.
   - [F] A clever enough $f$ can make $I(f(X); Y)$ larger than $I(X; Y)$.
