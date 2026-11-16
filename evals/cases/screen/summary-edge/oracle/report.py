"""One-line summaries for the run report."""


def size_summary(sizes):
    """One-line summary of file sizes in bytes."""
    if not sizes:
        return "no files"
    noun = "file" if len(sizes) == 1 else "files"
    return f"{len(sizes)} {noun}, avg {sum(sizes) / len(sizes):.1f} B"


def duration_summary(durations):
    """One-line summary of run durations in seconds."""
    if not durations:
        return "no runs"
    noun = "run" if len(durations) == 1 else "runs"
    return f"{len(durations)} {noun}, avg {sum(durations) / len(durations):.1f} s"
