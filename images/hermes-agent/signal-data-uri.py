"""Make the Signal adapter send attachments as data URIs instead of file paths.

signal-cli runs in its own pod and cannot read the gateway's file paths.
"""

import sys

path = sys.argv[1]
src = open(path).read()

replacements = [
    (
        "\n\ndef _is_image_ext(",
        '''

def _data_uri(path: str) -> str:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    mime = mime_for_ext(Path(path).suffix, fallback="application/octet-stream")
    return f"data:{mime};filename={quote(Path(path).name)};base64,{data}"


def _is_image_ext(''',
    ),
    ('"attachments": [file_path]', '"attachments": [_data_uri(file_path)]'),
    ("attachments=att_batch)", "attachments=[_data_uri(p) for p in att_batch])"),
]
for old, new in replacements:
    if src.count(old) != 1:
        sys.exit(f"{path}: expected one {old!r}, found {src.count(old)}")
    src = src.replace(old, new)

open(path, "w").write(src)
