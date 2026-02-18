graph TD
subgraph Source
  src__requests____init___py["src/requests/__init__.py"]
  src__requests____version___py["src/requests/__version__.py"]
  src__requests___internal_utils_py["src/requests/_internal_utils.py"]
  src__requests__adapters_py["src/requests/adapters.py"]
  src__requests__api_py["src/requests/api.py"]
  src__requests__auth_py["src/requests/auth.py"]
  src__requests__certs_py["src/requests/certs.py"]
  src__requests__compat_py["src/requests/compat.py"]
  src__requests__cookies_py["src/requests/cookies.py"]
  src__requests__exceptions_py["src/requests/exceptions.py"]
  src__requests__help_py["src/requests/help.py"]
  src__requests__hooks_py["src/requests/hooks.py"]
  src__requests__models_py["src/requests/models.py"]
  src__requests__packages_py["src/requests/packages.py"]
  src__requests__sessions_py["src/requests/sessions.py"]
  src__requests__status_codes_py["src/requests/status_codes.py"]
  src__requests__structures_py["src/requests/structures.py"]
  src__requests__utils_py["src/requests/utils.py"]
end
subgraph Project
  setup_py["setup.py"]
end
src__requests____init___py --> src__requests____version___py
src__requests____init___py --> src__requests__api_py
src__requests____init___py --> src__requests__exceptions_py
src__requests____init___py --> src__requests__models_py
src__requests____init___py --> src__requests__packages_py
src__requests____init___py --> src__requests__sessions_py
src__requests____init___py --> src__requests__status_codes_py
src__requests____init___py --> src__requests__utils_py
src__requests___internal_utils_py --> src__requests__compat_py
src__requests__adapters_py --> src__requests__auth_py
src__requests__adapters_py --> src__requests__compat_py
src__requests__adapters_py --> src__requests__cookies_py
src__requests__adapters_py --> src__requests__exceptions_py
src__requests__adapters_py --> src__requests__models_py
src__requests__adapters_py --> src__requests__structures_py
src__requests__adapters_py --> src__requests__utils_py
src__requests__api_py --> src__requests__sessions_py
src__requests__auth_py --> src__requests___internal_utils_py
src__requests__auth_py --> src__requests__compat_py
src__requests__auth_py --> src__requests__cookies_py
src__requests__auth_py --> src__requests__utils_py
src__requests__cookies_py --> src__requests___internal_utils_py
src__requests__cookies_py --> src__requests__compat_py
src__requests__exceptions_py --> src__requests__compat_py
src__requests__help_py --> src__requests____version___py
src__requests__models_py --> src__requests___internal_utils_py
src__requests__models_py --> src__requests__auth_py
src__requests__models_py --> src__requests__compat_py
src__requests__models_py --> src__requests__cookies_py
src__requests__models_py --> src__requests__exceptions_py
src__requests__models_py --> src__requests__hooks_py
src__requests__models_py --> src__requests__status_codes_py
src__requests__models_py --> src__requests__structures_py
src__requests__models_py --> src__requests__utils_py
src__requests__packages_py --> src__requests__compat_py
src__requests__sessions_py --> src__requests___internal_utils_py
src__requests__sessions_py --> src__requests__adapters_py
src__requests__sessions_py --> src__requests__auth_py
src__requests__sessions_py --> src__requests__compat_py
src__requests__sessions_py --> src__requests__cookies_py
src__requests__sessions_py --> src__requests__exceptions_py
src__requests__sessions_py --> src__requests__hooks_py
src__requests__sessions_py --> src__requests__models_py
src__requests__sessions_py --> src__requests__status_codes_py
src__requests__sessions_py --> src__requests__structures_py
src__requests__sessions_py --> src__requests__utils_py
src__requests__status_codes_py --> src__requests__structures_py
src__requests__structures_py --> src__requests__compat_py
src__requests__utils_py --> src__requests____version___py
src__requests__utils_py --> src__requests___internal_utils_py
src__requests__utils_py --> src__requests__certs_py
src__requests__utils_py --> src__requests__compat_py
src__requests__utils_py --> src__requests__cookies_py
src__requests__utils_py --> src__requests__exceptions_py
src__requests__utils_py --> src__requests__structures_py