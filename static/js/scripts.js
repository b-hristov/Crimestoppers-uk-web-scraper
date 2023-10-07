document.addEventListener('DOMContentLoaded', function () {
    new DataTable('#data-table');
});

// Function to update the progress bar
function updateProgress(percent) {
    $("#progress-bar-fill").css("width", percent + "%");
}

// Function to trigger the scraper
$("#run-scraper-button").on("click", function () {
    let counter = 0
    $("#count").hide();
    $("#datetime").hide();
    $("#buttons").hide();
    $("#loading-message").show();
    updateProgress(counter);
    $("#progress-bar").show();
    $.ajax({
        type: "POST",
        url: "/run_scraper/",
        success: function () {
            setInterval(function () {
                $.get("/check_scraper_status/", function (data) {
                    if (!data.scraping_in_progress) {
                        updateProgress(100);
                        setTimeout(function () {
                            location.reload();
                        }, 1000);
                    } else {
                        if (counter < 100) {
                            counter += 5;
                            updateProgress(counter);
                        }
                    }
                });
            }, 10000);
        }
    });
});

// Function to erase all entries
$("#erase-all-entries").on('click', function () {
    $.ajax({
        type: 'POST',
        url: '/erase_all_entries/',
        success: function () {
            location.reload();
        }
    });
});
