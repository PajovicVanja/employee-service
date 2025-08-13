# Auth is handled by the API Gateway; this service no longer exposes /token.
import pytest
pytest.skip("Auth endpoints removed from employee-service; covered at API Gateway.", allow_module_level=True)
