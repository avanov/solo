from alembic.config import Config


def alembic_config_from_solo(solo_cfg):
    alembic_cfg = Config(ini_section='main')

    # path to migration scripts
    alembic_cfg.set_main_option("script_location", ".alembic")

    # template used to generate migration files
    alembic_cfg.set_main_option("file_template", "%%(rev)s_%%(slug)s")

    # max length of characters to apply to the "slug" field
    alembic_cfg.set_main_option("truncate_slug_length", "40")

    # set to 'true' to run the environment during
    # the 'revision' command, regardless of autogenerate
    alembic_cfg.set_main_option("revision_environment", "false")

    # set to 'true' to allow .pyc and .pyo files without
    # a source .py file to be detected as revisions in the
    # versions/ directory
    alembic_cfg.set_main_option("sourceless", "false")

    # version location specification; this defaults
    # to .alembic/versions.  When using multiple version
    # directories, initial revisions must be specified with --version-path
    # version_locations = %(here)s/bar %(here)s/bat .alembic/versions
    alembic_cfg.set_main_option("version_locations", ".alembic/versions")

    # the output encoding used when revision files
    # are written from script.py.mako
    alembic_cfg.set_main_option("output_encoding", "utf-8")

    alembic_cfg.set_main_option("sqlalchemy.url", "driver://user:pass@localhost/dbname")

    return alembic_cfg
