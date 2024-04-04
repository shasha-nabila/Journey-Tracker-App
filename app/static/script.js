// script.js
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const friendList = document.getElementById('friendList');
    const suggestedUserList = document.getElementById('suggestedUserList');

    searchInput.addEventListener('input', function() {
        const searchTerm = searchInput.value.trim();
        if (searchTerm.length > 0) {
            // Send AJAX request to search for users
            fetch(`/search?query=${searchTerm}`)
            .then(response => response.json())
            .then(data => {
                // Clear previous results
                friendList.innerHTML = '';
                suggestedUserList.innerHTML = '';
                if (data.users.length > 0) {
                    data.users.forEach(user => {
                        // Display users in search results
                        const li = document.createElement('li');
                        li.textContent = user.username;
                        const addButton = document.createElement('button');
                        addButton.textContent = 'Add';
                        addButton.addEventListener('click', function() {
                            // Send friend request
                            sendFriendRequest(user.id);
                        });
                        li.appendChild(addButton);
                        friendList.appendChild(li);
                    });
                } else {
                    friendList.innerHTML = '<li>No user found</li>';
                }
            });
        } else {
            friendList.innerHTML = '';
            suggestedUserList.innerHTML = '';
        }
    });

    function sendFriendRequest(userId) {
        // Send AJAX request to send friend request
        fetch('/send_friend_request', {
            method: 'POST',
            body: new URLSearchParams({ 'userId': userId }),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Friend request sent successfully!');
            } else {
                alert('Failed to send friend request.');
            }
        });
    }
});
