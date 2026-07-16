import uuid

import pytest

from tmis.core.tenancy import scoped_query
from tmis.infrastructure.persistence.models import CaseModel, FirmModel


def test_scoped_query_filters_by_firm_id() -> None:
    firm_id = uuid.uuid4()
    stmt = scoped_query(CaseModel, firm_id)
    assert firm_id.hex in str(stmt.compile(compile_kwargs={"literal_binds": True}))


def test_scoped_query_refuses_a_model_without_firm_id() -> None:
    with pytest.raises(TypeError, match="firm_id"):
        scoped_query(FirmModel, uuid.uuid4())
