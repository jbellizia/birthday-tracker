function confirmLogout(event) {
    event.preventDefault();
    if (confirm('Are you sure you want to log out?')) {
        document.getElementById('logout-form').submit();
    }
}

function confirmDelete(event, form) {
    // Prevent the browser's default form submission so we can handle confirmation first
    event.preventDefault();
    if (confirm('Are you sure you want to delete this birthday?')) {
        form.submit();
    }
}
const searchInput = document.getElementById('search_field');
const rows = document.querySelectorAll('.birthday_row');

searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    rows.forEach(row => {
        // combine all text in the row (name, date, age, etc.)
        const rowText = row.textContent.toLowerCase();
        row.style.display = rowText.includes(query) ? '' : 'none';
    });
});