document.getElementById('login-btn')?.addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (response.ok) {
        checkAuth();
    } else {
        alert(data.error);
    }
});

document.getElementById('register-btn')?.addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (response.ok) {
        alert('Registered successfully! Now login.');
    } else {
        alert(data.error);
    }
});

document.getElementById('logout-btn')?.addEventListener('click', async () => {
    await fetch('/logout');
    window.location.reload();
});

async function checkAuth() {
    const response = await fetch('/me');
    const data = await response.json();
    if (data.logged_in) {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('user-info').style.display = 'block';
        document.getElementById('display-username').innerText = data.username;
        document.getElementById('library-section').style.display = 'block';
        loadLibrary();
        loadRecommendations();
    } else {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('user-info').style.display = 'none';
        document.getElementById('library-section').style.display = 'none';
    }
}

async function loadLibrary() {
    const response = await fetch('/library');
    const songs = await response.json();
    const list = document.getElementById('library-list');
    list.innerHTML = '';

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'glass-card song-card';
        card.innerHTML = `
            <h4>${song.title}</h4>
            <p style="color: var(--text-main);">${song.artist}</p>
            <div class="tags">
                ${song.tags.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
            <div class="rating-box">
                <label>Rate your undertone:</label>
                <div class="rating-stars" id="stars-${song.id}">
                    ${[1, 2, 3, 4, 5].map(i => `<span class="star" onclick="rateSong(${song.id}, ${i})">★</span>`).join('')}
                </div>
                <textarea id="comment-${song.id}" placeholder="How does this track resonate?"></textarea>
                <button onclick="saveRating(${song.id})" style="margin-top: 1rem; background: var(--bg-deep); border: 1px solid var(--glass-border); font-size: 0.8rem; padding: 0.5rem;">
                    Update Review
                </button>
            </div>
        `;
        list.appendChild(card);
    });
}

function rateSong(songId, rating) {
    const starContainer = document.getElementById(`stars-${songId}`);
    const stars = starContainer.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
    starContainer.dataset.value = rating;
}

async function saveRating(songId) {
    const rating = document.getElementById(`stars-${songId}`).dataset.value;
    const comment = document.getElementById(`comment-${songId}`).value;

    if (!rating) {
        alert('Please select a star rating first!');
        return;
    }

    const response = await fetch('/song/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_id: songId, rating: parseInt(rating), comment })
    });
    const data = await response.json();
    alert(data.message);
    loadRecommendations(); // Refresh recs when rating changes
}

async function loadRecommendations() {
    const response = await fetch('/recommendations');
    const songs = await response.json();
    const list = document.getElementById('recommendations-list');
    list.innerHTML = '';

    if (songs.length === 0) {
        list.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">Rate more songs to unlock personalized suggestions.</div>';
        return;
    }

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'glass-card song-card';
        card.innerHTML = `
            <div class="popularity-badge" style="color: var(--accent-primary)">MATCH: ${song.match_score}</div>
            <h4>${song.title}</h4>
            <p style="color: var(--text-main);">${song.artist}</p>
            <div class="tags">
                ${song.tags.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
            <button onclick="saveFromRec(${song.id})" style="margin-top: 1.5rem; padding: 0.6rem; font-size: 0.9rem; background: var(--bg-deep); border: 1px solid var(--accent-primary); color: var(--accent-primary);">
                Add to Library
            </button>
        `;
        list.appendChild(card);
    });
}

async function saveFromRec(songId) {
    const response = await fetch('/library/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_id: songId })
    });
    if (response.ok) {
        loadLibrary();
        loadRecommendations();
    }
}

checkAuth();
