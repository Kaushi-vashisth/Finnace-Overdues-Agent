import json
from apscheduler.schedulers.background import BackgroundScheduler

from database.failed_repository import FailedInvoicesRepository
from graphs.worker_graph import agent as worker

failed_repository = FailedInvoicesRepository()

def retry_failed_invoices() -> None:
    failed_rows = failed_repository.get_retryable(limit=100)
    print("\nRetrying for failed invoices:", len(failed_rows))
    for row in failed_rows:
        failed_id = row["id"]

        try:
            invoice_state = json.loads(row["invoice_state_json"])
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"Invalid invoice_state_json for failed_id={row['id']}: {exc}")
            continue

        try:

            invoice_no = invoice_state["invoice"]["invoice_no"]

            config = {
                "configurable": {
                "thread_id": f"retry-invoice-{invoice_no}-{failed_id}",
                "metadata": {
                    "invoice_no": invoice_no,
                    "failed_id": failed_id,
                    "retry": True,
                }
            }
        }

            result = worker.invoke(invoice_state,config=config)

            if result.get("send_status") != "failed":
                failed_repository.mark_resolved(failed_id)
                continue

            retry_count = row["retry_count"] + 1
            max_retries = row['max_retries']

            failed_repository.mark_retried(
                failed_id=failed_id,
                retry_count=retry_count,
                max_retries=max_retries,
                error_message=result.get("send_error", ""),
            )

        except Exception as e:
            retry_count = row["retry_count"] + 1
            max_retries = row["max_retries"]

            failed_repository.mark_retried(
                failed_id=failed_id,
                retry_count=retry_count,
                max_retries=max_retries,
                error_message=str(e),
            )


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        retry_failed_invoices,
        trigger="interval",
        minutes=2,
        id="retry_failed_invoices",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    return scheduler