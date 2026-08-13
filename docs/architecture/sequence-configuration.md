# Sequence configuration

Sequence signatures are loaded from versioned JSON arrays using `load_sequences`. Pydantic
validation rejects malformed signatures before they reach the matcher, including missing steps,
invalid predicates, and unbounded windows.

`build_pipeline` combines rule definitions from `config/rules` with optional sequence definitions
from `config/sequences`. The default configuration demonstrates a three-step credential attack
sequence: failed login, successful login, and privilege change. Configuration changes are therefore
reviewable, testable, and independent of matcher implementation code.
