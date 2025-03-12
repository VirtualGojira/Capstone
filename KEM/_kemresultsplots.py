import csv
import matplotlib.pyplot as plt
import pandas as pd

def plot_results(csv_filename):
    df = pd.read_csv(csv_filename)
    df.set_index("KEM Variant", inplace=True)
    
    # Plot KeyGen times
    plt.figure(figsize=(12, 6))
    df["KeyGen Time (s)"].plot(kind='bar', color='blue')
    plt.title("KeyGen Benchmark Results")
    plt.ylabel("Time (s)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("keygen_benchmark_results.png")
    plt.show()
    
    # Plot Encap times
    plt.figure(figsize=(12, 6))
    df["Encap Time (s)"].plot(kind='bar', color='green')
    plt.title("Encap Benchmark Results")
    plt.ylabel("Time (s)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("encap_benchmark_results.png")
    plt.show()
    
    # Plot Decap times
    plt.figure(figsize=(12, 6))
    df["Decap Time (s)"].plot(kind='bar', color='red')
    plt.title("Decap Benchmark Results")
    plt.ylabel("Time (s)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("decap_benchmark_results.png")
    plt.show()

plot_results("_kem_benchmark_results.csv")