# Sequence replay guarantee

The fixture `tests/fixtures/sequence_attack.jsonl` is a deterministic three-event credential
attack scenario. The replay integration test normalizes and enriches those records, runs the
configured rule and sequence pipeline, and compares the complete serialized incident projection
across independent runs.

The same test also replays the identical event objects through one pipeline instance and verifies
that incident counts, evidence, event IDs, and sequence severity do not change. This demonstrates
the current in-memory replay guarantee; durable checkpoint recovery and cross-process replay remain
deployment work.
