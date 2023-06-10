import nox


@nox.session
def tests(session):
    session.install(".")
    session.install("pytest")
    session.run("pytest")


@nox.session
def pre_commit(session):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")
