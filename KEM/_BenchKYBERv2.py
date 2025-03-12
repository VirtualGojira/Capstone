import oqs
import time
import csv
import matplotlib.pyplot as plt
import numpy as np

# Define the KEM variants
KEM_VARIANTS = {
    "Kyber": [
        "Kyber512",
        "Kyber768",
        "Kyber1024"
    ]
}

def benchmark_kem(variant, iterations=1000):
    kem = oqs.KeyEncapsulation(variant)
    keygen_times = []
    encap_times = []
    decap_times = []

    for _ in range(iterations):
        # Key generation benchmark
        start = time.perf_counter()
        public_key = kem.generate_keypair()
        end = time.perf_counter()
        keygen_times.append(end - start)

        # Encapsulation benchmark
        start = time.perf_counter()
        ciphertext, shared_secret_enc = kem.encap_secret(public_key)
        end = time.perf_counter()
        encap_times.append(end - start)

        # Decapsulation benchmark
        start = time.perf_counter()
        shared_secret_dec = kem.decap_secret(ciphertext)
        end = time.perf_counter()
        decap_times.append(end - start)

        # Verify that encapsulated and decapsulated secrets match
        assert shared_secret_enc == shared_secret_dec, "Shared secrets do not match!"
    
    kem.free()
    
    return {
        "keygen_times": keygen_times,
        "encap_times": encap_times,
        "decap_times": decap_times,
        "keygen_avg": sum(keygen_times) / iterations,
        "encap_avg": sum(encap_times) / iterations,
        "decap_avg": sum(decap_times) / iterations,
    }

def generate_grouped_bar_chart(results):
    """
    Generates a grouped bar chart comparing the average times for key generation,
    encapsulation, and decapsulation for each KEM variant.
    """
    # Unpack the results
    variants = [row[0] for row in results]
    keygen_avg = [row[2] for row in results]
    encap_avg = [row[3] for row in results]
    decap_avg = [row[4] for row in results]
    
    x = np.arange(len(variants))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, keygen_avg, width, label='KeyGen')
    ax.bar(x, encap_avg, width, label='Encap')
    ax.bar(x + width, decap_avg, width, label='Decap')
    
    ax.set_ylabel('Time (s)')
    ax.set_title('Average KEM Operation Times')
    ax.set_xticks(x)
    ax.set_xticklabels(variants)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig("kem_grouped_bar_chart.png")
    plt.show()

def generate_box_plot(benchmarks):
    """
    Generates box plots for the full distribution of times for key generation,
    encapsulation, and decapsulation across KEM variants.
    """
    variants = list(benchmarks.keys())
    keygen_data = [benchmarks[variant]["keygen_times"] for variant in variants]
    encap_data = [benchmarks[variant]["encap_times"] for variant in variants]
    decap_data = [benchmarks[variant]["decap_times"] for variant in variants]
    
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    
    # Box plot for key generation times
    axs[0].boxplot(keygen_data, labels=variants)
    axs[0].set_title("Key Generation Times")
    axs[0].set_ylabel("Time (s)")
    
    # Box plot for encapsulation times
    axs[1].boxplot(encap_data, labels=variants)
    axs[1].set_title("Encapsulation Times")
    
    # Box plot for decapsulation times
    axs[2].boxplot(decap_data, labels=variants)
    axs[2].set_title("Decapsulation Times")
    
    plt.suptitle("Distribution of KEM Operation Times over 1000 Iterations")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("kem_box_plots.png")
    plt.show()

def main():
    results = []        # List to hold average time results for CSV/text output.
    benchmarks = {}     # Dictionary to hold full timing distributions for plotting.
    iterations = 1000   # Number of iterations for benchmarking
    
    # Run benchmarks for each KEM variant.
    for family, variants in KEM_VARIANTS.items():
        for variant in variants:
            print(f"Benchmarking {variant} ({family})...")
            result = benchmark_kem(variant, iterations)
            benchmarks[variant] = result
            results.append([variant, family, result["keygen_avg"], result["encap_avg"], result["decap_avg"]])
    
    # Write average results to CSV.
    with open("_BenchKYBER.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["KEM Variant", "Family", "KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"])
        writer.writerows(results)
    
    # Write average results to text file.
    with open("_BenchKYBER.txt", "w") as f:
        f.write("KEM Variant | Family | KeyGen Time (s) | Encap Time (s) | Decap Time (s)\n")
        f.write("-" * 70 + "\n")
        for row in results:
            f.write(f"{row[0]} | {row[1]} | {row[2]:.6f} | {row[3]:.6f} | {row[4]:.6f}\n")
    
    print("Benchmark completed. Results saved to _BenchKYBER.csv and _BenchKYBER.txt")
    
    # Generate graphs.
    generate_grouped_bar_chart(results)
    generate_box_plot(benchmarks)

if __name__ == "__main__":
    main()
