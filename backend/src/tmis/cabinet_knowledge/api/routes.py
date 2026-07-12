from fastapi import APIRouter, Depends, HTTPException

from tmis.business_platform.bootstrap import (
    CABINET_KNOWLEDGE_QUALITY_FLAG_KEY,
    get_business_feature_flag_engine,
)
from tmis.business_platform.feature_flags.engine import BusinessFeatureFlagEngine
from tmis.business_platform.feature_flags.schemas import BusinessFlagContext
from tmis.cabinet_knowledge.api.schemas import (
    ApprovalPublishRequest,
    BestPracticeCreateRequest,
    BestPracticeResponse,
    ClauseCreateRequest,
    ClauseResponse,
    ClauseVariantOut,
    EvaluationResponse,
    FeedbackResponse,
    FeedbackSubmitRequest,
    GovernanceEventResponse,
    KnowledgeCreateRequest,
    KnowledgeObjectResponse,
    LessonLearnedCreateRequest,
    LessonLearnedResponse,
    LineageResponse,
    PlaybookCreateRequest,
    PlaybookInstanceResponse,
    PlaybookInstanceStartRequest,
    PlaybookResponse,
    PlaybookStepOut,
    ReasoningPatternCreateRequest,
    ReasoningPatternResponse,
    RecommendationRequest,
    RecommendationResponse,
    SearchRequest,
    SubmitForValidationRequest,
    TemplateCreateRequest,
    TemplateResponse,
    ValidationDecisionRequest,
    ValidationRequestResponse,
    WritingStyleResponse,
    WritingStyleUpdateRequest,
)
from tmis.cabinet_knowledge.approval.engine import ApprovalEngine, NotValidatedError
from tmis.cabinet_knowledge.best_practices.engine import BestPracticeEngine
from tmis.cabinet_knowledge.best_practices.schemas import BestPractice
from tmis.cabinet_knowledge.bootstrap import (
    get_approval_engine,
    get_best_practice_engine,
    get_clause_engine,
    get_evaluation_engine,
    get_feedback_engine,
    get_governance_engine,
    get_knowledge_space,
    get_lesson_learned_engine,
    get_lineage_engine,
    get_playbook_engine,
    get_quality_engine,
    get_reasoning_pattern_engine,
    get_recommendation_engine,
    get_search_engine,
    get_template_engine,
    get_validation_engine,
    get_writing_style_engine,
)
from tmis.cabinet_knowledge.clauses.engine import ClauseEngine
from tmis.cabinet_knowledge.clauses.schemas import Clause, ClauseVariant
from tmis.cabinet_knowledge.evaluation.engine import EvaluationEngine
from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.feedback.schemas import FeedbackAction
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import (
    KnowledgeObject,
    KnowledgeStatus,
    KnowledgeType,
)
from tmis.cabinet_knowledge.lessons_learned.engine import LessonLearnedEngine
from tmis.cabinet_knowledge.lessons_learned.schemas import LessonLearned
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.playbooks.engine import PlaybookEngine, PlaybookNotValidatedError
from tmis.cabinet_knowledge.playbooks.schemas import Playbook, PlaybookInstance, PlaybookStep
from tmis.cabinet_knowledge.quality.engine import QualityEngine
from tmis.cabinet_knowledge.reasoning_patterns.engine import ReasoningPatternEngine
from tmis.cabinet_knowledge.reasoning_patterns.schemas import ReasoningPattern
from tmis.cabinet_knowledge.recommendations.engine import RecommendationEngine
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.cabinet_knowledge.search.engine import SearchEngine
from tmis.cabinet_knowledge.search.schemas import SearchQuery
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.cabinet_knowledge.templates.schemas import CabinetTemplate
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision, ValidationRequest
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.platform.security.tenant_isolation import TenantAccessError

router = APIRouter(prefix="/cabinet-knowledge", tags=["cabinet-knowledge"])


def _get_object_or_404(
    firm_id: str, object_id: str, knowledge_space: KnowledgeSpace
) -> KnowledgeObject:
    try:
        obj = knowledge_space.get(firm_id, object_id)
    except TenantAccessError as exc:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found") from exc
    if obj is None:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found")
    return obj


def _to_ko_response(obj: KnowledgeObject) -> KnowledgeObjectResponse:
    return KnowledgeObjectResponse(
        id=obj.id,
        firm_id=obj.firm_id,
        type=obj.type.value,
        title=obj.title,
        content=obj.content,
        author=obj.author,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        version=obj.version,
        status=obj.status.value,
        quality_score=obj.quality_score,
        tags=sorted(obj.tags),
        is_published=obj.is_published,
        usage_count=obj.usage_count,
    )


def _to_playbook_response(playbook: Playbook) -> PlaybookResponse:
    return PlaybookResponse(
        id=playbook.id,
        case_type=playbook.case_type,
        title=playbook.title,
        steps=[
            PlaybookStepOut(
                order=s.order,
                title=s.title,
                description=s.description,
                documents=list(s.documents),
                risks=list(s.risks),
                vigilance_points=list(s.vigilance_points),
            )
            for s in playbook.steps
        ],
        checklist=list(playbook.checklist),
    )


def _to_clause_response(clause: Clause) -> ClauseResponse:
    return ClauseResponse(
        id=clause.id,
        domain=clause.domain.value,
        clause_type=clause.clause_type,
        title=clause.title,
        variants=[
            ClauseVariantOut(id=v.id, text=v.text, notes=v.notes, language=v.language)
            for v in clause.variants
        ],
        comments=list(clause.comments),
        jurisprudence_refs=list(clause.jurisprudence_refs),
    )


def _to_template_response(template: CabinetTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=template.id,
        document_type=template.document_type.value,
        title=template.title,
        structure=list(template.structure),
        body_variables=list(template.body_variables),
    )


def _to_pattern_response(pattern: ReasoningPattern) -> ReasoningPatternResponse:
    return ReasoningPatternResponse(
        id=pattern.id,
        title=pattern.title,
        context=pattern.context,
        strategy=pattern.strategy,
        arguments=list(pattern.arguments),
        counter_arguments=list(pattern.counter_arguments),
        references=list(pattern.references),
        confidence_level=pattern.confidence_level,
    )


def _to_best_practice_response(practice: BestPractice) -> BestPracticeResponse:
    return BestPracticeResponse(
        id=practice.id,
        title=practice.title,
        description=practice.description,
        domain=practice.domain.value,
        source=practice.source,
        applicability=list(practice.applicability),
    )


def _to_lesson_response(lesson: LessonLearned) -> LessonLearnedResponse:
    return LessonLearnedResponse(
        id=lesson.id,
        title=lesson.title,
        context=lesson.context,
        outcome=lesson.outcome,
        recommendation=lesson.recommendation,
        related_case_reference=lesson.related_case_reference,
    )


def _to_validation_response(request: ValidationRequest) -> ValidationRequestResponse:
    return ValidationRequestResponse(
        id=request.id,
        firm_id=request.firm_id,
        knowledge_object_id=request.knowledge_object_id,
        requested_by=request.requested_by,
        status=request.status.value,
        reviewer=request.reviewer,
        comment=request.comment,
    )


# --- Generic knowledge objects -------------------------------------------


@router.post("/objects", response_model=KnowledgeObjectResponse)
def create_object(
    request: KnowledgeCreateRequest,
    knowledge_space: KnowledgeSpace = Depends(get_knowledge_space),
) -> KnowledgeObjectResponse:
    try:
        type_ = KnowledgeType(request.type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown type {request.type!r}") from exc
    obj = knowledge_space.create(
        request.firm_id,
        type_,
        request.title,
        request.content,
        request.author,
        tags=frozenset(request.tags),
    )
    return _to_ko_response(obj)


@router.get("/objects/{object_id}", response_model=KnowledgeObjectResponse)
def get_object(
    object_id: str,
    firm_id: str,
    knowledge_space: KnowledgeSpace = Depends(get_knowledge_space),
) -> KnowledgeObjectResponse:
    return _to_ko_response(_get_object_or_404(firm_id, object_id, knowledge_space))


@router.get("/objects", response_model=list[KnowledgeObjectResponse])
def list_objects(
    firm_id: str,
    type: str | None = None,  # noqa: A002 — mirrors the query-param name
    status: str | None = None,
    knowledge_space: KnowledgeSpace = Depends(get_knowledge_space),
) -> list[KnowledgeObjectResponse]:
    type_ = KnowledgeType(type) if type else None
    status_ = KnowledgeStatus(status) if status else None
    return [
        _to_ko_response(obj) for obj in knowledge_space.list(firm_id, type_=type_, status=status_)
    ]


@router.get("/objects/{object_id}/history", response_model=list[GovernanceEventResponse])
def get_object_history(
    object_id: str,
    firm_id: str,
    governance: GovernanceEngine = Depends(get_governance_engine),
) -> list[GovernanceEventResponse]:
    return [
        GovernanceEventResponse(
            id=e.id,
            from_status=e.from_status.value,
            to_status=e.to_status.value,
            actor=e.actor,
            reason=e.reason,
            created_at=e.created_at,
        )
        for e in governance.history(firm_id, object_id)
    ]


@router.get("/objects/{object_id}/lineage", response_model=LineageResponse)
def get_object_lineage(
    object_id: str,
    firm_id: str,
    lineage: LineageEngine = Depends(get_lineage_engine),
) -> LineageResponse:
    try:
        explanation = lineage.explain(firm_id, object_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found") from exc
    return LineageResponse(
        knowledge_object_id=explanation.knowledge_object_id,
        current_version=explanation.current_version,
        origin_source_refs=[list(r.source_refs) for r in explanation.origin_records],
        governance_events=[
            GovernanceEventResponse(
                id=e.id,
                from_status=e.from_status.value,
                to_status=e.to_status.value,
                actor=e.actor,
                reason=e.reason,
                created_at=e.created_at,
            )
            for e in explanation.governance_events
        ],
    )


@router.post("/objects/{object_id}/quality", response_model=KnowledgeObjectResponse)
def evaluate_quality(
    object_id: str,
    firm_id: str,
    quality: QualityEngine = Depends(get_quality_engine),
    knowledge_space: KnowledgeSpace = Depends(get_knowledge_space),
    flags: BusinessFeatureFlagEngine = Depends(get_business_feature_flag_engine),
) -> KnowledgeObjectResponse:
    context = BusinessFlagContext(firm_id=firm_id)
    if not flags.is_enabled(CABINET_KNOWLEDGE_QUALITY_FLAG_KEY, context):
        raise HTTPException(status_code=403, detail="quality evaluation is disabled for this firm")
    try:
        quality.evaluate_and_store(firm_id, object_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found") from exc
    return _to_ko_response(_get_object_or_404(firm_id, object_id, knowledge_space))


# --- Validation & approval -------------------------------------------------


@router.post("/objects/{object_id}/submit-for-validation", response_model=ValidationRequestResponse)
def submit_for_validation(
    object_id: str,
    request: SubmitForValidationRequest,
    validation: ValidationEngine = Depends(get_validation_engine),
) -> ValidationRequestResponse:
    try:
        result = validation.submit_for_validation(request.firm_id, object_id, request.requested_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_validation_response(result)


@router.get("/validation-requests", response_model=list[ValidationRequestResponse])
def list_pending_validation_requests(
    firm_id: str, validation: ValidationEngine = Depends(get_validation_engine)
) -> list[ValidationRequestResponse]:
    return [_to_validation_response(r) for r in validation.pending_for_firm(firm_id)]


@router.post("/validation-requests/{request_id}/decide", response_model=ValidationRequestResponse)
def decide_validation_request(
    request_id: str,
    request: ValidationDecisionRequest,
    validation: ValidationEngine = Depends(get_validation_engine),
) -> ValidationRequestResponse:
    try:
        decision = ValidationDecision(request.decision)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"unknown decision {request.decision!r}"
        ) from exc
    authorize_or_403(request.firm_id, request.reviewer, Permission.CONSULTATION_VALIDATE)
    try:
        result = validation.decide(
            request.firm_id, request_id, decision, request.reviewer, request.comment
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"validation request {request_id} not found"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_validation_response(result)


@router.post("/objects/{object_id}/publish", response_model=KnowledgeObjectResponse)
def publish_object(
    object_id: str,
    request: ApprovalPublishRequest,
    approval: ApprovalEngine = Depends(get_approval_engine),
) -> KnowledgeObjectResponse:
    try:
        obj = approval.publish(request.firm_id, object_id, request.approver)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"object {object_id} not found") from exc
    except NotValidatedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_ko_response(obj)


# --- Feedback ---------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackSubmitRequest, feedback: FeedbackEngine = Depends(get_feedback_engine)
) -> FeedbackResponse:
    try:
        action = FeedbackAction(request.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown action {request.action!r}") from exc
    try:
        result = feedback.submit(
            request.firm_id, request.knowledge_object_id, action, request.author, request.comment
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"object {request.knowledge_object_id} not found"
        ) from exc
    return FeedbackResponse(
        id=result.id,
        knowledge_object_id=result.knowledge_object_id,
        action=result.action.value,
        author=result.author,
        comment=result.comment,
        created_at=result.created_at,
    )


@router.get("/objects/{object_id}/feedback", response_model=list[FeedbackResponse])
def list_feedback(
    object_id: str, firm_id: str, feedback: FeedbackEngine = Depends(get_feedback_engine)
) -> list[FeedbackResponse]:
    return [
        FeedbackResponse(
            id=f.id,
            knowledge_object_id=f.knowledge_object_id,
            action=f.action.value,
            author=f.author,
            comment=f.comment,
            created_at=f.created_at,
        )
        for f in feedback.history_for(firm_id, object_id)
    ]


# --- Playbooks ---------------------------------------------------------------


@router.post("/playbooks", response_model=PlaybookResponse)
def create_playbook(
    request: PlaybookCreateRequest, playbooks: PlaybookEngine = Depends(get_playbook_engine)
) -> PlaybookResponse:
    steps = tuple(
        PlaybookStep(
            order=s.order,
            title=s.title,
            description=s.description,
            documents=tuple(s.documents),
            risks=tuple(s.risks),
            vigilance_points=tuple(s.vigilance_points),
        )
        for s in request.steps
    )
    playbook = playbooks.create_playbook(
        request.firm_id,
        request.title,
        request.case_type,
        steps,
        tuple(request.checklist),
        request.author,
    )
    return _to_playbook_response(playbook)


@router.get("/playbooks", response_model=list[PlaybookResponse])
def list_playbooks(
    firm_id: str,
    case_type: str | None = None,
    playbooks: PlaybookEngine = Depends(get_playbook_engine),
) -> list[PlaybookResponse]:
    return [_to_playbook_response(p) for p in playbooks.list_playbooks(firm_id, case_type)]


@router.get("/playbooks/{playbook_id}", response_model=PlaybookResponse)
def get_playbook(
    playbook_id: str, firm_id: str, playbooks: PlaybookEngine = Depends(get_playbook_engine)
) -> PlaybookResponse:
    try:
        return _to_playbook_response(playbooks.get_playbook(firm_id, playbook_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"playbook {playbook_id} not found") from exc


def _to_instance_response(instance: PlaybookInstance, progress: float) -> PlaybookInstanceResponse:
    return PlaybookInstanceResponse(
        id=instance.id,
        firm_id=instance.firm_id,
        playbook_id=instance.playbook_id,
        case_reference=instance.case_reference,
        completed_step_orders=sorted(instance.completed_step_orders),
        progress=progress,
        completed=instance.completed_at is not None,
    )


@router.post("/playbooks/{playbook_id}/instances", response_model=PlaybookInstanceResponse)
def start_playbook_instance(
    playbook_id: str,
    request: PlaybookInstanceStartRequest,
    playbooks: PlaybookEngine = Depends(get_playbook_engine),
) -> PlaybookInstanceResponse:
    try:
        instance = playbooks.start_instance(request.firm_id, playbook_id, request.case_reference)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"playbook {playbook_id} not found") from exc
    except PlaybookNotValidatedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    progress = playbooks.progress(request.firm_id, instance.id)
    return _to_instance_response(instance, progress)


@router.post(
    "/playbook-instances/{instance_id}/steps/{step_order}/complete",
    response_model=PlaybookInstanceResponse,
)
def complete_playbook_step(
    instance_id: str,
    step_order: int,
    firm_id: str,
    playbooks: PlaybookEngine = Depends(get_playbook_engine),
) -> PlaybookInstanceResponse:
    try:
        instance = playbooks.complete_step(firm_id, instance_id, step_order)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"instance {instance_id} not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    progress = playbooks.progress(firm_id, instance_id)
    return _to_instance_response(instance, progress)


# --- Clauses ------------------------------------------------------------


@router.post("/clauses", response_model=ClauseResponse)
def create_clause(
    request: ClauseCreateRequest, clauses: ClauseEngine = Depends(get_clause_engine)
) -> ClauseResponse:
    try:
        domain = LegalDomain(request.domain)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown domain {request.domain!r}") from exc
    variants = tuple(
        ClauseVariant(id=v.id, text=v.text, notes=v.notes, language=v.language)
        for v in request.variants
    )
    clause = clauses.create_clause(
        request.firm_id,
        request.title,
        domain,
        request.clause_type,
        variants,
        request.author,
        tuple(request.comments),
        tuple(request.jurisprudence_refs),
    )
    return _to_clause_response(clause)


@router.get("/clauses", response_model=list[ClauseResponse])
def search_clauses(
    firm_id: str,
    domain: str | None = None,
    clause_type: str | None = None,
    keyword: str | None = None,
    clauses: ClauseEngine = Depends(get_clause_engine),
) -> list[ClauseResponse]:
    domain_ = LegalDomain(domain) if domain else None
    return [_to_clause_response(c) for c in clauses.search(firm_id, domain_, clause_type, keyword)]


@router.get("/clauses/{clause_id}", response_model=ClauseResponse)
def get_clause(
    clause_id: str, firm_id: str, clauses: ClauseEngine = Depends(get_clause_engine)
) -> ClauseResponse:
    try:
        return _to_clause_response(clauses.get_clause(firm_id, clause_id, mark_used=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"clause {clause_id} not found") from exc


# --- Templates ------------------------------------------------------------


@router.post("/templates", response_model=TemplateResponse)
def create_template(
    request: TemplateCreateRequest, templates: CabinetTemplateEngine = Depends(get_template_engine)
) -> TemplateResponse:
    try:
        document_type = DocumentType(request.document_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"unknown document_type {request.document_type!r}"
        ) from exc
    template = templates.create_template(
        request.firm_id,
        request.title,
        document_type,
        tuple(request.structure),
        request.author,
        tuple(request.body_variables),
    )
    return _to_template_response(template)


@router.get("/templates", response_model=list[TemplateResponse])
def list_templates(
    firm_id: str,
    document_type: str | None = None,
    templates: CabinetTemplateEngine = Depends(get_template_engine),
) -> list[TemplateResponse]:
    document_type_ = DocumentType(document_type) if document_type else None
    return [_to_template_response(t) for t in templates.list_templates(firm_id, document_type_)]


# --- Reasoning patterns -------------------------------------------------


@router.post("/reasoning-patterns", response_model=ReasoningPatternResponse)
def create_reasoning_pattern(
    request: ReasoningPatternCreateRequest,
    patterns: ReasoningPatternEngine = Depends(get_reasoning_pattern_engine),
) -> ReasoningPatternResponse:
    pattern = patterns.create_pattern(
        request.firm_id,
        request.title,
        request.context,
        request.strategy,
        tuple(request.arguments),
        request.author,
        tuple(request.counter_arguments),
        tuple(request.references),
        request.confidence_level,
    )
    return _to_pattern_response(pattern)


@router.get("/reasoning-patterns", response_model=list[ReasoningPatternResponse])
def list_reasoning_patterns(
    firm_id: str, patterns: ReasoningPatternEngine = Depends(get_reasoning_pattern_engine)
) -> list[ReasoningPatternResponse]:
    return [_to_pattern_response(p) for p in patterns.list_patterns(firm_id)]


# --- Writing style --------------------------------------------------------


@router.get("/writing-style", response_model=WritingStyleResponse)
def get_writing_style(
    firm_id: str,
    actor: str,
    style: WritingStyleEngine = Depends(get_writing_style_engine),
) -> WritingStyleResponse:
    profile = style.get_or_create_profile(firm_id, actor)
    return WritingStyleResponse(
        id=profile.id,
        vocabulary=list(profile.vocabulary),
        favorite_expressions=list(profile.favorite_expressions),
        structure_preferences=list(profile.structure_preferences),
        signature_block=profile.signature_block,
    )


@router.put("/writing-style", response_model=WritingStyleResponse)
def update_writing_style(
    request: WritingStyleUpdateRequest,
    style: WritingStyleEngine = Depends(get_writing_style_engine),
) -> WritingStyleResponse:
    profile = style.update_profile(
        request.firm_id,
        request.actor,
        vocabulary=tuple(request.vocabulary) if request.vocabulary is not None else None,
        favorite_expressions=(
            tuple(request.favorite_expressions)
            if request.favorite_expressions is not None
            else None
        ),
        structure_preferences=(
            tuple(request.structure_preferences)
            if request.structure_preferences is not None
            else None
        ),
        signature_block=request.signature_block,
    )
    return WritingStyleResponse(
        id=profile.id,
        vocabulary=list(profile.vocabulary),
        favorite_expressions=list(profile.favorite_expressions),
        structure_preferences=list(profile.structure_preferences),
        signature_block=profile.signature_block,
    )


# --- Best practices & lessons learned -------------------------------------


@router.post("/best-practices", response_model=BestPracticeResponse)
def create_best_practice(
    request: BestPracticeCreateRequest,
    practices: BestPracticeEngine = Depends(get_best_practice_engine),
) -> BestPracticeResponse:
    try:
        domain = LegalDomain(request.domain)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown domain {request.domain!r}") from exc
    practice = practices.create(
        request.firm_id,
        request.title,
        request.description,
        domain,
        request.source,
        request.author,
        tuple(request.applicability),
    )
    return _to_best_practice_response(practice)


@router.get("/best-practices", response_model=list[BestPracticeResponse])
def list_best_practices(
    firm_id: str,
    domain: str | None = None,
    practices: BestPracticeEngine = Depends(get_best_practice_engine),
) -> list[BestPracticeResponse]:
    domain_ = LegalDomain(domain) if domain else None
    return [_to_best_practice_response(p) for p in practices.list(firm_id, domain_)]


@router.post("/lessons-learned", response_model=LessonLearnedResponse)
def create_lesson_learned(
    request: LessonLearnedCreateRequest,
    lessons: LessonLearnedEngine = Depends(get_lesson_learned_engine),
) -> LessonLearnedResponse:
    lesson = lessons.create(
        request.firm_id,
        request.title,
        request.context,
        request.outcome,
        request.recommendation,
        request.author,
        request.related_case_reference,
    )
    return _to_lesson_response(lesson)


@router.get("/lessons-learned", response_model=list[LessonLearnedResponse])
def list_lessons_learned(
    firm_id: str,
    keyword: str | None = None,
    lessons: LessonLearnedEngine = Depends(get_lesson_learned_engine),
) -> list[LessonLearnedResponse]:
    return [_to_lesson_response(lesson) for lesson in lessons.list(firm_id, keyword)]


# --- Search & recommendations & evaluation --------------------------------


@router.post("/search", response_model=list[KnowledgeObjectResponse])
def search_knowledge(
    request: SearchRequest, search: SearchEngine = Depends(get_search_engine)
) -> list[KnowledgeObjectResponse]:
    query = SearchQuery(
        type=KnowledgeType(request.type) if request.type else None,
        status=KnowledgeStatus(request.status) if request.status else None,
        tag=request.tag,
        keyword=request.keyword,
        published_only=request.published_only,
    )
    return [_to_ko_response(obj) for obj in search.search(request.firm_id, query)]


@router.post("/recommendations", response_model=list[RecommendationResponse])
def get_recommendations(
    request: RecommendationRequest,
    recommendations: RecommendationEngine = Depends(get_recommendation_engine),
) -> list[RecommendationResponse]:
    context = RecommendationContext(domain_tag=request.domain_tag, keywords=tuple(request.keywords))
    return [
        RecommendationResponse(
            knowledge_object_id=r.knowledge_object_id,
            object_type=r.object_type.value,
            title=r.title,
            score=r.score,
            explanation=r.explanation,
        )
        for r in recommendations.recommend(request.firm_id, context, request.limit)
    ]


@router.get("/evaluation", response_model=EvaluationResponse)
def get_evaluation(
    firm_id: str, evaluation: EvaluationEngine = Depends(get_evaluation_engine)
) -> EvaluationResponse:
    result = evaluation.evaluate_firm(firm_id)
    return EvaluationResponse(
        firm_id=result.firm_id,
        total_objects=result.total_objects,
        by_status=result.by_status,
        validation_rate=result.validation_rate,
        average_quality_score=result.average_quality_score,
        most_reused=list(result.most_reused),
        feedback_acceptance_rate=result.feedback_acceptance_rate,
    )
