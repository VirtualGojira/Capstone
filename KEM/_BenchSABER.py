import re
import csv
import pandas as pd
import matplotlib.pyplot as plt

def parse_benchmark_file(filename):
    """
    Parse the given benchmark text file to extract:
    - KEM Variant name
    - Average Key Generation Time (s)
    - Average Encapsulation Time (s)
    - Average Decapsulation Time (s)
    """
    with open(filename, 'r') as f:
        content = f.read()

    # Use regex to extract required values
    variant_match = re.search(r"Variant:\s*(\S+)", content)
    keygen_match = re.search(r"Average times key_pair \(seconds\):\s*([\d\.]+)", content)
    encap_match = re.search(r"Average times enc \(seconds\):\s*([\d\.]+)", content)
    decap_match = re.search(r"Average times dec \(seconds\):\s*([\d\.]+)", content)
    
    variant = variant_match.group(1) if variant_match else "Unknown"
    keygen = float(keygen_match.group(1)) if keygen_match else None
    encap = float(encap_match.group(1)) if encap_match else None
    decap = float(decap_match.group(1)) if decap_match else None

    return {
        "KEM Variant": variant,
        "KeyGen Time (s)": keygen,
        "Encap Time (s)": encap,
        "Decap Time (s)": decap
    }

# List of text files for the SABER variants
files = ["firesaber_benchmark_output.txt", "saber_benchmark_output.txt", "lightsaber_benchmark_output.txt"]

# Parse each file and collect the results
results = [parse_benchmark_file(file) for file in files]

# Write the results to a CSV file
csv_filename = "_BenchSABER.csv"
with open(csv_filename, 'w', newline='') as csvfile:
    fieldnames = ["KEM Variant", "KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for res in results:
        writer.writerow(res)
print(f"CSV file '{csv_filename}' created.")

def plot_results(csv_filename):
    # Load CSV data into a DataFrame
    df = pd.read_csv(csv_filename)
    df.set_index("KEM Variant", inplace=True)
    
    # Create the bar chart for the times in seconds
    plt.figure(figsize=(3.15, 2.1))
    df[["KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"]].plot(kind='bar', figsize=(12,6))
    plt.title("KEM Benchmark Results")
    plt.ylabel("Time (s)")
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y')
    plt.tight_layout()
    
    # Save the plot as an EPS file
    eps_filename = '_BenchSABER.eps'
    plt.savefig(eps_filename, format='eps', dpi=600)
    plt.show()
    print(f"Plot saved as '{eps_filename}'.")

plot_results(csv_filename)
