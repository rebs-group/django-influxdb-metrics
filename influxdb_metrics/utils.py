"""Utilities for working with influxdb."""
from threading import Thread

from django.conf import settings

from influxdb import InfluxDBClient


def get_client():
    """Returns an ``InfluxDBClient`` instance."""
    return InfluxDBClient(
        settings.INFLUXDB_HOST,
        settings.INFLUXDB_PORT,
        settings.INFLUXDB_USER,
        settings.INFLUXDB_PASSWORD,
        settings.INFLUXDB_DATABASE,
        timeout=settings.INFLUXDB_TIMEOUT,
        ssl=getattr(settings, 'INFLUXDB_SSL', False),
        verify_ssl=getattr(settings, 'INFLUXDB_VERIFY_SSL', False),
    )


def query(query):
    """Wrapper around ``InfluxDBClient.query()``."""
    client = get_client()
    return client.query(query)


def write_points(data, force_disable_threading=False):
    """
    Writes a series to influxdb.

    :param data: Array of dicts, as required by
      https://github.com/influxdb/influxdb-python
    :param force_disable_threading: When being called from the Celery task, we
      set this to `True` so that the user doesn't accidentally use Celery and
      threading at the same time.

    """
    if getattr(settings, 'INFLUXDB_DISABLED', False):
        return

    client = get_client()
    use_threading = getattr(settings, 'INFLUXDB_USE_THREADING', False)
    if force_disable_threading:
        use_threading = False
    if use_threading is True:
        thread = Thread(target=write_points_threaded, args=(client, data, ))
        thread.start()
    else:
        client.write_points(data)


def write_points_threaded(client, data):  # pragma: no cover
    """Method to be called via threading module."""
    try:
        client.write_points(data)
    except Exception as err:
        if getattr(settings, 'INFLUXDB_FAIL_SILENTLY', True):
            pass
        else:
            raise err.message
