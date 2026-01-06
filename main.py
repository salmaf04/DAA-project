from experimental_analysis.experimental_analysis import run_mass_experiment_battery, generate_plots, find_bruteforce_limit_60s
if __name__ == "__main__":
    
    #1. Run the large test suite for CSV and statistics.
    datos = run_mass_experiment_battery()
    
    # 2. Generate graphs if pandas/matplotlib are installed
    try:
       generate_plots(datos)
    except Exception as e:
        print(f"Graphs could not be generated: {e}")

    # 3. Find the exact 60-second limit.
    find_bruteforce_limit_60s()