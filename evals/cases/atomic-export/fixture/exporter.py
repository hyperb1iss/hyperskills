from pathlib import Path


def export_lines(lines, destination):
    """Write UTF-8 lines to destination, adding one newline per line."""
    with Path(destination).open("w", encoding="utf-8") as output:
        for line in lines:
            output.write(line + "\n")
