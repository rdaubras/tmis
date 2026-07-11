from tmis.ai_fabric.critic.engine import CriticModel
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator, jaccard_similarity


def test_jaccard_similarity_of_identical_text_is_one() -> None:
    assert jaccard_similarity("le contrat est valide", "le contrat est valide") == 1.0


def test_jaccard_similarity_of_disjoint_text_is_zero() -> None:
    assert jaccard_similarity("chat chien oiseau", "voiture avion bateau") == 0.0


def test_jaccard_similarity_of_two_empty_strings_is_one() -> None:
    assert jaccard_similarity("", "") == 1.0


def test_response_evaluator_counts_citations() -> None:
    evaluator = ResponseEvaluator()

    metrics = evaluator.evaluate("Art. 1103 du Code civil impose la force obligatoire.")

    assert metrics.citation_count >= 1


def test_response_evaluator_flags_internal_contradiction() -> None:
    evaluator = ResponseEvaluator()
    text = (
        "Le contrat est valide et pleinement applicable entre les parties. "
        "Le contrat n'est pas valide et pleinement applicable entre les parties."
    )

    metrics = evaluator.evaluate(text)

    assert metrics.contradiction_flags
    assert metrics.coherence_score < 1.0


def test_response_evaluator_coherent_text_has_no_flags() -> None:
    evaluator = ResponseEvaluator()

    metrics = evaluator.evaluate("Le contrat est valide. Il produit ses effets entre les parties.")

    assert metrics.contradiction_flags == ()
    assert metrics.coherence_score == 1.0


def test_critic_model_never_alters_the_text_it_reviews() -> None:
    critic = CriticModel()
    text = "Le contrat est valide."

    verdict = critic.review("gpt-x", text)

    assert verdict.model_name == "gpt-x"
    assert verdict.metrics.length_words == len(text.split())


def test_critic_model_flags_absence_of_citations() -> None:
    critic = CriticModel()

    verdict = critic.review("gpt-x", "Le contrat semble valide sans plus de précision.")

    assert "aucune citation ou référence détectée" in verdict.issues


def test_critic_model_penalizes_contradictions_in_quality_score() -> None:
    critic = CriticModel()
    contradictory = (
        "Le contrat est valide et pleinement applicable entre les parties. "
        "Le contrat n'est pas valide et pleinement applicable entre les parties."
    )
    coherent = "Le contrat est valide. Il produit ses effets entre les parties."

    contradictory_verdict = critic.review("gpt-x", contradictory)
    coherent_verdict = critic.review("gpt-x", coherent)

    assert contradictory_verdict.quality_score < coherent_verdict.quality_score
