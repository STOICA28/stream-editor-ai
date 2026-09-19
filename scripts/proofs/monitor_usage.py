
import time
import psutil
import datetime

print("Starting resource monitor...")
peak_disk = 0
peak_ram = 0

while True:
    try:
        # Check ffmpeg memory
        ffmpeg_procs = [p for p in psutil.process_iter(["name", "memory_info"]) if p.info["name"] == "ffmpeg.exe"]
        for p in ffmpeg_procs:
            ram = p.info["memory_info"].rss
            if ram > peak_ram: peak_ram = ram
            
        # Check python worker memory
        worker_procs = [p for p in psutil.process_iter(["name", "memory_info"]) if "python" in p.info["name"].lower() or "celery" in p.info["name"].lower()]
        for p in worker_procs:
            try:
                cmd = " ".join(p.cmdline())
                if "celery" in cmd.lower():
                    ram = p.info["memory_info"].rss
                    if ram > peak_ram: peak_ram = ram
            except: pass
            
        # Write to log periodically
        with open("monitor_stats.txt", "w") as f:
            f.write(f"Peak RAM: {peak_ram / 1024 / 1024:.2f} MB\n")
            f.write(f"Last updated: {datetime.datetime.now()}\n")
            
    except Exception as e:
        print(f"Monitor error: {e}")
        
    time.sleep(5)

