# Prior

1. A variable $N$ has $I(N; T) = 0$. What does this mean?
   - [ ] $N$ and $T$ are the same variable
   - [ ] $N$ determines $T$
   - [ ] $T$ has zero entropy
   - [x] Knowing $N$ does not reduce the uncertainty about $T$
2. A representation $Z$ is computed from the input $X$. Evaluate these statements:
   - [T] $I(Z; T) \le I(X; T)$
   - [F] $Z$ can carry more information about the task $T$ than $X$ does.

# Learned

1. When is a representation $Z$ minimal?
   - [ ] When it has the fewest dimensions
   - [ ] When $I(Z; X) = 0$
   - [x] When it is sufficient, $I(Z; T) = I(X; T)$, and has the smallest $I(Z; X)$ among the sufficient representations
   - [ ] When it keeps everything about the input
2. Evaluate these statements:
   - [F] A sufficient representation must keep all the information about the input $X$.
   - [T] If $Z$ is sufficient and $I(Z; X) = I(X; T)$, then $I(Z; N) = 0$ for every nuisance $N$.
   - [T] A minimal sufficient representation is invariant to nuisances.
3. Why can we not get a minimal representation by just making the state smaller?
   - [x] Fewer dimensions make the state less expressive, and what matters is bits, not dimensions
   - [ ] A smaller state always keeps more nuisances
   - [ ] A smaller state cannot be computed from the input
   - [ ] Minimal representations need more dimensions than the input
