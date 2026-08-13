# Sequence quality gates

CI explicitly validates the sequence subsystem in addition to the repository-wide quality job.
The targeted gate covers:

- JSON contract validation and configuration loading;
- FSM ordering, actor isolation, lateness, bounded state, and metrics;
- configured pipeline-to-incident integration;
- deterministic replay across independent and repeated runs;
- a 200-event benchmark smoke check with expected match count and positive throughput.

The benchmark smoke check is intentionally small and stable. It verifies that the harness still
executes and produces the expected deterministic result; it is not a production performance SLO.
