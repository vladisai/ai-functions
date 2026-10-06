# Learned

1. Which statement about a probability density function $f_X(x)$ of a continuous random variable is correct?
   - [ ] $f_X(x) = P(X = x)$, so it can never exceed 1
   - [x] $f_X(x)$ can exceed 1, as long as $\int f_X(x)\,dx = 1$
   - [ ] $f_X(x)$ is the CDF evaluated at $x$
   - [ ] $f_X(x)$ must sum to one over the possible values of $x$
2. Evaluate these statements about independence and conditional independence:
   - [T] If $X$ and $Y$ are independent, then $\mathbb{E}[XY]=\mathbb{E}[X]\mathbb{E}[Y]$
   - [F] If $X$ and $Y$ are conditionally independent given $Z$, then they must be marginally independent
   - [T] Conditional independence given $Z$ means $p(x,y|z)=p(x|z)\,p(y|z)$
   - [F] Zero covariance between $X$ and $Y$ guarantees they are independent
3. A coin is chosen at random, either fair or heavily biased toward heads. $X$ and $Y$ are two flips of the chosen coin, and $Z$ is which coin was chosen. Which description is right?
   - [ ] $X$ and $Y$ are marginally independent, but dependent given $Z$
   - [ ] $X$ and $Y$ are both marginally independent and independent given $Z$
   - [x] $X$ and $Y$ are independent given $Z$, but marginally dependent
   - [ ] $X$ and $Y$ are dependent given $Z$ and also marginally dependent
4. Using the umbrella table (rain&umbrella 0.25, rain&none 0.05, sun&umbrella 0.10, sun&none 0.60), what is $P(\text{rain}\mid\text{umbrella})$ and why?
   - [ ] $0.25$, because it is the joint probability of rain and umbrella
   - [ ] $0.30$, because it is the marginal probability of rain
   - [x] $0.25/0.35\approx 0.71$, because we restrict to the umbrella column and renormalize by $P(\text{umbrella})$
   - [ ] $0.25/0.30\approx 0.83$, because we divide by $P(\text{rain})$
