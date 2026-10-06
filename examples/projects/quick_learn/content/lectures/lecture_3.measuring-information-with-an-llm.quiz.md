# Prior

1. Which identity for three tokens is right in general?
   - [ ] $p(x_1, x_2, x_3) = p(x_1) + p(x_2 \mid x_1) + p(x_3 \mid x_1, x_2)$
   - [x] $p(x_1, x_2, x_3) = p(x_1)\,p(x_2 \mid x_1)\,p(x_3 \mid x_1, x_2)$
   - [ ] $p(x_1, x_2, x_3) = p(x_1)\,p(x_2)\,p(x_3)$
   - [ ] $p(x_1, x_2, x_3) = p(x_3 \mid x_1, x_2)$
2. Evaluate these statements:
   - [T] A less probable sample has a longer optimal code, of $-\log p(x)$ bits.
   - [T] $\log(ab) = \log a + \log b$

# Learned

1. Why can an LLM compute $\log p(x)$ for a whole sentence?
   - [ ] The LLM stores a table with the probability of every sentence
   - [ ] It counts how often the sentence appears in its training data
   - [x] By the chain rule, $\log p(x)$ is a sum of next-token log-probabilities, and each of them is what the LLM outputs
   - [ ] It is the number of tokens in the sentence
2. A sentence $x$ costs 40 bits alone and 25 bits given a context $y$. What is $\mathrm{PMI}(x, y)$?
   - [x] 15 bits
   - [ ] 65 bits
   - [ ] 25 bits
   - [ ] 40 bits
3. Evaluate these statements:
   - [F] A chat model is preferable to a base model for this measurement, since what we want is $p(x)$ itself.
   - [T] "Purple silent rocks dream loudly." costs more bits than "The cat sat on the mat." because the model finds it less probable.
   - [T] A related context, like "Alice grew up in Paris." for "She speaks French fluently.", saves more bits than an unrelated one.
