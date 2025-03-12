import matplotlib.pyplot as plt
import re

# Read the text file
file_content = """
Running _BB84Naiveavg.py...
Average time taken over 100 runs: 1385.11 ms

================================================================================
Running _BB84ryrzavg.py...
Average time taken over 100 runs: 1453.80 ms

================================================================================
Running _BB84rzrxrzavg.py...
Average time taken over 100 runs: 1489.82 ms

================================================================================
"""

# Extract method names and times using regex
pattern = r"Running (.*?)\.\.\.\nAverage time taken over 100 runs: ([\d.]+) ms"
matches = re.findall(pattern, file_content)

# Process extracted data
methods = [match[0] for match in matches]  # Extract method names
times = [float(match[1]) for match in matches]  # Convert times to float

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))  # 600 DPI, 6x4 inches for high resolution
ax.bar(methods, times, color=['blue', 'green', 'red'])
ax.set_ylabel("Time (ms)")
ax.set_xlabel("Method")
ax.set_title("BB84 Benchmarking Results")
ax.set_xticklabels(methods, rotation=45, ha='right')
plt.savefig('_BenchBB84.eps', format='eps', dpi=600)

# Show the graph
plt.show()
