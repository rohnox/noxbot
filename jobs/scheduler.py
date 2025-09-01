import time
from apscheduler.schedulers.background import BackgroundScheduler

def tick():
    print("Scheduler tick - health check")

if __name__ == "__main__":
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(tick, "interval", seconds=30)
    sched.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        sched.shutdown()
