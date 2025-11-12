import subprocess
import time

command = ["uv", "run", "stats-code", "../cpython"]
# command = ["uv", "run", "stats-code", "./"]
# command = ["uv", "run", "stats-code", "../cpython"]
# command = ["stats-code", "../cpython"]


times = []

for i in range(30):
    start_time = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    times.append(elapsed_time)
    print(f"run {i + 1}: {elapsed_time:.4f}s")

average_time = sum(times) / len(times)
print(f"average time: {average_time:.4f}s")
