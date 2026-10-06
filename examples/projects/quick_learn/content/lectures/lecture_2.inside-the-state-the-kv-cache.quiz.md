# Prior

1. In the attention layer of a transformer, how is the output for a token computed?
   - [x] Its query is compared with the keys of the tokens, and the resulting weights average their values
   - [ ] Its value is compared with the queries, and the weights average the keys
   - [ ] It copies the value of the previous token
   - [ ] It averages the embeddings of all tokens with equal weights
2. Evaluate these statements about a decoder-only (causal) language model:
   - [T] A token can attend to itself and to the tokens before it
   - [F] A token can attend to tokens that come after it

# Learned

1. Where does the stochasticity enter the loop of generating a token?
   - [ ] When the keys and values are written into the cache
   - [ ] In the forward pass, which outputs a random token
   - [x] When a token is sampled from the distribution that the forward pass outputs
   - [ ] When the query attends over the cached keys
2. Evaluate these statements:
   - [F] Tokens injected by the controller, such as a tool output, are sampled from the model's distribution
   - [T] Once the context window is full, the state can no longer grow
   - [F] The output of a forward pass is a single token
3. When are the keys and values of a newly sampled token computed?
   - [ ] Before the token is sampled
   - [x] On the next forward pass, after the token is appended to the state
   - [ ] Never, only injected tokens are stored in the cache
   - [ ] Only once the context window is full
