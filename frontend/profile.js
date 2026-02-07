// Basic URL for the API
const API_BASE = "";

// Helper for fetch with credentials
async function apiFetch(endpoint, options = {}) {
    options.credentials = 'include';
    options.headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    return fetch(`${API_BASE}${endpoint}`, options);
}

// Auth UI handling
const loginForm = document.getElementById('login-form');
const userInfo = document.getElementById('user-info');
const displayUsername = document.getElementById('display-username');
const librarySection = document.getElementById('library-section');

function updateUI(user) {
    if (user) {
        loginForm.style.display = 'none';
        userInfo.style.display = 'block';
        displayUsername.textContent = user;
        librarySection.style.display = 'block';
        loadLibrary();
    } else {
        loginForm.style.display = 'block';
        userInfo.style.display = 'none';
        librarySection.style.display = 'none';
    }
}

// Event Listeners
window.addEventListener('load', checkSession);

async function checkSession() {
    try {
        const res = await apiFetch('/me');
        const data = await res.json();
        if (data.logged_in) {
            updateUI(data.username);
        } else {
            updateUI(null);
        }
    } catch (e) {
        console.error("Session check failed", e);
        updateUI(null);
    }
}

document.getElementById('register-btn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const res = await apiFetch('/register', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    alert(data.message || data.error);
});

document.getElementById('login-btn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const res = await apiFetch('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
        updateUI(data.username);
    } else {
        alert(data.error);
    }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
    await apiFetch('/logout');
    updateUI(null);
});

async function loadLibrary() {
    const res = await apiFetch('/library');
    const songs = await res.json();
    const libList = document.getElementById('library-list');

    if (songs.length === 0) {
        libList.innerHTML = "Your library is empty.";
        return;
    }

    libList.innerHTML = songs.map(song => `
        <div class="song-card">
            <strong>${song.artist} - ${song.title}</strong><br>
            <small>${song.genre} (${song.year})</small><br>
            BPM: ${song.bpm} | Peak: ${song.decibel_peak}dB
            <div style="margin-top: 5px;">
                ${song.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
            <div class="rating-box">
                Rate: 
                <select onchange="rateSong(${song.id}, this.value)">
                    <option value="5">5 Stars</option>
                    <option value="4">4 Stars</option>
                    <option value="3">3 Stars</option>
                    <option value="2">2 Stars</option>
                    <option value="1">1 Star</option>
                </select>
                <input type="text" placeholder="Comment" onblur="commentSong(${song.id}, this.value)">
            </div>
        </div>
    `).join('');
}

async function rateSong(songId, rating) {
    await apiFetch('/song/rate', {
        method: 'POST',
        body: JSON.stringify({ song_id: songId, rating: parseInt(rating) })
    });
}

async function commentSong(songId, comment) {
    if (!comment) return;
    await apiFetch('/song/rate', {
        method: 'POST',
        body: JSON.stringify({ song_id: songId, comment })
    });
}
