from tmis.platform.logging.redaction import RedactSensitiveFields


def test_redacts_a_top_level_sensitive_key() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(None, "info", {"event": "login", "password": "hunter2"})

    assert result["password"] == "***REDACTED***"
    assert result["event"] == "login"


def test_redaction_is_case_insensitive() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(None, "info", {"Authorization": "Bearer abc123"})

    assert result["Authorization"] == "***REDACTED***"


def test_redacts_nested_dict_values() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(None, "info", {"user": {"name": "Alice", "token": "secret-token"}})

    assert result["user"]["token"] == "***REDACTED***"
    assert result["user"]["name"] == "Alice"


def test_redacts_sensitive_keys_inside_list_of_dicts() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(
        None,
        "info",
        {"users": [{"name": "Alice", "token": "t1"}, {"name": "Bob", "token": "t2"}]},
    )

    assert result["users"] == [
        {"name": "Alice", "token": "***REDACTED***"},
        {"name": "Bob", "token": "***REDACTED***"},
    ]


def test_a_sensitive_top_level_key_is_fully_redacted_even_if_its_value_is_a_list() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(None, "info", {"api_key": ["k1", "k2"]})

    assert result["api_key"] == "***REDACTED***"


def test_non_sensitive_values_pass_through_unchanged() -> None:
    redactor = RedactSensitiveFields()

    result = redactor(None, "info", {"case_id": "case-1", "count": 3})

    assert result == {"case_id": "case-1", "count": 3}


def test_custom_sensitive_keys_can_be_configured() -> None:
    redactor = RedactSensitiveFields(sensitive_keys=frozenset({"ssn"}))

    result = redactor(None, "info", {"ssn": "123-45-6789", "password": "not-redacted-here"})

    assert result["ssn"] == "***REDACTED***"
    assert result["password"] == "not-redacted-here"
