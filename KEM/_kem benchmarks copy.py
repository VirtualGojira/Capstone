import oqs
import time
import csv
import matplotlib.pyplot as plt
import pandas as pd

KEM_VARIANTS = {
    "Kyber": [
        "Kyber512",
        "Kyber768",
        "Kyber1024"
    ],
    "NTRU": [
        "sntrup761"
    ],
    "FrodoKEM": [
        "FrodoKEM-640-AES", 
        "FrodoKEM-640-SHAKE", 
        "FrodoKEM-976-AES", 
        "FrodoKEM-976-SHAKE", 
        "FrodoKEM-1344-AES", 
        "FrodoKEM-1344-SHAKE"
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

        assert shared_secret_enc == shared_secret_dec, "Shared secrets do not match!"
    
    kem.free()
    
    return {
        "keygen_avg": sum(keygen_times) / iterations,
        "encap_avg": sum(encap_times) / iterations,
        "decap_avg": sum(decap_times) / iterations,
    }

def plot_results(csv_filename):
    df = pd.read_csv(csv_filename)
    df.set_index("KEM Variant", inplace=True)
    
    plt.figure(figsize=(12, 6))
    df[["KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"]].plot(kind='bar', figsize=(12,6))
    plt.title("KEM Benchmark Results")
    plt.ylabel("Time (s)")
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y')
    plt.tight_layout()
    ###plt.savefig('destination_path.eps', format='eps', dpi=1000)
    plt.show()

def main():
    results = []
    iterations = 1000  # Adjust for more or fewer iterations
    
    for family, variants in KEM_VARIANTS.items():
        for variant in variants:
            print(f"Benchmarking {variant} ({family})...")
            result = benchmark_kem(variant, iterations)
            results.append([variant, family, result["keygen_avg"], result["encap_avg"], result["decap_avg"]])
    
    # Write results to CSV
    csv_filename = "kem_benchmark_results.csv"
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["KEM Variant", "Family", "KeyGen Time (s)", "Encap Time (s)", "Decap Time (s)"])
        writer.writerows(results)
    
    # Write results to text file
    with open("kem_benchmark_results.txt", "w") as f:
        f.write("KEM Variant | Family | KeyGen Time (s) | Encap Time (s) | Decap Time (s)\n")
        f.write("-" * 70 + "\n")
        for row in results:
            f.write(f"{row[0]} | {row[1]} | {row[2]:.6f} | {row[3]:.6f} | {row[4]:.6f}\n")
    
    print("Benchmark completed. Results saved to kem_benchmark_results.csv and kem_benchmark_results.txt")
    
    # Generate and show graphs
    plot_results(csv_filename)

if __name__ == "__main__":
    main()
