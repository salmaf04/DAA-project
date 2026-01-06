import time
import random
import csv
import matplotlib.pyplot as plt
import pandas as pd
from solutions.dp_solution import solve_discrete_transport
from solutions.efficient_solution import efficient_solution


# 1. ROBUST CASE GENERATOR

def generate_random_case(n, num_mules, difficulty="normal"):
    mule_caps = [50] * num_mules  # Fixed base capacity for control
    articles = []
    
    if difficulty == "normal":
        for _ in range(n):
            articles.append((random.randint(10, 100), random.randint(1, 20)))
    elif difficulty == "tight": 
        # Heavy articles (30-60% of a mule's capacity)
        for _ in range(n):
            articles.append((random.randint(50, 100), random.randint(15, 30)))
    elif difficulty == "tiny":
        for _ in range(n):
            articles.append((random.randint(1, 10), random.randint(1, 5)))
    elif difficulty == "greedy_trap":
        articles = [(100, 10), (100, 10), (90, 10), (80, 10)]
        while len(articles) < n:
            articles.append((5, 1))

    return articles, mule_caps


# 2. MASSIVE EXPERIMENTATION ENGINE

def run_mass_experiment_battery():
    print(f"\n{'='*20} STARTING 100+ TEST CASES {'='*20}")
    
    # Define the test scenario to cover more than 100 configurations
    # N ranges from small (safe for DP) to medium (where DP struggles)
    # Note: we avoid very large N (e.g., 100) here because the DP solver would take too long.
    # To evaluate the approximation at larger N, run a separate test without DP.
    n_range = range(5, 23)
    case_types = ["normal", "tight", "greedy_trap", "tiny"]
    repetitions = 2  # Repeat each configuration to reduce noise
    
    export_data = []
    total_cases = len(n_range) * len(case_types) * repetitions
    counter = 0

    print(f"{'Case':<4} | {'N':<3} | {'Type':<10} | {'Exact(s)':<10} | {'Approx(s)':<10} | {'Gap(%)':<8} | {'Status'}")
    print("-" * 80)

    for n in n_range:
        for case_type in case_types:
            for _ in range(repetitions):
                counter += 1
                items, caps = generate_random_case(n, num_mules=3, difficulty=case_type)
                
                # --- Run DP (with logical timeout) ---
                # Skip DP execution when N is too large to keep the script responsive
                exact_time = -1
                exact_result = -1
                
                if n <= 18:  # Safety limit for the massive battery
                    start = time.time()
                    try:
                        exact_result, _ = solve_discrete_transport(items, caps)
                        exact_time = time.time() - start
                    except RecursionError:
                        exact_result = "RecError"
                    except Exception:
                        exact_result = "Error"
                else:
                    exact_result = "Skipped"

                # --- Run approximation ---
                start = time.time()
                approx_result, _, discarded = efficient_solution(items, caps)
                approx_time = time.time() - start
                
                # --- Compute metrics ---
                gap_value = None
                gap_display = "N/A"
                status = "OK"

                # Comparison logic
                if isinstance(exact_result, (int, float)) and exact_result != float('inf'):
                    if exact_result == 0:
                        gap_value = 0.0 if approx_result == 0 else 100.0
                    else:
                        gap_value = round(((approx_result - exact_result) / exact_result) * 100, 2)
                    gap_display = gap_value
                elif exact_result == float('inf'):
                    status = "Exact-Infeasible"
                    gap_display = "N/A"

                if len(discarded) > 0:
                    status = f"Approx-Discard({len(discarded)})"

                # Print line
                print(f"{counter:<4} | {n:<3} | {case_type:<10} | {exact_time:<10.5f} | {approx_time:<10.5f} | {gap_display:<8} | {status}")

                # Store data
                export_data.append({
                    "N": n,
                    "Type": case_type,
                    "Exact_Time": exact_time if isinstance(exact_time, float) and exact_time > 0 else None,
                    "Approx_Time": approx_time,
                    "Exact_Result": exact_result,
                    "Approx_Result": approx_result,
                    "Gap": gap_value,
                    "Approx_Discarded": len(discarded)
                })

    # Export to CSV for later analysis
    keys = export_data[0].keys()
    with open('transport_results.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(export_data)
    
    print(f"\n>>> Data saved to 'transport_results.csv' ({len(export_data)} records).")
    return export_data


# 3. BREAKPOINT FINDER (60 SECONDS)

def find_bruteforce_limit_60s():
    print("\n" + "="*30)
    print(">>> SEARCHING FOR BREAKPOINT (Limit: 60s)")
    print("="*30)
    
    n = 10
    mule_count = 3
    time_limit = 60.0 
    
    while True:
        items, caps = generate_random_case(n, mule_count, "normal")
        
        print(f"Testing N={n}, Mules={mule_count}...", end=" ", flush=True)
        
        start = time.time()
        try:
            solve_discrete_transport(items, caps)
            duration = time.time() - start
            print(f"Time: {duration:.4f}s")
        except RecursionError:
            print("ERROR: RecursionError (Stack overflow)")
            break
            
        if duration > time_limit:
            print(f"\n[!] LIMIT REACHED: At N={n} with {mule_count} mules, the runtime exceeded 60s.")
            break
        
        # Safety increments to avoid long waits when the solver is fast
        if duration < 1.0:
            n += 2
        else:
            n += 1


# 4. PLOT GENERATOR

def generate_plots(data_list):
    if not data_list:
        return
    df = pd.DataFrame(data_list)
    
    # Filter valid DP entries
    df_dp = df.dropna(subset=['Exact_Time'])
    
    plt.figure(figsize=(14, 6))

    # Plot 1: Time comparison (log scale)
    plt.subplot(1, 2, 1)
    plt.plot(df_dp['N'], df_dp['Exact_Time'], 'o-', label='Exact (DP)', color='red')
    plt.plot(df['N'], df['Approx_Time'], 'x-', label='Approximation', color='blue')
    plt.yscale('log')
    plt.xlabel('Number of Items (N)')
    plt.ylabel('Time (seconds) - Log Scale')
    plt.title('Scalability: Exact vs Approximation')
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()

    # Plot 2: Quality (Gap) by type
    plt.subplot(1, 2, 2)
    # Filter entries where the gap was computed
    df_gap = df.dropna(subset=['Gap'])
    for case_type in df_gap['Type'].unique():
        subset = df_gap[df_gap['Type'] == case_type]
        plt.scatter(subset['N'], subset['Gap'], label=case_type, alpha=0.7)
    
    plt.xlabel('Number of Items (N)')
    plt.ylabel('Gap of Optimality (%)')
    plt.title('Solution Quality (Lower is better)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('empirical_analysis.png')
    print(">>> Charts saved as 'empirical_analysis.png'")
    plt.show()
