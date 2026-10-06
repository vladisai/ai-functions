# Prior

1. A variable $X$ takes one of 4 values with equal probability. What is $H(X)$?
   - [ ] 4 bits
   - [ ] 1 bit
   - [ ] 0 bits
   - [x] 2 bits
2. Evaluate these statements:
   - [T] $X$ and $Y$ are independent when $p(x, y) = p(x)\,p(y)$.
   - [F] If $X$ and $Y$ are independent, knowing $Y$ changes the distribution of $X$.

# Learned

1. What does $I(X; Y)$ measure?
   - [ ] The total uncertainty of $X$ and $Y$ together
   - [x] How much knowing $Y$ reduces the uncertainty about $X$
   - [ ] The uncertainty about $X$ that remains once $Y$ is known
   - [ ] The difference $H(X) - H(Y)$
2. Evaluate these statements:
   - [T] $H(X \mid Y) = H(X, Y) - H(Y)$ is how much more information $X$ and $Y$ have together than $Y$ alone.
   - [T] In the compression view, $I(X; Y)$ is the number of bits saved when encoding $X$ if we already know $Y$.
   - [F] If $H(X) = 5$ bits and $H(X \mid Y) = 2$ bits, then $I(X; Y) = 7$ bits.
3. Knowing $Y$ determines $X$ completely, so $H(X \mid Y) = 0$. What is $I(X; Y)$?
   - [ ] 0
   - [x] $H(X)$
   - [ ] 1 bit
   - [ ] $-H(X)$
