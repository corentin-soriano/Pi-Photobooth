/**
 * This file contains js project functions.
 */

/**
 * Fetch translations from the server.
 *
 * This function sends an AJAX request to fetch translations from the server.
 * It returns a Promise that resolves with the response or rejects with an error.
 *
 * @returns {Promise<Object>} A promise that resolves with the response data.
 */
function translations() {

    /* Request translations */
    return new Promise((resolve, reject) => {
        $.ajax({
            url: '/translations',
            method: 'GET',
            success: function(response) {
                resolve(response);
            },
            error: function(error) {
                reject(error);
            }
        });
    });
}

/**
 * Hide countdown overlay and display review overlay.
 * 
 * @param {String} message Text message to print on review overlay.
 * 
 * @param {String} img_path Path of picture.
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
 * 
 * @param {string} lang Json containing all label translations.
 */
function captureImage(lang) {

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
            $('#countdown-overlay').text(lang.wait_capture);

            /* Get actual background */
            let background = $('.background-item.selected').data('background');

            /* Take photo */
            fetch('/capture/' + background)
                .then(response => {
                    if (response.ok) {
                        return response.text();
                    } else {
                        switchOverlays(lang.error_capture, null);
                    }
                })
                .then (data => {
                    switchOverlays(null, data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    switchOverlays(lang.error_capture_network, null);
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
                let listItem = '<li class="background-item" data-background="' + imageName + '"><img src="/background/' + imageName + '" /></li>';
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
                $('#refresh').show();
                $('#temperature-close').show();
                $('#print-close').show();
            }
            /* Admin mode disabled */
            else {
                /* Hide settings button and overlay */
                $('#settings-overlay').hide();
                $('#settings-open').hide();
                $('#refresh').hide();
                $('#temperature-close').hide();
                $('#print-close').hide();
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
 * @param {string} action Reboot or shutdown requested.
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

/**
 * Monitor print job and close overlay.
 * 
 * @param {int} job_id ID of job to monitor
 */
function wait_print_job(job_id) {

    /* Request informations */
    $.ajax({
        url: '/print/monitoring/' + job_id,
        method: 'GET',
        success: function(response) {

            /* Print not completed */
            if (response.state === true) {

                /* Wait 500ms and retry */
                setTimeout(function() {
                    wait_print_job(response.job_id);
                }, 500);
            }

            /* Print completed, block the user for a few more seconds */
            else {
                setTimeout(function() {
                    $('#print-overlay').hide();
                }, 30000);
            }
        },
        error: function(error) {
            console.error('Error:', error);

            /* Avoid infinite loading if connection error */
            $('#print-overlay').hide();
        }
    });
}

/**
 * Send a picture to printer.
 */
function send_print() {

    /* Show printing overlay */
    $('#print-overlay').show();

    /* Get picture path */
    let path = $('#review #photo img').attr('src');

    /* Request print */
    $.ajax({
        url: '/print/start/' + path,
        method: 'GET',
        success: function(response) {
            console.log(response.job_id);
            wait_print_job(response.job_id);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}

/**
 * Refresh settings form values from given json.
 * 
 * @param {Object} settings Json formatted settings.
 */
function refreshSettingsForm(settings) {

    /* Convert python bool to js bool */
    enable_date = settings.enable_date.toLowerCase() === 'true';
    enable_time = settings.enable_time.toLowerCase() === 'true';

    /* Update form data */
    $('#setting-display-date').prop('checked', enable_date);
    $('#setting-display-time').prop('checked', enable_time);
    $('#setting-display-message').val(settings.message);
}

/**
 * Get settings from server.
 */
function getSettings() {

    /* Request settings values */
    $.ajax({
        url: '/settings',
        method: 'GET',
        success: function(response) {

            /* Update form data */
            refreshSettingsForm(response);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}

/**
 * Send updated settings to server.
 */
function sendSettings() {

    /* Get form data */
    let data = {
        enable_date: $('#setting-display-date').is(':checked'),
        enable_time: $('#setting-display-time').is(':checked'),
        message: $('#setting-display-message').val(),
    };

    /* Send form data */
    $.ajax({
        url: '/settings',
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {

            /* Update form data */
            refreshSettingsForm(response);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}
