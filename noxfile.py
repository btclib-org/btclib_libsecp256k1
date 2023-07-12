import nox


@nox.session
def pre_commit(session):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def tests(session):
    session.install(".")
    session.install("pytest", "pytest-cov")
    pytest = "pytest --cov-report term-missing:skip-covered --cov=btclib_libsecp256k1"
    session.run(*pytest.split())
