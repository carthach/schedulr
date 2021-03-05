var body = document.getElementsByTagName("body")[0];
var user_dropdown = document.getElementById('user-dropdown-menu');
var sort_dropdown = document.getElementById('sort-dropdown-menu');
var notification_dropdown = document.getElementById('notification-dropdown-menu');

if (user_dropdown !== null) {
    body.addEventListener("click", function () {
        // Hide the user dropdown when you click outside of it
        user_dropdown.classList.remove('opacity-100');
        user_dropdown.classList.remove('scale-100');
        user_dropdown.classList.add('opacity-0');
        user_dropdown.classList.add('scale-95');
        user_dropdown.style.display = 'none';
    }, false);
    document.getElementById('user-menu').addEventListener("click", function (ev) {
        ev.stopPropagation(); //this is important! If removed, you'll get both alerts
    }, false);
}

if (sort_dropdown !== null) {
    body.addEventListener("click", function () {
        // Hide the sort dropdown when you click outside of it
        sort_dropdown.classList.remove('opacity-100');
        sort_dropdown.classList.remove('scale-100');
        sort_dropdown.classList.add('opacity-0');
        sort_dropdown.classList.add('scale-95');
        sort_dropdown.style.display = 'none';
    }, false);
    document.getElementById('sort-dropdown-button').addEventListener("click", function (ev) {
        ev.stopPropagation(); //this is important! If removed, you'll get both alerts
    }, false);
}

if (notification_dropdown !== null) {
    body.addEventListener("click", function () {
        // Hide the user dropdown when you click outside of it
        notification_dropdown.classList.remove('opacity-100');
        notification_dropdown.classList.remove('scale-100');
        notification_dropdown.classList.add('opacity-0');
        notification_dropdown.classList.add('scale-95');
        notification_dropdown.style.display = 'none';
    }, false);
    document.getElementById('notification-menu').addEventListener("click", function (ev) {
        ev.stopPropagation(); //this is important! If removed, you'll get both alerts
    }, false);
}