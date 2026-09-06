import subprocess


def test_read_issue_fetches_title_and_body(monkeypatch):
    from starboy.issue import read_issue

    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"title": "Fix the button", "body": "It does not submit."}',
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    issue = read_issue(123)

    assert issue.title == "Fix the button"
    assert issue.body == "It does not submit."
