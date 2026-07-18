# Rapport d'audit — Sprint 46 (Axe B-1 : réduction de surface)

Sprint d'audit et d'élagage, pas de fonctionnalité. Périmètre : les sept
paquets de la famille « plateforme/IA transverse » (`ai_fabric`,
`ai_team`, `ai_governance`, `platform`, `runtime_platform`,
`cloud_operations`, `platform_sdk`). Ce rapport couvre T1 (audit), T2
(élagage) et T4 (désambiguïsation de nommage) ; T3 (carte des couches)
est traité séparément par `docs/172-adr-arch-01-carte-des-couches.md`.

## 1. Méthodologie (T1)

Script AST reproductible :
`backend/scripts/audit_platform_usage.py`. Il ne fait tourner aucun
code — analyse statique uniquement.

```
cd backend && python scripts/audit_platform_usage.py --format md   # tableau
cd backend && python scripts/audit_platform_usage.py --format csv  # CSV
```

Ce qu'il calcule, par sous-module direct de chacun des sept paquets :

1. **Consommateurs externes** : fichiers en dehors du sous-module
   (`backend/src` uniquement, hors tests) qui importent un de ses
   symboles — un import absolu `tmis.<paquet>.<sous_module>...`.
   Confirmé par grep qu'aucun import relatif n'existe dans ce dépôt
   (`grep -rn "^from \." src/tmis` → 0 résultat), donc l'analyse AST des
   imports absolus est exhaustive.
2. **Monté (main/api)** : le sous-module est-il dans la fermeture
   transitive des imports depuis `tmis.main`, le point d'entrée FastAPI
   réel (`app = FastAPI(...)`) ? Calculé par parcours en largeur du
   graphe d'imports, pas seulement le premier niveau — un sous-module
   consommé uniquement par un `bootstrap.py` lui-même consommé par
   `api/routes.py` compte comme monté.
3. **Testé** : au moins un fichier sous `backend/tests` importe un de
   ses symboles.

Limites assumées : l'analyse est structurelle (imports), pas
d'exécution — un import réel mais mort en pratique (jamais appelé) sera
compté comme consommateur. C'est un biais conservateur, cohérent avec le
principe du sprint (« preuve avant suppression » : mieux vaut sous-élaguer
que sur-élaguer).

## 2. Correction d'une prémisse du brief

Le brief donnait `cloud_operations/cache` comme « point de départ
confirmé : 0 consommateur ». Vérifié par grep frais avant tout calcul :
**faux dans l'état actuel du dépôt.**

```
$ grep -rn "cloud_operations\.cache" src tests | grep -v "^src/tmis/cloud_operations/cache/"
src/tmis/cloud_operations/bootstrap.py:25:from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
src/tmis/cloud_operations/api/routes.py:37:from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
tests/unit/cloud_operations/test_cache_queue_errors.py:1:from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
```

`cloud_operations/api/routes.py:283-289` monte réellement
`GET /cache/{cache_name}` sur `CacheObservabilityEngine.stats(...)`. Le
module est vivant, monté, testé — non supprimé. Le brief documentait
vraisemblablement un état antérieur du dépôt ; ce sprint applique son
propre principe directeur (« audit d'abord ») plutôt que la prémisse
donnée. Voir `docs/172-adr-arch-01-carte-des-couches.md` §4 pour ce que
`cloud_operations/cache` fait réellement (observabilité, pas cache).

## 3. Tableau d'audit (T1) — les sept paquets

Généré par `backend/scripts/audit_platform_usage.py --format md` le
2026-07-18 (`main.py` comme point d'entrée). Reproductible à
l'identique tant que le graphe d'imports ne change pas.

## `ai_fabric`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `api` | ModelDescriptorResponse, RoutingRequestPayload, RoutingDecisionResponse, PlanRequest… | 1 | oui | non |
| `batch` | BatchProcessor, BatchRequest, BatchResult | 0 | non | oui |
| `benchmark` | BenchmarkEngine, BenchmarkStorePort, BenchmarkRun, InMemoryBenchmarkStore | 2 | oui | oui |
| `cache` | ResponseCache | 2 | oui | oui |
| `capabilities` | Capability | 5 | oui | oui |
| `comparison` | ComparisonEngine, ComparisonEntry, ComparisonResult | 3 | oui | oui |
| `consensus` | ConsensusEngine, ModelPosition, ConsensusOutcome | 4 | oui | oui |
| `cost_optimizer` | CostOptimizer | 1 | oui | oui |
| `critic` | CriticModel, CriticVerdict | 3 | oui | oui |
| `evaluation` | ResponseEvaluator, ResponseMetrics | 9 | oui | oui |
| `fallback` | FallbackEngine, NoAvailableModelError | 3 | oui | oui |
| `fusion` | FusionEngine, FusionSource, FusedResponse | 3 | oui | oui |
| `governance` | GovernanceEngine, GovernanceStorePort, PolicyDecision, InMemoryGovernanceStore | 3 | oui | oui |
| `latency_optimizer` | LatencyOptimizer | 2 | oui | oui |
| `model_profiles` | ModelProfile | 8 | oui | oui |
| `model_registry` | ModelRegistryPort, ModelDescriptor, InMemoryModelRegistry | 13 | oui | oui |
| `planner` | TaskPlanner, PlanStepKind, SubTask, PlannedStep… | 3 | oui | oui |
| `policies` | PolicyStorePort, PolicyType, Policy, InMemoryPolicyStore | 3 | oui | oui |
| `prompt_optimizer` | PromptOptimizer, OptimizedPrompt | 2 | oui | oui |
| `provider_registry` | — | 2 | oui | non |
| `quality_optimizer` | QualityOptimizer, QualityStatsStorePort, ModelQualityStats, InMemoryQualityStatsStore | 3 | oui | oui |
| `quotas` | QuotaEngine, QuotaStorePort, Quota, InMemoryQuotaStore | 3 | oui | oui |
| `retry` | RetryPolicy | 1 | oui | oui |
| `router` | RouterEngine, RoutingRequest, RoutingDecision, NoEligibleModelError… | 10 | oui | oui |
| `streaming` | StreamingService, StreamAggregator, StreamChunk | 1 | oui | oui |
| `telemetry` | TelemetryDashboard, ModelTelemetrySnapshot, FabricTelemetry | 5 | oui | oui |
| `token_manager` | TokenManager | 4 | oui | oui |

## `ai_team`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `agents` | KernelAgentAdapter, KernelPort, TeamAgentPort, PromptedTeamAgent… | 15 | oui | oui |
| `api` | AgentResponse, TeamCreateRequest, CustomTeamCreateRequest, TeamResponse… | 1 | oui | non |
| `capabilities` | LegalDomain, TaskType | 27 | oui | oui |
| `consensus` | ConsensusEngine, AgentPosition, ConsensusResult | 2 | oui | oui |
| `context` | ContextEngine, ContextSlice, ContextTraceEntry | 2 | oui | oui |
| `coordinator` | CoordinatorEngine, MissionStorePort, MissionStatus, Mission… | 2 | oui | oui |
| `critique` | CritiqueEngine, Critique | 3 | oui | oui |
| `delegation` | DelegationEngine, DelegationRecord | 2 | oui | oui |
| `evaluation` | Evaluator → **`MissionQualityScorer`** (renommé, voir §4), MissionEvaluation | 1 | oui | oui |
| `human_loop` | HumanLoopEngine, HumanDecisionStorePort, HumanDecisionType, HumanDecision… | 3 | oui | oui |
| `memory` | AgentMemoryPort, ShortTermMemoryEntry, LongTermMemoryEntry, AgentPreferences… | 1 | oui | oui |
| `metrics` | MetricsCollector, AgentRunMetric, MissionMetricsSummary | 4 | oui | oui |
| `negotiation` | NegotiationEngine, NegotiationRound, NegotiationOutcome | 1 | oui | oui |
| `planner` | Planner, SubTask, MissionPlan | 4 | oui | oui |
| `registry` | AgentRegistryPort, AgentDescriptor, InMemoryAgentRegistry | 6 | oui | oui |
| `review` | ReviewEngine, ReviewDecision, ReviewRecord | 1 | oui | oui |
| `teams` | TeamBuilder, TeamStorePort, MissionComplexity, Team… | 6 | oui | oui |
| `work_queue` | InMemoryWorkQueue, WorkQueuePort, WorkItemStatus, WorkItem | 3 | oui | oui |

## `ai_governance`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `api` | ChainStepRequest, ChainStepResponse, ReasoningChainResponse, ChainGraphNodeResponse… | 1 | oui | non |
| `audit` | AIAuditEngine, AIAuditStorePort, AIAuditEntry, InMemoryAIAuditStore | 4 | oui | oui |
| `bias_detection` | GeneralizationBiasDetector, BiasDetectionEngine, BiasDetectorPort, BiasFinding | 5 | oui | oui |
| `compliance` | ComplianceEngine, ComplianceVerdict | 3 | oui | oui |
| `confidence` | GovernanceConfidenceEngine, GovernanceConfidenceWeights, GovernanceConfidenceScore | 3 | oui | oui |
| `decision_records` | DecisionRecordEngine, DecisionRecordStorePort, DecisionRecord, InMemoryDecisionRecordStore | 3 | oui | oui |
| `ethics` | EthicsEngine, EthicsFinding | 3 | oui | oui |
| `evaluation` | GovernanceEvaluator, GovernanceMetricsSinkPort, GovernanceRunMetrics, InMemoryGovernanceMetricsSink | 1 | oui | oui |
| `explainability` | ExplainabilityEngine, ExplainabilityStorePort, IgnoredElement, ExplainabilityReport… | 4 | oui | oui |
| `hallucination_detection` | HallucinationDetectionEngine, HallucinationAlert | 5 | oui | oui |
| `human_validation` | HumanValidationEngine, ValidationStorePort, ValidationMode, ValidationStatus… | 14 | oui | oui |
| `lineage` | LineageEngine, LineageStorePort, LineageRecord, LineageExplanation… | 3 | oui | oui |
| `policy_engine` | PolicyEngine, GovernancePolicyStorePort, GovernancePolicyType, GovernancePolicy… | 5 | oui | oui |
| `provenance` | ProvenanceEngine, ProvenanceStorePort, ProvenanceGranularity, SourceType… | 3 | oui | oui |
| `quality` | GovernanceQualityEngine, GovernanceQualityBreakdown | 3 | oui | oui |
| `reasoning_chain` | ReasoningChainEngine, ReasoningChainStorePort, ChainStageType, ChainStep… | 3 | oui | oui |
| `reporting` | ReportGenerator, ReportType, ReportSection, GovernanceReport | 1 | oui | oui |
| `risk_engine` | RiskEngine, RiskCategory, RiskSeverity, RiskFinding | 4 | oui | oui |
| `traceability` | TraceabilityEngine, TraceStorePort, TraceEntryKind, TraceEntry… | 3 | oui | oui |

## `platform`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `api` | — | 1 | oui | non |
| `audit` | PlatformAuditEngine, PermissionAuditEngine, PlatformAuditPort, PermissionAuditPort… | 0 | non | oui |
| `autoscaling` | AutoscalingPolicy | 3 | oui | oui |
| `backup` | BackupEngine, LocalFilesystemBackupStorage, BackupStoragePort, BackupRecordStorePort… | 4 | oui | oui |
| `cache` | CachePolicy, CachePolicyRegistry | 0 | non | oui |
| `compliance` | ComplianceEngine, DataSourceCollectorPort, AccessLogStorePort, RetentionPolicyStorePort… | 2 | oui | oui |
| `configuration` | EnvironmentTier, ConfigIssue, ConfigurableSettings | 0 | non | oui |
| `cost_control` | CostTrackerEngine, CostTrackerSummaryAdapter, CostEntryStorePort, AlertThresholdStorePort… | 10 | oui | oui |
| `deployment` | DeploymentTier, DeploymentProfile | 2 | non | oui |
| `disaster_recovery` | DisasterRecoveryEngine, DisasterRecoveryPort, RecoveryObjective, FailoverDecision | 3 | oui | oui |
| `feature_flags` | FeatureFlagEngine, FeatureFlagStorePort, FeatureFlagEnginePort, FeatureFlag… | 2 | oui | oui |
| `health` | CallableHealthCheck, ConnectorBackendHealthCheck, HealthCheckEngine, HealthCheckPort… | 11 | oui | oui |
| `kubernetes` | KubernetesManifestConfig | 0 | non | oui |
| `licensing` | LicenseEngine, LicenseStorePort, LicenseEnginePort, License… | 6 | oui | oui |
| `logging` | RedactSensitiveFields | 2 | oui | oui |
| `metrics` | Counter, Gauge, Histogram, MetricsRegistry | 13 | oui | oui |
| `monitoring` | NullCostSummaryPort, MonitoringEngine, CostSummaryPort, MonitoringEnginePort… | 4 | oui | oui |
| `observability` | — | 1 | oui | non |
| `performance` | BenchmarkResult, PageRequest, Page | 1 | oui | oui |
| `rate_limiting` | BruteForceProtector, InMemoryRateLimiter, RateLimiterPort, BruteForceProtectorPort… | 4 | oui | oui |
| `restore` | RestoreEngine, RestoreEnginePort, RestorePlan | 3 | oui | oui |
| `security` | CsrfProtect, EncryptionPort, FernetEncryption, SecurityHeadersMiddleware… | 8 | oui | oui |

## `runtime_platform`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `api` | — | 1 | oui | non |
| `async_processing` | AsyncProcessingEngine, AsyncJobStorePort, AsyncJobStatus, AsyncJob… | 2 | oui | oui |
| `autoscaling_advisor` | AutoscalingAdvisorEngine, ScalingRecommendation | 2 | oui | oui |
| `chaos_engineering` | RuntimeChaosEngine, RuntimeChaosScenarioType, RuntimeChaosResult | 2 | oui | oui |
| `cqrs` | HandlerAlreadyRegisteredError, NoHandlerRegisteredError, CommandBus, QueryBus… | 1 | oui | oui |
| `disaster_recovery` | RuntimeDisasterRecoveryEngine, BackupPolicyStorePort, BackupPolicy, RestoreSimulationResult… | 2 | oui | oui |
| `distributed_cache` | DistributedCacheEngine, CacheUsageStats | 3 | oui | oui |
| `event_store` | ArchivedStreamError, EventStoreEngine, EventStreamStorePort, SnapshotStorePort… | 2 | oui | oui |
| `event_streaming` | EventStreamingEngine, PublishableEventBusPort, EventEnvelope | 2 | oui | oui |
| `high_availability` | HighAvailabilityEngine, NodeHeartbeatStorePort, NodeStatus, NodeHeartbeat… | 2 | oui | oui |
| `load_testing` | LoadTestingEngine, LoadTestPreset, LoadTestReport | 2 | oui | oui |
| `runtime_optimizer` | RuntimeOptimizerEngine, OptimizationCategory, OptimizationSeverity, OptimizationRecommendation | 2 | oui | oui |
| `runtime_orchestrator` | RuntimeOrchestrator, RuntimeTaskStorePort, RuntimeTaskStatus, RuntimeTask… | 2 | oui | oui |

## `cloud_operations`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `ai_monitoring` | AIMonitoringEngine, AIQualityIncidentStorePort, AIQualityIssueKind, AIQualityIncident… | 2 | oui | oui |
| `alerting` | UnknownAlertRuleError, AlertingEngine, AlertRuleStorePort, AlertEventStorePort… | 2 | oui | oui |
| `api` | — | 1 | oui | non |
| `audit_pipeline` | AuditPipelineEngine, AuditSource, AuditPipelineEvent | 2 | oui | oui |
| `cache` | CacheObservabilityEngine, CacheStats | 2 | oui | oui |
| `capacity` | CapacityEngine, CapacityForecast | 3 | oui | oui |
| `chaos_testing` | ProductionChaosTestingForbiddenError, ChaosTestingEngine, ChaosScenarioType, ChaosScenarioResult | 4 | oui | oui |
| `cost_monitoring` | CostMonitoringEngine, CostMonitoringSnapshot | 2 | oui | oui |
| `dashboards` | DashboardsEngine, WorkflowsDashboard, IntegrationsDashboard, OperationsOverview | 2 | oui | non |
| `diagnostics` | DiagnosticsEngine, DiagnosticReport | 2 | oui | oui |
| `error_tracking` | ErrorTrackingEngine, ErrorEventStorePort, ErrorSeverity, ErrorEvent… | 4 | oui | oui |
| `exports` | ObservabilityExportEngine | 2 | oui | oui |
| `health_checks` | — | 1 | oui | non |
| `incident_management` | UnknownIncidentError, IncidentManagementEngine, IncidentStorePort, IncidentUpdateStorePort… | 4 | oui | oui |
| `integration_monitoring` | IntegrationMonitoringEngine, ConnectorMetricsReaderPort, IntegrationMonitoringSnapshot | 2 | oui | oui |
| `logging` | LoggingGovernanceEngine, LogRetentionPolicyStorePort, LogRetentionCategory, LogRetentionPolicy… | 1 | oui | oui |
| `metrics` | MetricsEngine, MetricEventStorePort, MetricCategory, MetricKind… | 23 | oui | oui |
| `performance` | PerformanceEngine, PerformanceSnapshot | 4 | oui | oui |
| `profiling` | ProfilingEngine, ProfilingSampleStorePort, ProfilingFindingType, ProfilingSample… | 4 | oui | oui |
| `queue_monitoring` | QueueObservabilityEngine, QueueStats | 2 | oui | oui |
| `resilience` | CircuitOpenError, CircuitBreaker, CircuitState, CircuitBreakerConfig… | 3 | oui | oui |
| `retention` | RetentionEngine, ObservabilityRetentionPolicyStorePort, ObservabilityDataCategory, ObservabilityRetentionPolicy… | 2 | oui | oui |
| `runbooks` | RunbooksEngine, RunbookStep, Runbook | 2 | oui | oui |
| `security_monitoring` | SecurityMonitoringEngine, SecurityMonitoringSnapshot | 2 | oui | oui |
| `sla` | SLAEngine, SLATargetStorePort, SLASampleStorePort, SLAMetricType… | 6 | oui | oui |
| `slo` | SLOEngine, SLOTargetStorePort, SLOTarget, SLOStatus… | 2 | oui | oui |
| `telemetry` | TelemetryEngine, TelemetryEventStorePort, TelemetryEvent, InMemoryTelemetryEventStore | 1 | oui | oui |
| `tenant_monitoring` | TenantMonitoringEngine, TenantMonitoringSnapshot | 2 | oui | oui |
| `tracing` | UnknownSpanError, TracingEngine, SpanStorePort, SpanKind… | 7 | oui | oui |
| `workflow_monitoring` | WorkflowMonitoringEngine, WorkflowMetricsReaderPort, WorkflowMonitoringSnapshot | 3 | oui | oui |

## `platform_sdk`

| sous-module | symboles publics (best-effort) | consommateurs externes | monté (main/api) | testé |
|---|---|---|---|---|
| `agent_sdk` | BaseAgentPlugin | 2 | oui | oui |
| `api` | PluginManifestResponse, ValidationIssueResponse, ValidationReportResponse, PublishingActionRequest… | 1 | oui | non |
| `api_sdk` | TmisApiClient, HttpTransportPort, HttpxTransport, InMemoryTransport | 0 | non | oui |
| `cli` | — | 0 | non | oui |
| `connector_sdk` | BaseConnectorPlugin, ConnectorPage, ConnectorResult | 1 | oui | oui |
| `developer_portal` | DeveloperPortalService, ResourceType, PortalResource | 2 | oui | oui |
| `document_sdk` | MissingVariablesError, BaseDocumentTemplatePlugin, TemplateVariable, TemplateSectionRef… | 1 | oui | oui |
| `events_sdk` | PlatformEventBus, PlatformEventName, PlatformEvent | 1 | oui | oui |
| `examples` | AgentDroitSocialPlugin, AgentFiscalPlugin, ConnectorGedPlugin, DocumentTemplateConsultationPlugin… | 1 | oui | oui |
| `extensions` | PluginNotAvailableError, UngrantablePermissionError, ExtensionEngine, ExtensionStorePort… | 5 | oui | oui |
| `marketplace` | MarketplaceEngine, ReviewStorePort, InvalidRatingError, Review… | 3 | oui | oui |
| `permissions` | PermissionEngine, PermissionStorePort, ExtensionPermission, InMemoryPermissionStore | 15 | oui | oui |
| `plugin_loader` | PluginNotPublishedError, PluginImplementationMissingError, PluginLoader, InMemoryPluginImplementationRegistry | 3 | oui | oui |
| `plugin_registry` | PluginRegistryPort, InMemoryPluginRegistry | 10 | oui | oui |
| `plugin_system` | PluginType, PublishingStatus, PluginManifest | 20 | oui | oui |
| `publishing` | PublishingEngine, PublishingStorePort, InvalidPublishingTransitionError, ValidationFailedError… | 4 | oui | oui |
| `sandbox` | SandboxExecutor, ResourceQuota, SandboxExecutionResult | 1 | oui | oui |
| `sdk` | EventPublisherPort, PermissionCheckerPort, PluginPort, PluginContext | 11 | oui | oui |
| `templates` | — | 1 | non | oui |
| `validation` | CircularDependencyError, PluginValidator, ValidationIssue, ValidationReport | 2 | oui | oui |
| `workflow_sdk` | BaseWorkflowPlugin, WorkflowRunResult, UnknownActionError, WorkflowActionRegistry… | 1 | oui | oui |

## 4. Élagage (T2) — zéro suppression, avec preuves

**Résultat au niveau demandé par le brief (sous-module) :** aucun
sous-module des sept paquets ne cumule les trois critères
« 0 consommateur externe **et** non monté **et** non testé ». Confirmé
programmatiquement : `grep -E "\| 0 \| non \| non \|"` sur le tableau
ci-dessus → 0 ligne.

Sept sous-modules ont 0 consommateur externe (`ai_fabric.batch`,
`platform.audit`, `platform.cache`, `platform.configuration`,
`platform.kubernetes`, `platform_sdk.api_sdk`, `platform_sdk.cli`) mais
sont **tous testés** — donc exclus par le troisième critère du brief.
Ce sprint est allé un cran plus loin, au niveau fichier, pour vérifier
que ce n'était pas un artefact de la granularité (un fichier vraiment
mort caché dans un sous-module par ailleurs actif) :

| Fichier | Constat | Décision |
|---|---|---|
| 5× `*/ports.py` (`ai_team.memory`, `platform.audit`, `platform.disaster_recovery`, `platform.rate_limiting`, `platform.restore`) | Convention d'architecture répétée dans **241 fichiers `ports.py`** à travers tout le dépôt (pas spécifique à ces 7 paquets) — interfaces `Protocol` documentant le point d'extension d'un adaptateur interchangeable. Le typage structurel de `Protocol` ne nécessite pas d'import pour être satisfait ; l'absence d'import n'indique pas une absence d'usage architectural. | Conservé — convention repo-wide, hors périmètre d'un sprint sur une seule famille |
| `platform.security.sso` | Docstring explicite : « Architecture-only extension point for a future OpenID Connect/SAML integration... no implementation ships this sprint » (référence `docs/47-guide-securite-entreprise.md`) | Conservé — TODO explicite, exactement le cas d'exception prévu par le brief |
| `platform.monitoring.adapters` (`NullCostSummaryPort`) | Docstring explicite : « reports zero cost — the default until `tmis.platform.cost_control` is wired in » | Conservé — placeholder documenté |
| `platform_sdk.cli.__main__` | Point d'entrée `python -m tmis.platform_sdk.cli`, jamais importé par construction (invoqué par l'OS, pas par du code Python) | Conservé — faux positif de la méthode (les entry points n'ont normalement pas de consommateur) |
| `ai_fabric.batch.engine` (`BatchProcessor`) | 0 consommateur en dehors de son propre test — **mais** documenté comme composant livré dans `docs/73-architecture-ai-fabric.md` (diagramme de couches, ligne `batch/`) et réutilise explicitement `platform.performance.concurrency.bounded_gather` (§Réutilisation du même doc). Non listé comme dette dans « Ce que ce sprint ne fait pas ». | Conservé — exclu par le critère « testé » du brief, et documenté comme livrable réel plutôt que scaffolding |

**Conclusion T2 : aucune suppression ce sprint.** Les modules
véritablement non câblés dans cette famille (le triptyque marketplace,
`ai_team.marketplace`) ont déjà été identifiés et supprimés au Sprint 44
(`docs/171-audit-marketplace.md`, `docs/reports/sprint-44-rapport-audit.md`).
Ce sprint confirme, par la même méthode, qu'il n'en reste pas d'autre
dans le périmètre audité au 2026-07-18.

## 5. Vraie duplication éventuelle

Aucune nouvelle duplication réelle (même concern, même couche, deux
implémentations divergentes) trouvée dans le périmètre de ce sprint. Les
similitudes de nom relevées dans `docs/172-adr-arch-01-carte-des-couches.md`
(`evaluation` ×4, `cache` ×3, chaîne d'orchestration) sont, à la
vérification, des concerns distincts à des couches distinctes — pas des
doublons. Backlog : néant à ce stade pour cette famille.

## 6. Désambiguïsation de nommage (T4)

Un seul renommage, strictement interne, effectué :

- **`tmis.ai_team.evaluation.Evaluator` → `MissionQualityScorer`.**
  Collision de nom brute confirmée avec `tmis.ai.evaluation.Evaluator`
  (même nom de classe, package différent, hors périmètre de ce sprint).
  Consommateurs de la version `ai_team` avant renommage : uniquement
  `ai_team/bootstrap.py` et `tests/unit/ai_team/
  test_ai_team_metrics_evaluation.py` — 0 consommateur hors du paquet
  `ai_team`, aucun symbole public cassé. Les deux points d'appel mis à
  jour dans ce sprint. `ai.evaluation.Evaluator` (télémétrie d'appel,
  `tmis.ai.kernel`) n'est pas touché — hors des sept paquets audités.

Aucun autre renommage : les autres noms partagés
(`ResponseEvaluator`/`GovernanceEvaluator` pour `evaluation` ;
`kernel`/`router`/`planner`/`coordinator`/`copilots` pour
l'orchestration ; `distributed_cache`/`platform.cache`/
`cloud_operations.cache`) sont déjà distincts au niveau nom de classe,
ou publics (consommés hors de leur paquet — table §3), donc hors règle
« interne uniquement » du sprint. Leur désambiguïsation reste
documentaire, via `docs/172-adr-arch-01-carte-des-couches.md`.

## 7. Definition of Done

- [x] Tableau d'audit d'usage produit et versionné, reproductible par
      `backend/scripts/audit_platform_usage.py`.
- [x] Modules non câblés : recherche exhaustive menée, **aucun trouvé**
      répondant aux trois critères simultanément (§4) — donc aucune
      suppression, aucun commit de suppression nécessaire.
- [x] `docs/172-adr-arch-01-carte-des-couches.md` écrit (carte des
      couches + 3 diagrammes Mermaid), chaque nom surchargé désambiguïsé.
- [x] Un seul renommage, strictement interne (§6) ; aucun symbole public
      cassé.
- [x] Suites existantes vertes, couverture ≥ 90 %, `ruff`/`mypy`/
      `bandit`/`pip-audit` verts — voir §8.

## 8. Résultats qualité

- **Tests** : `pytest --cov=tmis`, Postgres 16 local réel (migrations
  Alembic appliquées à `head`), `TMIS_REDIS_URL` volontairement
  injoignable (invariant documenté par `tests/conftest.py` —
  `redis_ping_server` : « several tests… rely on the *default*
  `TMIS_REDIS_URL` staying unreachable in CI »), secrets non-placeholder
  (mêmes valeurs que `.github/workflows/ci.yml`) : **2 388 passés, 6
  skippés, 0 échec.** Suite inchangée par ce sprint (aucun test modifié
  hors des deux points d'appel renommés en §6) — 0 régression.
  - Un premier essai local avec un vrai `redis-server` sur le port par
    défaut (6379) avait fait échouer 23 à 88 tests selon la
    configuration : faux positifs auto-infligés — la suite bascule alors
    sur le backend Redis réel au lieu du repli en mémoire attendu par
    les tests, invariant documenté ci-dessus mais rompu par la
    configuration locale, pas par ce sprint. Diagnostiqué (traceback
    `redis.asyncio` bloqué en lecture) puis corrigé en coupant Redis ;
    non gardé dans ce dépôt.
- **Couverture** : 96 % (`TOTAL` de `--cov-report=term-missing`),
  au-dessus du seuil de 90 %.
- **`ruff check .`** (ruff 0.6.9, la version épinglée par ce dépôt) :
  0 erreur. (Une invocation initiale avec un `ruff` global plus récent,
  hors venv du projet, avait signalé `UP042` sur des enums
  pré-existants — règle absente de la version 0.6.9 réellement utilisée
  par ce dépôt ; écart d'outillage local, pas une régression.)
- **`ruff format --check`** sur les fichiers touchés : déjà formatés.
- **`mypy src`** (mypy 1.20.2 avec les dépendances du projet installées) :
  1 erreur pré-existante, sans rapport avec ce sprint
  (`src/tmis/core/tenancy.py:28`, `"type[ModelT]" has no attribute
  "firm_id"` — fichier non touché par ce sprint).
- **`bandit -r src -ll`** : 0 problème Medium/High. En incluant les
  `Low` : 22 (20 `assert` hors tests + 1 `hardcoded_password_string` sur
  `"secret.manage"`, comme documenté au Sprint 45, + 1
  `B406`/`xml.sax.saxutils.escape` dans
  `cabinet_os/reports/xlsx_writer.py`, apparu depuis le Sprint 45) —
  aucun dans un fichier touché par ce sprint (vérifié :
  `bandit ... | grep Location | grep -E "ai_team|audit_platform_usage"`
  → 0 résultat).
- **`pip-audit --skip-editable`** : 65 CVE connues sur 10 paquets
  transitifs — dette pré-existante, indépendante de ce sprint (aucune
  dépendance ajoutée ou modifiée), non bloquante en CI
  (`continue-on-error: true`), cohérente avec la dette documentée au
  Sprint 45 (mise à jour de dépendances recommandée séparément).
