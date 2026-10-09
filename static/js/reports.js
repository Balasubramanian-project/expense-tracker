document.addEventListener('DOMContentLoaded', function () {
    fetchReportCharts();
});

function fetchReportCharts() {
    const urlParams = new URLSearchParams(window.location.search);
    const period = urlParams.get('period') || 'monthly';
    const startDate = urlParams.get('start_date') || '';
    const endDate = urlParams.get('end_date') || '';

    const apiUrl = `/api/reports/chart-data?period=${encodeURIComponent(period)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;

    fetch(apiUrl)
        .then(res => res.json())
        .then(data => {
            initReportsTimeline(data.timeline);
            initReportsPie(data.category_pie);
        })
        .catch(err => console.error('Error loading report charts:', err));
}

function initReportsTimeline(timelineData) {
    const ctx = document.getElementById('reportsTimelineChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: timelineData.labels,
            datasets: [
                {
                    type: 'line',
                    label: 'Income (₹)',
                    data: timelineData.income,
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.2
                },
                {
                    type: 'bar',
                    label: 'Expenses (₹)',
                    data: timelineData.expenses,
                    backgroundColor: 'rgba(239, 68, 68, 0.75)',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return `${ctx.dataset.label}: ₹${ctx.raw.toLocaleString('en-IN')}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (v) { return '₹' + v.toLocaleString('en-IN'); }
                    }
                }
            }
        }
    });
}

function initReportsPie(pieData) {
    const ctx = document.getElementById('reportsPieChart');
    if (!ctx) return;

    if (!pieData.labels || pieData.labels.length === 0) {
        ctx.parentElement.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="bi bi-pie-chart fs-1 opacity-50"></i>
                <p class="small mt-2">No category data for selected period</p>
            </div>`;
        return;
    }

    const chartColors = [
        '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#ec4899', '#f97316', '#64748b', '#14b8a6'
    ];

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: pieData.labels,
            datasets: [{
                data: pieData.values,
                backgroundColor: chartColors.slice(0, pieData.labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ` ${ctx.label}: ₹${ctx.raw.toLocaleString('en-IN')}`;
                        }
                    }
                }
            }
        }
    });
}
