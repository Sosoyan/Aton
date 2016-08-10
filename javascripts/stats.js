var apiRoot = "https://api.github.com/";

// Display the stats
function showStats(data) {

    var err = false;
    var errMessage = '';

    if(data.status == 404) {
        err = true;
        errMessage = "The project does not exist!";
    }

    if(data.length == 0) {
        err = true;
        errMessage = "There are no releases for this project";
    }

    var html = '';

    if(err) {
        html = "<div>" + errMessage + "</div>";
    } else {
        html += "<div>";

        var releaseAssets = data.assets;
        var hasAssets = releaseAssets.length != 0;

        if(hasAssets) {

            $.each(releaseAssets, function(index, asset) {
            var assetSize = (asset.size / 1000000.0).toFixed(2);
            var lastUpdate = asset.updated_at.split("T")[0];
            html += "<p>" + asset.name + " (" + assetSize + "MB)<span id='downloads-result'></span><br><i>Last updated on " + lastUpdate + "</i></p>";

            });

        }
        html += "</div>";
    }

    var resultDiv = $("#stats-result");
    resultDiv.hide();
    resultDiv.html(html);
    $("#loader-gif").hide();
    resultDiv.slideDown();
}

function showDownloads(data) {

    var err = false;
    var errMessage = '';

    if(data.status == 404) {
        err = true;
        errMessage = "The project does not exist!";
    }

    if(data.length == 0) {
        err = true;
        errMessage = "There are no releases for this project";
    }

    var html = '';

    if(err) {
        html = "<div>" + errMessage + "</div>";
    } else {
        var total = 0;
        $.each(data, function(index, item) {

            var releaseAssets = item.assets;
            var hasAssets = releaseAssets.length != 0;

            if(hasAssets) {

                $.each(releaseAssets, function(index, asset) {
                    var assetSize = (asset.size / 1000000.0).toFixed(2);
                    var lastUpdate = asset.updated_at.split("T")[0];
                    total += asset.download_count;

                });
            }
        });

        html += " - Downloaded " + total + " times."
    }

    var resultDiv = $("#downloads-result");
    resultDiv.html(html);
    $("#loader-gif").hide();
    resultDiv.slideDown();
}

// Callback function for getting release stats
function getStats() {
    var user = 'Sosoyan';
	var repository = 'Aton';

    var url = apiRoot + "repos/" + user + "/" + repository + "/releases/latest";
    var url2 = apiRoot + "repos/" + user + "/" + repository + "/releases";
    $.getJSON(url, showStats).fail(showStats);
    setTimeout(function(){$.getJSON(url2, showDownloads).fail(showDownloads)}, 500);

}
getStats();
