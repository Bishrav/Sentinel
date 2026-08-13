# Entity baselines

Phase 4 Milestone 2 adds an online baseline store for behavioral feature vectors.

Each entity maintains per-feature count, mean, and population standard deviation using Welford’s numerically stable update algorithm. Event IDs are tracked so replaying an event does not bias the baseline. Baselines are returned as immutable `EntityBaseline` models ordered by entity ID.

This milestone computes statistics only. It does not decide whether an event is anomalous; anomaly scoring and model evaluation are separate milestones.
