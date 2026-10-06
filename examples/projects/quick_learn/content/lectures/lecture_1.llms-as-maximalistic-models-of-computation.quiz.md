# Prior

1. Which of these describes a dynamical system?
   - [x] A system whose state evolves over time from an initial condition, according to a rule
   - [ ] A system with no internal state
   - [ ] A fixed table from inputs to outputs, with no notion of time
   - [ ] A collection of independent random numbers
2. Evaluate these statements:
   - [T] An LLM generates text by sampling one token at a time, each conditioned on the tokens so far.
   - [T] A Turing machine run twice on the same input goes through the same steps.
   - [F] When sampling at nonzero temperature, an LLM always returns the same output for the same prompt.

# Learned

1. Why is a prompt not a program for an LLM, in the lecture's view?
   - [x] The LLM is stochastic, so an initial condition can condition its execution but never control it, and the prompt says what the problem is, not how to solve it
   - [ ] Prompts are written in natural language, which no computer can execute
   - [ ] Prompts are too short to contain a program
   - [ ] The program is stored in the weights, which change as the LLM runs
2. Evaluate these statements:
   - [T] Turing machines were designed to be deterministic and minimalistic, so humans could better understand computability.
   - [F] The chain-of-thought is the program of an LLM, written before execution starts.
   - [F] The lecture's point is that LLMs are universal because their weights can be tweaked to implement any Turing machine.
   - [T] An LLM can be seen as a first-order random walk, with the trained backbone providing the drift vector field.
