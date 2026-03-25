from apscheduler.schedulers.background import BackgroundScheduler
from models.alerts import get_active_alerts_raw, trigger_alert
from services.market_data import get_current_price
from services.notifier import send_notification
from config import ALERT_CHECK_INTERVAL_MINUTES

_scheduler = None


def check_all_alerts():
    alerts = get_active_alerts_raw()
    for alert in alerts:
        price = get_current_price(alert["symbol"])
        if price is None:
            continue

        triggered = False
        if alert["direction"] == "above" and price >= alert["target_price"]:
            triggered = True
        elif alert["direction"] == "below" and price <= alert["target_price"]:
            triggered = True

        if triggered:
            trigger_alert(alert["id"])
            send_notification(
                f"{alert['symbol']} hit ${price:.2f} "
                f"({'above' if alert['direction'] == 'above' else 'below'} "
                f"target of ${alert['target_price']:.2f})"
            )


def start_alert_checker():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(check_all_alerts, "interval", minutes=ALERT_CHECK_INTERVAL_MINUTES)
    _scheduler.start()


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running
