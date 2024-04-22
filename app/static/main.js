// Tooltip Initialization
document.addEventListener("DOMContentLoaded", function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Chart Generation
document.addEventListener('DOMContentLoaded', function () {
    if (window.cumulativeRevenue) {
        const canvas = document.getElementById('revenueChart');
        const ctx = canvas.getContext('2d');
        // Check if the chart instance already exists
        if (window.revenueChartInstance) {
            window.revenueChartInstance.destroy();
        }
        // Create the chart instance and store it on the window object
        window.revenueChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [...Array(window.cumulativeRevenue.length).keys()].map(i => `Week ${i + 1}`),
                datasets: [{
                    label: 'Cumulative Projected Revenue (£)',
                    data: window.cumulativeRevenue,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
});

// Initialize Sidebar
jQuery(document).ready(function ($) {

    $("#sidebar").mCustomScrollbar({
        theme: "minimal"
    });

    $('#sidebarCollapse').on('click', function () {
        // open or close navbar
        $('#sidebar').toggleClass('active');
    });

});