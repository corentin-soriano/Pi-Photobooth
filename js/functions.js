/**
 * This file contains js project functions.
 */

/**
 * Hide countdown overlay and display review overlay.
 * 
 * @param message
 *      Text message to print on review overlay.
 * 
 */
function switchOverlays(message, img_path) {

    /* Mask countdown-overlay */
    $('#countdown-overlay').text();
    $('#countdown-overlay').hide();

    /* Review captured photo */
    $('#review-overlay').show();
    $('#review-message').text(message ?? '');
    
    if (message === null) {
        $('#review-message').hide();
        $('#review').show();
        $('#review #photo img').attr('src', img_path);
        $('#review #qrcode img').attr('src', 'qrcode/' + img_path.split('/').pop());
    } else {
        $('#review-message').show();
        $('#review').hide();
    }

}

/**
 * Called when #captureImage button is pressed.
 */
function captureImage() {

    /* Countdown before capture */
    let counter = 3;

    /* Display countdown overlay */
    $('#countdown-overlay').show();
    $('#countdown-overlay').text(counter);

    /* Countdown and capture photo */
    const countdownInterval = setInterval(function() {
        counter--;

        if (counter > 0) {
            /* Display new value */
            $('#countdown-overlay').text(counter);
        } else {

            /* Display waiting message */
            $('#countdown-overlay').text('Souriez !');

            /* Get actual background */
            background = $('.background-item.selected').data('background');

            /* Take photo */
            fetch('/capture/' + background)
                .then(response => {
                    if (response.ok) {
                        return response.text();
                    } else {
                        switchOverlays('Erreur lors de la capture de l\'image.', null);
                    }
                })
                .then (data => {
                    switchOverlays(null, data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    switchOverlays('Erreur d\'accès au serveur d\'application, image non sauvegardée.', null);
                });

            /* Stop countdown */
            clearInterval(countdownInterval);
        }
    }, 1000);

}

/**
 * Generate background list.
 */
function generateBackgroundList() {

    /* Download background items list */
    $.ajax({
        url: '/background/list',
        method: 'GET',
        success: function(data) {

            /* Json list with all available backgrounds */
            data.forEach(function(imageName) {
                /* Add new item list for each available background */
                var listItem = '<li class="background-item" data-background="' + imageName + '"><img src="/background/' + imageName + '" /></li>';
                $('#background-list').append(listItem);
            });

            /* Add event listener on items */
            bgItemEventListenerAdd();
        },
        error: function(error) {
            console.log('Error retrieving list of images:', error);
        }
    });
}

/**
 * Check if admin button is enabled or not.
 * Settings can be visible only when this button is enabled.
 */
function checkGPIOAdmin() {

    /* GET admin button state */
    $.ajax({
        url: '/gpio/admin_button',
        method: 'GET',
        success: function(response) {
            /* Admin mode enabled */
            if (response.state === true) {
                /* Display settings button */
                $('#settings-open').show();
                $('#temperature-close').show();
            }
            /* Admin mode disabled */
            else {
                /* Hide settings button and overlay */
                $('#settings-overlay').hide();
                $('#settings-open').hide();
                $('#temperature-close').hide();
            }
        },
        error: function(error) {
            console.error('Error checking GPIO PIN State:', error);
        }
    });
}

/**
 * Check if RPI is not overheating and block access if necessary.
*/
function checkCPUTemp() {

    /* GET admin button state */
    $.ajax({
        url: '/health/temp',
        method: 'GET',
        success: function(response) {

            /* Get displayed temp */
            displayed_temp = $('#temp-value').text();

            /* Too hot, block access */
            if (response.temp >= 80 && displayed_temp == 0) {

                /* Display overlay */
                $('#temperature-overlay').show();

                /* Stop video stream */
                $('#preview-img').data('src', $('#preview-img').attr('src'));
                $('#preview-img').removeAttr('src');

                /* Update displayed temperature */
                $('#temp-value').text(response.temp);
            }
            
            /* Correct temperature but wait a bit more */
            else if (response.temp >= 70 && displayed_temp > 0) {

                /* Hide overlay */
                $('#temperature-overlay').show();
                
                /* Update displayed temperature */
                $('#temp-value').text(response.temp);
            }
            /* Correct temperature, grant access */
            else if (displayed_temp > 0) {

                /* Hide overlay */
                $('#temperature-overlay').hide();

                /* Restart video stream */
                $('#preview-img').attr('src', $('#preview-img').data('src'));
                $('#preview-img').removeAttr('data-src');

                /* Reset displayed temperature */
                $('#temp-value').text(0);
            }
            /* Otherwise, do nothing */

        },
        error: function(error) {
            console.error('Error checking CPU temperature:', error);
        }
    });
}

/**
 * Poweroff or reboot raspberry.
 * 
 * @param {string} action
 *      Reboot or shutdown requested.
 */
function power(action) {

    /* Send reboot or shutdown to RPI */
    $.ajax({
        url: '/power/' + action,
        method: 'GET',
        success: function(response) {
            console.log(response.state);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}
