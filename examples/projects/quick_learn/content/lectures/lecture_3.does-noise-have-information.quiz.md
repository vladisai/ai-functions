# Prior

1. A lossless codec compresses files. Which file does it compress the least?
   - [x] A file of random noise
   - [ ] An image with large regions of a single color
   - [ ] A file that repeats one short pattern
   - [ ] A file of all zeros
2. Evaluate these statements:
   - [T] $I(X; Y) = 0$ when knowing $Y$ does not reduce the uncertainty about $X$.
   - [T] $I(X; Y)$ is how much knowing $Y$ reduces the uncertainty about $X$.

# Learned

1. In the Mondrian example, $Y$ is the signal $X$ plus the noise $N$. Which shares more Shannon information with $Y$?
   - [ ] The signal $X$, since it is what we care about
   - [ ] Both share about the same amount
   - [ ] Neither, since the noise destroys all the information
   - [x] The noise $N$, by a very large factor
2. Evaluate these statements:
   - [F] The mutual information in the example was computed exactly from the known distributions of $X$ and $N$.
   - [T] Shannon information does not tell meaningful bits from meaningless ones, so most of the bits $Y$ shares are with the noise.
   - [T] For Shannon's information, the noise is the most informative part of the image.
