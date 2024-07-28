/*
 * Pi-Photobooth  Copyright (C) 2024  Corentin SORIANO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * This file contains DOM event listeners.
 */
$(document).ready(function() {

    /* Hide overlays */
    $('#countdown-overlay').hide();
    $('#print-overlay').hide();
    $('#review-overlay').hide();
    $('#settings-overlay').hide();
    $('#temperature-overlay').hide();

    /* Hide buttons by default */
    $('#settings-open').hide();
    $('#refresh').hide();
    $('#temperature-close').hide();
    $('#print-close').hide();

    /* Get translations */
    translations()
        .then(response => {
            lang = response;
        })
        .catch(error => {
            console.error('Error:', error);
        });

    /* Generate background-list */
    generateBackgroundList();

    /* Click on capture image button */
    $('#captureImage').on('click', function() {
        captureImage(lang);
    });
    
    /* Click on review overlay close */
    $('#review-close').on('click', function() {

        /* Reset text on review overlay */
        $('#review-message').text();

        /* Hide review overlay */
        $('#review-overlay').hide();
        $('#review #photo img').attr('src', '');
        $('#review #qrcode img').attr('src', '');

    });

    /* Print button */
    $('#print').on('click', send_print);

    /* Hide print overlay */
    $('#print-close').on('click', function() {
        $('#print-overlay').hide();
    });

    /* Click on settings open button */
    $('#settings-open').on('click', function() {
        /* Refresh form content and display overlay */
        getSettings();
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

    /* Refresh button */
    $('#refresh').on('click', function() {
        location.reload();
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

    /* Check system health */
    setInterval(checkSystemHealth, 5000);

    $('#settings input').on('change', sendSettings);

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
        let background = $(this).data('background');
        $('#preview-img').attr('src', '/video_feed/' + background);

    });
}
