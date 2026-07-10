"""Enterprise Platform layer (Sprint 10).

Makes TMIS ready for first commercial deployment at pilot law firms —
no new business features here, only cross-cutting hardening: security,
compliance, audit, observability (logging/metrics/tracing), resilience
(backup/restore/disaster recovery), performance, cost control, feature
flags, licensing, and deployment (Kubernetes, autoscaling, CI/CD).

Every module follows the same discipline as the rest of TMIS: a narrow
Protocol port per capability, a reference implementation behind it,
and zero direct dependency on an AI provider. See docs/46-platform.md.
"""
