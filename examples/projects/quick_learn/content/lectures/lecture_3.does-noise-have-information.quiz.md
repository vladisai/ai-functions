# Learned

1. $H(X) = 5$ bits and $H(X \mid Y) = 2$ bits. What is $I(X; Y)$, and what does it measure? [[lecture_3#Mutual information]]
   - [ ] 7 bits, the information that $X$ and $Y$ have together
   - [ ] 2 bits, the uncertainty about $X$ that remains once $Y$ is known
   - [x] 3 bits, the bits saved when encoding $X$ if we already know $Y$
   - [ ] 2.5 bits, the ratio of the two entropies
2. Under an LLM, a sentence $x$ costs 40 bits alone and 25 bits given a context $y$. What is $\mathrm{PMI}(x, y)$? [[lecture_3#Measuring information with an LLM]]
   - [ ] 65 bits
   - [ ] 25 bits
   - [x] 15 bits
   - [ ] 40 bits
3. An agent writes notes $f(X)$ from a test log $X$, and $Y$ is the correct fix. Which statement always holds? [[lecture_3#The data processing inequality]]
   - [ ] $I(f(X); Y) \ge I(X; Y)$, since good notes bring out what the log hides
   - [x] $I(f(X); Y) \le I(X; Y)$, since the notes only see the fix through the log
   - [ ] $I(f(X); Y) = 0$, since the notes are shorter than the log
   - [ ] $I(f(X); Y) = I(X; Y)$, whatever the notes are
4. Evaluate these statements: [[lecture_3#Measuring information with an LLM]] [[lecture_3#Communication, not meaning]] [[lecture_3#Does noise have information?]]
   - [T] By the chain rule, an LLM gives $\log p(x)$ of a sentence as the sum of the next-token log-probabilities it outputs.
   - [T] For two round clusters of equal mass, the cut between the clusters and a random, irregular cut that splits the mass in half each give one bit.
   - [F] In the Mondrian example, the signal $X$ shares more Shannon information with $Y = X + N$ than the noise $N$ does.
   - [F] Shannon information tells meaningful bits from meaningless ones.
