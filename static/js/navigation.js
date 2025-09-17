// Handle browser navigation
window.addEventListener('popstate', function(event) {
    // Prevent exiting the site, return to main page
    if (document.referrer.includes(window.location.host)) {
        window.location.href = '/';
    } else {
        history.pushState(null, '', '/');
        window.location.reload();
    }
});

// Ensure forward/back gestures don't exit
window.addEventListener('load', function() {
    history.pushState(null, '', window.location.href);
});