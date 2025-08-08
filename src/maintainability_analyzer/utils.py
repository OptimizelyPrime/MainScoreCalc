import os

def guess_language(filepath):
    _, extension = os.path.splitext(filepath)
    extension_map = {
        '.py': 'python',
        '.cpp': 'cpp',
        '.hpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.java': 'java',
        '.cs': 'csharp',
    }
    return extension_map.get(extension)
