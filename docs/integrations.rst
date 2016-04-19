Alembic integration
-------------------

Add ``[solo]`` section to your ``alembic.ini`` config:

.. code-block:: ini

    [solo]
    config = config.yml

    [alembic]
    # alembic options...

Then, in the ``env.py`` of your project's migrations directory:

.. code-block:: python

    from solo.integrations import alembic as solo_alembic

    target_metadata = solo_alembic.collect_metadata(config)
    run_migrations_online = solo_alembic.get_run_migrations_online(config, target_metadata, context)

