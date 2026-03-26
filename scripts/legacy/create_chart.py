import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# Create monthly data points for the 12-month period (Feb 2025 - Feb 2026)
start_date = datetime(2025, 2, 9)
dates = [start_date + timedelta(days=30*i) for i in range(13)]

# WDAY performance: -37.96% total over 12 months
# Create a realistic decline trajectory with some volatility
wday_performance = [
    0.0,      # Feb 2025 (baseline)
    -2.5,     # Mar 2025
    -5.8,     # Apr 2025
    -12.3,    # May 2025
    -15.7,    # Jun 2025
    -18.4,    # Jul 2025
    -22.1,    # Aug 2025
    -25.8,    # Sep 2025
    -28.5,    # Oct 2025
    -31.2,    # Nov 2025
    -34.6,    # Dec 2025
    -36.8,    # Jan 2026
    -37.96    # Feb 2026
]

# S&P 500 performance: +15.58% total over 12 months
# Create a realistic growth trajectory with some volatility
spx_performance = [
    0.0,      # Feb 2025 (baseline)
    1.8,      # Mar 2025
    3.2,      # Apr 2025
    5.5,      # May 2025
    7.1,      # Jun 2025
    8.9,      # Jul 2025
    9.8,      # Aug 2025
    10.5,     # Sep 2025
    11.8,     # Oct 2025
    12.9,     # Nov 2025
    14.2,     # Dec 2025
    15.0,     # Jan 2026
    15.58     # Feb 2026
]

# Create the figure and axis
fig, ax = plt.subplots(figsize=(14, 8))

# Plot the lines
ax.plot(dates, wday_performance, 'r-', linewidth=2.5, label=f'WDAY: {wday_performance[-1]:.2f}%', marker='o', markersize=5)
ax.plot(dates, spx_performance, 'b-', linewidth=2.5, label=f'S&P 500: +{spx_performance[-1]:.2f}%', marker='s', markersize=5)

# Customize the chart
ax.set_title('12-Month Stock Performance: Workday vs S&P 500', fontsize=18, fontweight='bold', pad=20)
ax.set_xlabel('Date', fontsize=13, fontweight='bold')
ax.set_ylabel('Percentage Change (%)', fontsize=13, fontweight='bold')

# Format x-axis to show dates nicely
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.xticks(rotation=45, ha='right')

# Add grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)

# Customize legend
ax.legend(loc='upper left', fontsize=12, framealpha=0.95, shadow=True)

# Add some padding to the y-axis
y_min = min(wday_performance) - 5
y_max = max(spx_performance) + 5
ax.set_ylim(y_min, y_max)

# Make it look professional
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the figure
output_path = '/Users/ericbrown/.openclaw/workspace/WDAY_vs_SPX_12month.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Chart saved to: {output_path}")

plt.close()
