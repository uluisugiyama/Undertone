let authMode = 'login';

function switchAuth(mode) {
    authMode = mode;
    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const btn = document.getElementById('auth-submit-btn');
    const tabs = document.querySelectorAll('.auth-tab');
    const errorMsg = document.getElementById('auth-error');

    errorMsg.style.display = 'none';

    tabs.forEach(tab => {
        if (tab.innerText.toLowerCase() === mode) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    if (mode === 'login') {
        title.innerText = 'Welcome Back';
        subtitle.innerText = 'Enter your credentials to continue.';
        btn.innerText = 'Login to Undertone';
    } else {
        title.innerText = 'Join Undertone';
        subtitle.innerText = 'Start your journey into deep discovery.';
        btn.innerText = 'Create Free Account';
    }
}

document.getElementById('auth-submit-btn')?.addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('auth-error');

    if (!username || !password) {
        errorMsg.innerText = 'Please enter both username and password.';
        errorMsg.style.display = 'block';
        return;
    }

    const endpoint = authMode === 'login' ? '/login' : '/register';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            if (authMode === 'register') {
                // Auto login after registration
                authMode = 'login';
                document.getElementById('auth-submit-btn').click();
            } else {
                checkAuth();
            }
        } else {
            errorMsg.innerText = data.error || 'Something went wrong.';
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.innerText = 'Server error. Please try again later.';
        errorMsg.style.display = 'block';
    }
});

document.getElementById('logout-btn')?.addEventListener('click', async () => {
    await fetch('/logout');
    window.location.reload();
});

async function checkAuth() {
    const response = await fetch('/me');
    const data = await response.json();

    const authSection = document.getElementById('auth-section');
    const userInfoSection = document.getElementById('user-info-section');
    const displayUsername = document.getElementById('display-username');

    if (data.logged_in) {
        authSection.style.display = 'none';
        userInfoSection.style.display = 'block';
        displayUsername.innerText = data.username;
        loadLibrary();
        loadRecommendations();
    } else {
        authSection.style.display = 'block';
        userInfoSection.style.display = 'none';
    }
}

async function loadLibrary() {
    const response = await fetch('/library');
    const songs = await response.json();
    const list = document.getElementById('library-list');
    list.innerHTML = '';

    if (songs.length === 0) {
        list.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">Your library is empty. Discover and save some tracks!</div>';
        return;
    }

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'song-card fade-in';
        card.innerHTML = `
        <h4>${song.title}</h4>
        <div class="artist">${song.artist}</div>
        <div class="meta">${song.genre} • ${song.bpm} BPM</div>
        
        <div class="tags">
            ${song.tags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>

        <div class="rating-box" style="margin-top: 1.5rem;">
            <div style="font-weight:800; font-size:0.7rem; text-transform:uppercase; margin-bottom:0.5rem;">Reader Rating</div>
            <div class="rating-stars" id="stars-${song.id}" data-value="${song.user_rating || 0}">
                ${[1, 2, 3, 4, 5].map(i => `
                    <span class="star ${(song.user_rating >= i) ? 'active' : ''}" 
                          onclick="rateSong(${song.id}, ${i})">★</span>
                `).join('')}
            </div>
            <textarea id="comment-${song.id}" placeholder="Editorial notes...">${song.user_comment || ''}</textarea>
            <button onclick="saveRating(${song.id})" style="margin-top: 1rem; font-size: 0.75rem; padding: 0.8rem;">
                UPDATE NOTES
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

    // Smooth refresh of recommendations
    loadRecommendations();
}

async function loadRecommendations() {
    const response = await fetch('/recommendations');
    const songs = await response.json();
    const list = document.getElementById('recommendations-list');

    if (songs.length === 0) {
        list.innerHTML = '<div class="editorial-card" style="grid-column: 1/-1; text-align: center;">Curate more resonance to unlock suggestions.</div>';
        return;
    }

    list.innerHTML = '';
    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'song-card fade-in';
        card.innerHTML = `
        <div style="font-size:0.65rem; font-weight:800; color:var(--accent-red); margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px;">AFFINITY: ${song.match_score}</div>
        <h4>${song.title}</h4>
        <div class="artist">${song.artist}</div>
        
        <div class="tags">
            ${song.tags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
        
        <button onclick="saveFromRec(${song.id})" style="margin-top: 1.5rem; padding: 0.8rem; font-size: 0.8rem;">
            SAVE TO ARCHIVE
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

// Global scope for onclick handlers
window.switchAuth = switchAuth;
window.rateSong = rateSong;
window.saveRating = saveRating;
window.saveFromRec = saveFromRec;

checkAuth();
