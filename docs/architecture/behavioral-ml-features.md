# Behavioral ML features

Phase 4 begins with a framework-independent feature contract. `extract_features` converts one canonical `SecurityEvent` into a typed `BehavioralFeatureVector` for the acting entity.

Current features include:

- cyclic login-hour encoding using sine and cosine;
- day of week;
- failure, authentication, and permission-use indicators;
- request rate;
- response size;
- transferred bytes;
- endpoint frequency.

Missing optional telemetry defaults to zero. The extractor does not fit a model, access external state, or make an anomaly decision. This makes the input reproducible for later baseline training and model evaluation.
