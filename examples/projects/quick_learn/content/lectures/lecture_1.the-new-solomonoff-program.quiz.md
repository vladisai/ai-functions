# Learned

1. According to Solomonoff's 1984 observation, what is the only role learning can play in optimal inference for verifiable tasks? [[lecture_1#Solomonoff's 1984 observation: The role of learning in optimal inference for verifiable tasks]]
   - [ ] Reducing uncertainty about the test distribution
   - [x] Reducing the constant in Levin's search, so that new tasks are solved faster
   - [ ] Shrinking the set of hypotheses
   - [ ] Removing the need for a verifier
2. Why is a prompt not a program for an LLM, in the lecture's view? [[lecture_1#LLMs as Maximalistic Models of Computation]]
   - [ ] Prompts are written in natural language, which no computer can execute
   - [ ] Prompts are too short to contain a program
   - [x] The LLM is stochastic, so an initial condition can condition its execution but never control it, and the prompt says what the problem is, not how to solve it
   - [ ] The program is stored in the weights, which change as the LLM runs
3. Evaluate these statements: [[lecture_1#LLMs as Maximalistic Models of Computation]]
   - [T] Turing machines were designed to be deterministic and minimalistic, so humans could better understand computability.
   - [F] The chain-of-thought is the program of an LLM, written before execution starts.
   - [F] The lecture's point is that LLMs are universal because their weights can be tweaked to implement any Turing machine.
   - [T] An LLM can be seen as a first-order random walk, with the trained backbone providing the drift vector field.
4. Evaluate these statements about learning in the lecture's new view: [[lecture_1#Solomonoff's 1984 observation: The role of learning in optimal inference for verifiable tasks]] [[lecture_1#The New Solomonoff Program]]
   - [T] Having solved many tasks before lets one sample or compose past solutions into a solution to a new, unforeseen task, possibly exponentially faster.
   - [F] Like statistical learning, this view of learning advocates shedding information about past data.
   - [F] "Generality" here means generalization: what worked on past data keeps working on future data from the same distribution.
   - [T] Agentic learning can improve tasks the model was not trained on, unlike inductive learning, whose set of hypotheses is fixed at the outset.
