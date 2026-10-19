function approveDescription(id) {
    fetch('/approve-description', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Description approved:', data);
        location.reload();  // Reload the page to update the list of descriptions
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function rejectDescription(id) {
    // Similar to approveDescription, but call a different endpoint
}