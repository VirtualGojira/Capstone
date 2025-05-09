import numpy as np
import re

# Option 1: Custom parsing approach
with open('LAB_results.txt', 'r') as file:
    lines = file.readlines()
    
# Extract numbers from each line using regex
data = []
for line in lines:
    # Remove brackets and extract numbers
    numbers = re.findall(r'\d+', line)
    data.append([int(num) for num in numbers])

# Convert to numpy array
data = np.array(data)
print(data.shape)

mean_values = np.mean(data, axis=0)
std_dev_values = np.std(data, axis=0)

for i in range(1):
    print(f"{round(mean_values[i], 2)} +- {round(std_dev_values[i], 2)}")

