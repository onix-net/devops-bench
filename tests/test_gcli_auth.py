import sys
import types

# deepeval and openclaw are not installed in the test environment; stub them out
# before importing gcli so the module-level imports don't fail.
for _mod in ("deepeval", "deepeval.tracing"):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

_tracing = sys.modules["deepeval.tracing"]
if not hasattr(_tracing, "observe"):
    _tracing.observe = lambda *a, **kw: (lambda f: f)

for _mod in ("pkg.agents.runner.openclaw",):
    if _mod not in sys.modules:
        _stub = types.ModuleType(_mod)
        _stub.run_openclaw_agent = None
        _stub.run_openclaw_agent_local = None
        sys.modules[_mod] = _stub

from pkg.agents.runner.gcli import _apply_gemini_auth_env


def test_api_key_wins_over_project():
    env = {"AGENT_API_KEY": "k", "GCP_PROJECT_ID": "p"}
    result = _apply_gemini_auth_env(env)
    assert result["GOOGLE_API_KEY"] == "k"
    assert result["GEMINI_API_KEY"] == "k"
    assert "GOOGLE_GENAI_USE_VERTEXAI" not in result


def test_vertex_adc_path():
    env = {"GCP_PROJECT_ID": "my-proj"}
    result = _apply_gemini_auth_env(env)
    assert result["GOOGLE_GENAI_USE_VERTEXAI"] == "true"
    assert result["GOOGLE_CLOUD_PROJECT"] == "my-proj"
    assert result["GOOGLE_CLOUD_LOCATION"] == "us-central1"
    assert "GOOGLE_API_KEY" not in result
    assert "GEMINI_API_KEY" not in result


def test_vertex_adc_custom_location():
    env = {"GCP_PROJECT_ID": "my-proj", "GCP_VERTEX_LOCATION": "europe-west1"}
    result = _apply_gemini_auth_env(env)
    assert result["GOOGLE_CLOUD_LOCATION"] == "europe-west1"


def test_adc_path_clears_preexisting_api_keys():
    env = {
        "GCP_PROJECT_ID": "p",
        "GOOGLE_API_KEY": "leftover",
        "GEMINI_API_KEY": "leftover",
    }
    result = _apply_gemini_auth_env(env)
    assert "GOOGLE_API_KEY" not in result
    assert "GEMINI_API_KEY" not in result


def test_empty_agent_api_key_falls_through_to_adc():
    env = {"AGENT_API_KEY": "", "GCP_PROJECT_ID": "p"}
    result = _apply_gemini_auth_env(env)
    assert result["GOOGLE_GENAI_USE_VERTEXAI"] == "true"


def test_model_mapping():
    env = {"AGENT_MODEL": "gemini-x"}
    result = _apply_gemini_auth_env(env)
    assert result["GEMINI_MODEL"] == "gemini-x"


def test_bare_no_auth():
    env = {}
    result = _apply_gemini_auth_env(env)
    assert "GOOGLE_API_KEY" not in result
    assert "GOOGLE_GENAI_USE_VERTEXAI" not in result
    assert "GEMINI_MODEL" not in result
