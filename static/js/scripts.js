// // Function to trigger the scraper
// document.getElementById("run-scraper-button").addEventListener("click", function () {
//     // Show the progress bar
//     document.getElementById("spinner").style.display = "block";
//
//     // Make an AJAX request to the endpoint
//     var xhr = new XMLHttpRequest();
//     xhr.open("POST", "/run_scraper/", true);
//     xhr.onreadystatechange = function () {
//         if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
//             var response = JSON.parse(xhr.responseText);
//             if (response.status === "Scraping complete") {
//                 // Hide the progress bar
//                 document.getElementById("spinner").style.display = "none";
//
//                 // Reload the page
//                 location.reload();
//             }
//         }
//     };
//     xhr.send();
// });

document.getElementById("run-scraper-button").addEventListener("click", function () {
  document.getElementById("spinner").style.display = "block";
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
              document.getElementById("spinner").style.display = "none";
              location.reload();
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