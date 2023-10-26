from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from sqlalchemy.exc import IntegrityError

import crud
from config import get_settings

BROKER_URL = "sqla+" + get_settings().SQLALCHEMY_DATABASE_URL
app = Celery(broker=BROKER_URL, broker_connection_retry_on_startup=False)
app.conf.enable_utc = False


logger = get_task_logger(__name__)


@app.task
def compute_winner() -> None:
    try:
        winners = crud.compute_winner()
        logger.info(
            "winners = list[tuple[restaurant_id: int, vote_count: int]] = %s", winners
        )
    except IntegrityError as e:
        if (
            e.orig is not None
            and isinstance(e.orig.args[0], str)
            and e.orig.args[0].lower().count("unique")
        ):
            logger.warn("winner already computed")
            return
        logger.exception("could not compute winner")


t = get_settings().VOTING_ENDS_AT


# add "birthdays_today" task to the beat schedule
app.conf.beat_schedule = {
    "periodic": {
        "task": "workers.compute_winner",
        "schedule": crontab(hour=t.hour, minute=t.minute),
    }
}
