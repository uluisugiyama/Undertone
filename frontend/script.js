document.getElementById('search-btn').addEventListener('click', async () => {
    const genre = document.getElementById('genre').value;
    const tempo = document.getElementById('tempo').value;
    const loudness = document.getElementById('loudness').value;
    const popularity = document.getElementById('popularity').value;

    const resultsList = document.getElementById('results-list');
    const resultsTitle = document.getElementById('results-title');

    resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">Searching for your undertone...</div>';
    resultsTitle.style.display = 'block';

    const params = new URLSearchParams();
    if (genre) params.append('genre', genre);
    if (tempo !== 'any') params.append('tempo', tempo);
    if (loudness !== 'any') params.append('loudness', loudness);
    if (popularity !== 'all') params.append('popularity', popularity);

    try {
        const response = await fetch(`/search/objective?${params.toString()}`, {
            headers: { 'Content-Type': 'application/json' }
        });
        const songs = await response.json();

        resultsList.innerHTML = '';
        if (songs.length === 0) {
            resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">No matches found. Try widening your filters.</div>';
            return;
        }

        songs.forEach(song => {
            const card = document.createElement('div');
            card.className = 'glass-card song-card';

            const popularityTag = song.mainstream_score > 70 ? 'MAINSTREAM' : (song.mainstream_score < 40 ? 'NICHE' : 'BALANCED');

            card.innerHTML = `
                <div class="popularity-badge">${popularityTag}</div>
                <h4>${song.title}</h4>
                <p style="font-weight: 500; color: var(--text-main);">${song.artist}</p>
                <p style="margin-top: 0.5rem; font-size: 0.8rem;">${song.genre} • ${song.bpm} BPM • ${song.decibel_peak} dB</p>
                
                <div class="tags">
                    ${song.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                </div>
                
                <button class="save-btn" onclick="saveToLibrary(${song.id})" style="margin-top: 1.5rem; padding: 0.6rem; font-size: 0.9rem;">
                    Save to Collection
                </button>
            `;
            resultsList.appendChild(card);
        });
    } catch (err) {
        console.error(err);
        resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center; color: #ff4d4d;">Search failed. Please try again.</div>';
    }
});

async function saveToLibrary(songId) {
    try {
        const response = await fetch('/library/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ song_id: songId })
        });
        const data = await response.json();
        if (response.status === 401) {
            alert('Please login to save songs!');
            window.location.href = '/gui/profile';
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

// --- External Search Logic ---
const externalSearchBtn = document.getElementById('external-search-btn');
const externalSearchInput = document.getElementById('external-search-input');
const externalResults = document.getElementById('external-results');

if (externalSearchBtn) {
    externalSearchBtn.addEventListener('click', async () => {
        const query = externalSearchInput.value;
        if (!query) return;

        externalResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center;">Searching Last.fm...</div>';

        try {
            const response = await fetch(`/search/external?q=${encodeURIComponent(query)}`);
            const tracks = await response.json();

            externalResults.innerHTML = '';
            if (tracks.length === 0) {
                externalResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center;">No tracks found on Last.fm.</div>';
                return;
            }

            tracks.forEach(track => {
                const card = document.createElement('div');
                card.className = 'glass-card song-card';
                card.style.padding = '1rem';
                card.innerHTML = `
                    <h5 style="color: var(--accent-primary); margin-bottom: 0.2rem;">${track.title}</h5>
                    <p style="font-size: 0.8rem; margin-bottom: 0.8rem;">${track.artist}</p>
                    <button class="import-btn" onclick="importTrack('${track.artist.replace(/'/g, "\\'")}', '${track.title.replace(/'/g, "\\'")}')" 
                            style="padding: 0.5rem; font-size: 0.8rem; background: var(--bg-input); border: 1px solid var(--accent-primary); color: var(--accent-primary);">
                        Import to Undertone
                    </button>
                `;
                externalResults.appendChild(card);
            });
        } catch (err) {
            console.error(err);
            externalResults.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #ff4d4d;">External search failed.</div>';
        }
    });
}

async function importTrack(artist, title) {
    try {
        const response = await fetch('/song/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ artist, title })
        });
        const song = await response.json();
        if (response.status === 201 || response.status === 200) {
            alert(`"${song.title}" imported successfully!`);
            // Optionally trigger a local search to show it
        } else {
            alert('Import failed: ' + (song.error || 'Unknown error'));
        }
    } catch (err) {
        console.error(err);
        alert('Import failed.');
    }
}

// Check auth status on load
async function checkAuth() {
    const response = await fetch('/me');
    const data = await response.json();
    const userDisplay = document.getElementById('user-display');
    if (data.logged_in) {
        userDisplay.innerHTML = `Logged in as <a href="profile.html" style="color: var(--accent-primary); font-weight: 600;">${data.username}</a>`;
    } else {
        userDisplay.innerHTML = `<a href="profile.html">Login / Register</a>`;
    }
}

checkAuth();
