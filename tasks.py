from invoke import task, run


@task
def serve():
    run('runme ./config.yml')


@task
def db_revision(msg=None):
    if not msg:
        msg = 'Auto'
    run('alembic revision --autogenerate -m "{msg}"'.format(msg=msg))


@task
def db_migrate():
    run("alembic upgrade head")
