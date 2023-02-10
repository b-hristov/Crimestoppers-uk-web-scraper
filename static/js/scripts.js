// Function to update the progress bar
let fill = document.getElementById("progress-bar-fill");
function updateProgress(percent) {
    fill.style.width = percent + "%";
}

let counter = 0

// Function to trigger the scraper
document.getElementById("run-scraper-button").addEventListener("click", function () {
    document.getElementById("count").style.display = "none";
    document.getElementById("loading-message").style.display = "block";
    updateProgress(counter);
    document.getElementById("progress-bar").style.display = "block";
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/run_scraper/", true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            setInterval(function () {
                var xhr2 = new XMLHttpRequest();
                xhr2.open("GET", "/check_scraper_status/", true);
                xhr2.onreadystatechange = function () {
                    if (xhr2.readyState === XMLHttpRequest.DONE && xhr2.status === 200) {
                        var data = JSON.parse(xhr2.responseText);
                        if (!data.scraping_in_progress) {
                            updateProgress(100);
                            setTimeout(function () {
                                location.reload();
                            }, 2000);
                        } else {
                            counter += 3;
                            updateProgress(counter);
                        }
                    }
                };
                xhr2.send();
            }, 10000);
        }
    };
    xhr.send();
});

// Function to erase all entries
document.getElementById("erase-all-entries").addEventListener('click', function () {
    // Make an AJAX request to the endpoint
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/erase_all_entries/', true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            location.reload()
        }
    };
    xhr.send();
});