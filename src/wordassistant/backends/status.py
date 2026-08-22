from importlib.util import find_spec

def advanced_word_backend_available()->bool:
    return find_spec('docx_mcp') is not None
