from model import IntersectionModel, Vehicle, MechanicVehicle, VehicleState
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from collections import defaultdict
import os
from tqdm import tqdm

def compute_traffic_metrics(model: IntersectionModel) -> Dict:
    """
    Compute various traffic metrics for analysis.
    """
    # Get all vehicles (excluding mechanics)
    vehicles = [agent for agent in model.agents if isinstance(agent, Vehicle) 
               and not isinstance(agent, MechanicVehicle)]
    
    if not vehicles:
        return {
            "avg_happiness": 0,
            "avg_waiting_time": 0,
            "anger_rate": 0,
            "traffic_flow": 0,
            "breakdown_rate": 0,
            "intersection_congestion": 0,
            "total_vehicles": 0,
            "broken_vehicles": 0,
            "completed_per_broken": 0,
            "happiness_per_broken": 0,
            "broken_percentage": 0,
            "completion_percentage": 0
        }
    
    # Basic metrics
    broken_vehicles = len([v for v in vehicles if v.broken])
    completed_vehicles = len([v for v in vehicles if not v.active])
    total_vehicles = len(vehicles)
    avg_happiness = sum(v.happiness for v in vehicles) / total_vehicles
    
    # New metrics
    completed_per_broken = completed_vehicles / broken_vehicles if broken_vehicles > 0 else 0
    happiness_per_broken = avg_happiness / broken_vehicles if broken_vehicles > 0 else 0
    broken_percentage = (broken_vehicles / total_vehicles) * 100
    completion_percentage = (completed_vehicles / total_vehicles) * 100
    
    # Other metrics
    avg_waiting_time = sum(v.waiting_time for v in vehicles) / total_vehicles
    anger_rate = len([v for v in vehicles if v.state == VehicleState.ANGRY]) / total_vehicles
    
    # Calculate intersection congestion
    intersections = [(12, 11), (13, 11), (12, 12), (13, 12)]
    vehicles_at_intersections = sum(1 for v in vehicles if v.pos in intersections)
    intersection_congestion = vehicles_at_intersections / len(intersections) if vehicles_at_intersections > 0 else 0
    
    return {
        "avg_happiness": avg_happiness,
        "avg_waiting_time": avg_waiting_time,
        "anger_rate": anger_rate,
        "traffic_flow": completed_vehicles,
        "breakdown_rate": broken_vehicles,
        "intersection_congestion": intersection_congestion,
        "total_vehicles": total_vehicles,
        "broken_vehicles": broken_vehicles,
        "completed_per_broken": completed_per_broken,
        "happiness_per_broken": happiness_per_broken,
        "broken_percentage": broken_percentage,
        "completion_percentage": completion_percentage
    }

def run_simulation(params: Dict, steps: int = 100) -> List[Dict]:
    """
    Run a single simulation with given parameters for specified number of steps.
    """
    model = IntersectionModel(**params)
    results = []
    
    for step in range(steps):
        model.step()
        metrics = compute_traffic_metrics(model)
        metrics.update(params)
        metrics['step'] = step
        results.append(metrics)
    
    return results

def run_batch_analysis():
    """
    Run batch analysis with different parameter combinations.
    """
    # Define parameter ranges
    params_list = [
        {
            "vehicle_spawn_rate": spawn_rate,
            "min_vehicles": min_v,
            "max_vehicles": max_v,
            "width": 24,
            "height": 24
        }
        for spawn_rate in [0.1, 0.3, 0.5, 0.7, 0.9]
        for min_v in [5, 10, 15]
        for max_v in [20, 30, 40]
        if max_v > min_v
    ]
    
    # Run simulations
    all_results = []
    print(f"Running {len(params_list)} parameter combinations...")
    
    for params in tqdm(params_list):
        # Run each parameter set 3 times for statistical significance
        for run in range(3):
            simulation_results = run_simulation(params, steps=100)
            for result in simulation_results:
                result['run'] = run
            all_results.extend(simulation_results)
    
    return pd.DataFrame(all_results)

def analyze_results(results_df: pd.DataFrame):
    """
    Analyze and visualize the batch run results with focus on broken vehicles.
    """
    if not os.path.exists("analysis_plots"):
        os.makedirs("analysis_plots")
    
    plt.rcParams['figure.figsize'] = [12, 6]
    plt.rcParams['axes.grid'] = True
    
    # 1. Completion Rate vs Broken Vehicles over Time
    plt.figure(figsize=(15, 8))
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Completion Rate vs Broken Vehicles Over Time', fontsize=16)
    
    spawn_rates = sorted(results_df['vehicle_spawn_rate'].unique())
    for idx, spawn_rate in enumerate(spawn_rates):
        row = idx // 3
        col = idx % 3
        
        data = results_df[results_df['vehicle_spawn_rate'] == spawn_rate]
        
        scatter = axes[row, col].scatter(data['broken_percentage'], 
                                       data['completion_percentage'],
                                       c=data['step'],
                                       cmap='viridis',
                                       alpha=0.6)
        
        plt.colorbar(scatter, ax=axes[row, col], label='Time Step')
        
        axes[row, col].set_title(f'Spawn Rate: {spawn_rate}')
        axes[row, col].set_xlabel('Broken Vehicles (%)')
        axes[row, col].set_ylabel('Completed Vehicles (%)')
        
        z = np.polyfit(data['broken_percentage'], data['completion_percentage'], 1)
        p = np.poly1d(z)
        axes[row, col].plot(data['broken_percentage'], 
                          p(data['broken_percentage']), 
                          "r--", alpha=0.8)
    
    plt.tight_layout()
    plt.savefig("analysis_plots/completion_vs_broken_over_time.png")
    plt.close()

    # 2. Traffic Flow Analysis
    plt.figure()
    sns.lineplot(data=results_df, x='step', y='traffic_flow', 
                hue='vehicle_spawn_rate', ci=95)
    plt.title('Traffic Flow Over Time by Spawn Rate')
    plt.xlabel('Step')
    plt.ylabel('Completed Vehicles')
    plt.savefig("analysis_plots/traffic_flow.png")
    plt.close()

    # 3. Completion Percentage Over Time
    plt.figure()
    sns.lineplot(data=results_df, x='step', y='completion_percentage',
                hue='vehicle_spawn_rate', ci=95)
    plt.title('Vehicle Completion Percentage Over Time')
    plt.xlabel('Step')
    plt.ylabel('Completion Percentage (%)')
    plt.savefig("analysis_plots/completion_percentage_time.png")
    plt.close()

    # 4. Happiness Level per Broken Vehicle
    plt.figure()
    sns.boxplot(data=results_df, x='vehicle_spawn_rate', y='happiness_per_broken')
    plt.title('Happiness Level per Broken Vehicle by Spawn Rate')
    plt.xlabel('Spawn Rate')
    plt.ylabel('Happiness/Breakdown Ratio')
    plt.savefig("analysis_plots/happiness_per_breakdown.png")
    plt.close()
    
    # 5. Percentage of Broken Vehicles Over Time
    plt.figure()
    sns.lineplot(data=results_df, x='step', y='broken_percentage', 
                hue='vehicle_spawn_rate', ci=95)
    plt.title('Percentage of Broken Vehicles Over Time')
    plt.xlabel('Step')
    plt.ylabel('Broken Vehicles (%)')
    plt.savefig("analysis_plots/broken_percentage.png")
    plt.close()
    
    # 6. System Performance Matrix
    metrics = ['broken_percentage', 'completed_per_broken', 'happiness_per_broken', 
              'completion_percentage', 'traffic_flow', 'intersection_congestion']
    correlation = results_df[metrics].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation Matrix of System Performance Metrics')
    plt.tight_layout()
    plt.savefig("analysis_plots/performance_correlation.png")
    plt.close()
    
    # Save summary statistics
    summary_stats = results_df.groupby('vehicle_spawn_rate')[
        ['completed_per_broken', 'happiness_per_broken', 'broken_percentage',
         'completion_percentage', 'traffic_flow', 'intersection_congestion']
    ].agg(['mean', 'std', 'min', 'max'])
    summary_stats.to_csv("analysis_plots/summary_statistics.csv")
    
    # Print key findings
    print("\nKey Findings:")
    print(f"Average completion per breakdown: {results_df['completed_per_broken'].mean():.2f}")
    print(f"Average completion percentage: {results_df['completion_percentage'].mean():.2f}%")
    print(f"Average percentage of broken vehicles: {results_df['broken_percentage'].mean():.2f}%")
    print(f"Correlation between completion and breakdowns: {results_df['completion_percentage'].corr(results_df['broken_percentage']):.3f}")
    
    return summary_stats

def main():
    """
    Main function to run the batch analysis and generate insights.
    """
    print("Starting batch analysis...")
    results_df = run_batch_analysis()
    
    print("\nAnalyzing results...")
    summary_stats = analyze_results(results_df)
    
    print("\nSummary Statistics:")
    print(summary_stats)
    
    # Save full results
    results_df.to_csv("analysis_plots/full_results.csv", index=False)
    
    print("\nAnalysis complete! Check the 'analysis_plots' directory for visualizations.")

if __name__ == "__main__":
    main()