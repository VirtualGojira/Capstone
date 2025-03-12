import subprocess

scripts = ["_BB84Naiveavg.py", "_BB84ryrzavg.py", "_BB84rzrxrzavg.py"]

with open("result.txt", "w") as result_file:
    for script in scripts:
        result_file.write(f"Running {script}...\n")
        print(f"Running {script}...")

        result = subprocess.run(["python", script], capture_output=True, text=True)
        
        # Write output and errors to file
        result_file.write(result.stdout)
        result_file.write(result.stderr)
        result_file.write("\n" + "=" * 80 + "\n")  # Separator for readability

        # Also print output to console
        print(result.stdout)
        print(result.stderr)
