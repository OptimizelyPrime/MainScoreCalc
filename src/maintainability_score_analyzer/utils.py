import os


EXTENSION_MAP = {
    ".py": "python",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".java": "java",
    ".cs": "csharp",
}

SUPPORTED_LANGUAGES = sorted(set(EXTENSION_MAP.values()))


def guess_language(filepath):
    _, extension = os.path.splitext(filepath)
    return EXTENSION_MAP.get(extension)
