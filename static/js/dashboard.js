document.addEventListener('DOMContentLoaded', function () {
    fetchDashboardCharts();
});

function fetchDashboardCharts() {
    fetch('/api/dashboard/chart-data')
        .then(response => response.json())
        .then(data => {
            initTrendChart(data.trend_chart);
            initCategoryChart(data.category_chart);
        })
        .catch(err => console.error('Error fetching dashboard chart data:', err));
}

function initTrendChart(trendData) {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.labels,
            datasets: [
                {
                    label: 'Income (₹)',
                    data: trendData.income,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Expenses (₹)',
                    data: trendData.expenses,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ₹${context.raw.toLocaleString('en-IN')}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}

function initCategoryChart(categoryData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    const chartColors = [
        '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#ec4899', '#f97316', '#64748b', '#14b8a6'
    ];

    if (!categoryData.labels || categoryData.labels.length === 0) {
        ctx.parentElement.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="bi bi-pie-chart fs-1 opacity-50"></i>
                <p class="small mt-2">No expenses logged for this month</p>
            </div>`;
        return;
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data: categoryData.datasets[0].data,
                backgroundColor: chartColors.slice(0, categoryData.labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
                        boxWidth: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw;
                            return ` ${context.label}: ₹${value.toLocaleString('en-IN')}`;
                        }
                    }
                }
            }
        }
    });
}
