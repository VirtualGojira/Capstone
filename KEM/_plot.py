import csv
import matplotlib.pyplot as plt
import pandas as pd

def plot_results(csv_filename):
    df = pd.read_csv(csv_filename)
    df.set_index("KEM Variant", inplace=True)
    
    plt.figure(figsize=(3.15, 2.1))
    df[["KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"]].plot(kind='bar', figsize=(12,6))
    plt.title("KEM Benchmark Results")
    plt.ylabel("Time (s)")
    plt.yscale('log')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig('_BenchFASTEST.eps', format='eps', dpi=600)
    plt.show()

plot_results("_BenchFASTEST.csv")