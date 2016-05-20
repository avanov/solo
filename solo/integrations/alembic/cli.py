import argparse
from typing import Dict, Any

from alembic import command as alembic_cmd
from solo.cli.util import parse_app_config
from .config import alembic_config_from_solo


ALEMBIC_KV_OPTS = {  # Copied from alembic.config.CommandLine
    'template': (
        "-t", "--template",
        dict(
            default='generic',
            type=str,
            help="Setup template for use with 'init'"
        )
    ),
    'message': (
        "-m", "--message",
        dict(
            type=str,
            help="Message string to use with 'revision'")
    ),
    'sql': (
        "--sql",
        dict(
            action="store_true",
            help="Don't emit SQL to database - dump to "
            "standard output/file instead"
        )
    ),
    'tag': (
        "--tag",
        dict(
            type=str,
            help="Arbitrary 'tag' name - can be used by "
            "custom env.py scripts.")
    ),
    'head': (
        "--head",
        dict(
            type=str,
            help="Specify head revision or <branchname>@head "
            "to base new revision on."
        )
    ),
    'splice': (
        "--splice",
        dict(
            action="store_true",
            help="Allow a non-head revision as the "
            "'head' to splice onto"
        )
    ),
    'depends_on': (
        "--depends-on",
        dict(
            action="append",
            help="Specify one or more revision identifiers "
            "which this revision should depend on."
        )
    ),
    'rev_id': (
        "--rev-id",
        dict(
            type=str,
            help="Specify a hardcoded revision id instead of "
            "generating one"
        )
    ),
    'version_path': (
        "--version-path",
        dict(
            type=str,
            help="Specify specific path from config for "
            "version file"
        )
    ),
    'branch_label': (
        "--branch-label",
        dict(
            type=str,
            help="Specify a branch label to apply to the "
            "new revision"
        )
    ),
    'verbose': (
        "-v", "--verbose",
        dict(
            action="store_true",
            help="Use more verbose output"
        )
    ),
    'resolve_dependencies': (
        '--resolve-dependencies',
        dict(
            action="store_true",
            help="Treat dependency versions as down revisions"
        )
    ),
    'autogenerate': (
        "--autogenerate",
        dict(
            action="store_true",
            help="Populate revision script with candidate "
            "migration operations, based on comparison "
            "of database to model.")
    ),
    'head_only': (
        "--head-only",
        dict(
            action="store_true",
            help="Deprecated.  Use --verbose for "
            "additional output")
    ),
    'rev_range': (
        "-r", "--rev-range",
        dict(
            action="store",
            help="Specify a revision range; "
            "format is [start]:[end]")
    )
}

ALEMBIC_POS_OPTS = {  # Copied from alembic.config.CommandLine
    'directory': "location of scripts directory",
    'revision': "revision identifier",
    'revisions': "one or more revisions, or 'heads' for all heads"

}


def integrate_alembic_cli(parent_cli: argparse._SubParsersAction, prefix: str = 'db'):
    """
    """
    db = parent_cli.add_parser(prefix, help='Database commands integrated with Alembic CLI')
    subparsers = db.add_subparsers(title='sub-commands',
                                   description='valid sub-commands',
                                   help='Available Alembic commands')

    # Revision
    # http://alembic.readthedocs.io/en/latest/api/commands.html#alembic.command.revision
    # ----------------------------------------------------------------------------------
    revision = subparsers.add_parser('revision', help='integrates "alembic revision" command')
    for opt in ('message', 'autogenerate', 'sql', 'head', 'splice', 'branch_label', 'rev_id', 'depends_on'):
        *pos_opts, kv_opts = ALEMBIC_KV_OPTS[opt]
        revision.add_argument(*pos_opts, **kv_opts)

    revision.set_defaults(func=revision_cmd)

    # Upgrade
    # http://alembic.readthedocs.io/en/latest/api/commands.html#alembic.command.upgrade
    # ----------------------------------------------------------------------------------
    upgrade = subparsers.add_parser('upgrade', help='integrates "alembic upgrade" command')
    for opt in ('sql', 'tag'):
        *pos_opts, kw_opts = ALEMBIC_KV_OPTS[opt]
        upgrade.add_argument(*pos_opts, **kw_opts)

    for opt in ('revision',):
        opt_help = ALEMBIC_POS_OPTS[opt]
        upgrade.add_argument(opt, help=opt_help)

    upgrade.set_defaults(func=upgrade_cmd)


def upgrade_cmd(args, solo_cfg: Dict[str, Any]):
    config = alembic_config_from_solo(solo_cfg)
    alembic_cmd.upgrade(config, revision=args.revision, sql=args.sql, tag=args.tag)


def revision_cmd(args, solo_cfg: Dict[str, Any]):
    config = alembic_config_from_solo(solo_cfg)
    alembic_cmd.revision(config,
                         message=args.message,
                         autogenerate=args.autogenerate,
                         sql=args.sql,
                         head=args.head,
                         splice=args.splice,
                         branch_label=args.branch_label,
                         version_path=None,
                         rev_id=args.rev_id,
                         depends_on=args.depends_on)

