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

// Delete journey function
function confirmDelete(journey_id) {
    if (confirm("Are you sure you want to delete this journey?")) {
        // Send a confirmation dialog to the user
        fetch('/delete_journey/' + journey_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Display success message or handle success scenario
                console.log(data.message);
                location.reload();
            } else {
                // Display error message or handle error scenario
                console.error(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}