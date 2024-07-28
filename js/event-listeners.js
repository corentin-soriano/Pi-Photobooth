/**
 * This file contains DOM event listeners.
 */
$(document).ready(function() {

    /* Hide overlays */
    $('#countdown-overlay').hide();
    $('#review-overlay').hide();
    $('#settings-overlay').hide();
    $('#temperature-overlay').hide();

    /* Hide buttons by default */
    $('#settings-open').hide();
    $('#temperature-close').hide();

    /* Generate background-list */
    generateBackgroundList();

    /* Click on capture image button */
    $('#captureImage').on('click', captureImage);
    
    /* Click on review overlay close */
    $('#review-close').on('click', function() {

        /* Reset text on review overlay */
        $('#review-message').text();

        /* Hide review overlay */
        $('#review-overlay').hide();
        $('#review #photo img').attr('src', '');
        $('#review #qrcode img').attr('src', '');

    });

    /* Click on settings open button */
    $('#settings-open').on('click', function() {
        $('#settings-overlay').show();
    });

    /* Click on settings close button */
    $('#settings-close').on('click', function() {
        $('#settings-overlay').hide();
    });

    /* Hide overlay */
    $('#temperature-close').on('click', function() {
        $('#temperature-overlay').hide();
    });

    /* Power buttons */
    $('#shutdown').on('click', function() {
        power('shutdown');
    });
    $('#reboot').on('click', function() {
        power('reboot');
    });

    /* Check if admin button is enabled */
    setInterval(checkGPIOAdmin, 5000);

    /* Check CPU temperature */
    setInterval(checkCPUTemp, 5000);

});

/**
 * Function to add event listener on .background-item after list loading.
 */
function bgItemEventListenerAdd() {
    /* Click on background item */
    $('.background-item').on('click', function() {

        /* Reset selected item */
        $('.background-item').removeClass('selected');

        /* Add selected class on this item */
        $(this).addClass('selected');

        /* Change video feed */
        background = $(this).data('background');
        $('#preview-img').attr('src', '/video_feed/' + background);

    });
}
