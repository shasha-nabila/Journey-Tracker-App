document.addEventListener('DOMContentLoaded', function () {    
    // Function to fetch the list of friends from the server
    function fetchFriends(){
        const friendsList = document.getElementById('friends-list');
        friendsList.innerHTML = ''; // Initiate by clearing list

        fetch('/get_friends')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                // If there are friends, populate the list
                data.forEach(friend => {
                    // Add list item and button
                    const li = document.createElement('li');

                    const span = document.createElement('span');
                    span.className = 'username'
                    span.textContent = friend.username;
                    li.appendChild(span);
    
                    const button = document.createElement('button');
                    button.textContent = "Remove Friend";
                    button.className = 'isFriend'
                    button.id = friend.username
                    li.appendChild(button);
    
                    friendsList.appendChild(li);
                });
            } else {
                // If no friends found, display a message
                const p = document.createElement('p');
                p.textContent = 'No users found';
                friendsList.appendChild(p);
            }
        })
        .catch(error => {
            console.error('Error fetching friends:', error);
        });
    }
    
    // Function to fetch the list of suggested users from the server
    function fetchUsers(){
        const suggestedUserList = document.getElementById('suggestedUserList');
        suggestedUserList.innerHTML = ''; // Initiate by clearing list

        fetch('/get_suggested_users')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                // If there are suggested users, populate the list
                data.forEach(user => {
                    // Add list item and button
                    const li = document.createElement('li');

                    const span = document.createElement('span');
                    span.className = 'username'
                    span.textContent = user.username;
                    li.appendChild(span);
    
                    const button = document.createElement('button');
                    button.textContent = "Add Friend";
                    button.className = 'isUser'
                    button.id = user.username
                    li.appendChild(button);
    
                    suggestedUserList.appendChild(li);
                });
            } else {
                // If no suggested users found, display a message
                const p = document.createElement('p');
                p.textContent = 'No suggested users available';
                suggestedUserList.appendChild(p);
            }
        })
        .catch(error => {
            console.error('Error fetching suggested users:', error);
        });
    }

    fetchFriends()
    fetchUsers()
    
    // Function to fetch friends view when Friends button is clicked
    document.getElementById('friends-btn').addEventListener('click', function () {
        fetchFriends();
    });

    // Function to fetch suggested users view when Suggested Users button is clicked
    document.getElementById('suggested-users-btn').addEventListener('click', function () {
        fetchUsers();
    });
    
});

// Switch between active tabs
const tabs = document.querySelectorAll('.tab_btn');
const all_content = document.querySelectorAll('.content');

tabs.forEach((tab, index)=>{
    tab.addEventListener('click', (e)=>{
        tabs.forEach(tab=>{tab.classList.remove('active')});
        tab.classList.add('active');

        var line = document.querySelector('.line');
    line.style.width = e.target.offsetWidth + "px";
    line.style.left = e.target.offsetLeft + "px";

    all_content.forEach(content=>{content.classList.remove('active')})
    all_content[index].classList.add('active');
    })
});

// Attach the event listener to a parent element that is always present in the DOM
document.addEventListener('click', function(event) {
    // Check if the clicked element has the class .isFriend or .isUser
    if (event.target.classList.contains('isFriend') || event.target.classList.contains('isUser')) {
        const toggleButton = event.target;

        if (toggleButton.classList.contains('isFriend')) {
            toggleButton.innerText = 'Add Friend';
            toggleButton.classList.remove('isFriend');
            toggleButton.classList.add('isUser');
            // Remove the friend and toggle the button text and class
            removeFriend(toggleButton.id);
        } else if (toggleButton.classList.contains('isUser')) {
            toggleButton.innerText = 'Remove Friend';
            toggleButton.classList.remove('isUser');
            toggleButton.classList.add('isFriend');
            // Add user as new friend and toggle the button text and class
            addFriend(toggleButton.id);
        }
    }

    // Function to add friend
    function addFriend(username) {
        // Send AJAX request to add or remove friend based on action
        fetch(`/add_friendship/${username}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response
            console.log(data);
            if (data.error) {
                alert(data.error); // Display error message
            } else if (data.info) {
                alert(data.info); // Display info message
            } else if (data.success) {
                // Do not do anything, button will be toggled
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Function to remove friend
    function removeFriend(username) {
        // Send AJAX request to remove friend
        fetch(`/delete_friendship/${username}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response
            console.log(data);
            if (data.error) {
                alert(data.error); // Display error message
            } else if (data.info) {
                alert(data.info); // Display info message
            } else if (data.success) {
                // Do not do anything, button will be toggled
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }  
});