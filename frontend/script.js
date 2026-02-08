// Helper to render song cards
function renderSongCards(songs, containerId, searchLogId = null) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'glass-card song-card';

        // Handle AI Recommendations vs DB results
        const isAI = song.ai_recommendation;
        const btnText = isAI ? 'Import to Undertone' : 'Save to Collection';
        const btnAction = isAI ? `importExternal('${song.artist.replace(/'/g, "\\'")}', '${song.title.replace(/'/g, "\\'")}')` : `saveToLibrary(${song.id}, ${searchLogId})`;
        const metaLine = isAI ? 'AI RECOMMENDATION' : `${song.genre} • ${song.bpm} BPM • ${song.decibel_peak} dB`;
        const tagHtml = isAI ? '<p style="font-size: 0.8rem; color: var(--text-muted);">This song matches your unique intent. Import it to see full metadata.</p>' : (song.tags ? song.tags.map(t => `<span class="tag">${t.tag_name}</span>`).join('') : '');

        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h4 class="song-title">${song.title}</h4>
                    <p class="song-artist">${song.artist}</p>
                </div>
                <span style="font-size: 0.7rem; color: var(--accent-primary); font-weight: bold; letter-spacing: 1px;">
                    ${isAI ? 'AI SUGGESTED' : (song.mainstream_score > 70 ? 'MAINSTREAM' : 'UNDERTONE')}
                </span>
            </div>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0.8rem 0;">${metaLine}</p>
            <div class="tag-container">
                ${tagHtml}
            </div>
            <button onclick="${btnAction}" class="action-btn" style="margin-top: 1.5rem; width: 100%;">${btnText}</button>
        `;
        container.appendChild(card);
    });
}

async function loadExploreSongs() {
    const resultsList = document.getElementById('results-list');
    const resultsTitle = document.getElementById('results-title');

    resultsTitle.innerText = "Library Exploration";
    resultsTitle.style.display = 'block';
    resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">Curating a selection of tracks...</div>';

    try {
        const response = await fetch('/songs/explore');
        const songs = await response.json();
        renderSongCards(songs, 'results-list');
    } catch (err) {
        console.error(err);
        resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">Unable to load library.</div>';
    }
}

// Mode selection logic
let currentMode = 'all';
document.querySelectorAll('.mode-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.mode-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentMode = chip.dataset.mode;
    });
});

document.getElementById('search-btn').addEventListener('click', async () => {
    const intent = document.getElementById('intent-input').value;

    const resultsList = document.getElementById('results-list');
    const resultsTitle = document.getElementById('results-title');

    if (!intent) return;

    resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">Parsing your musical intent...</div>';
    resultsTitle.innerText = "Analyzed Results";
    resultsTitle.style.display = 'block';

    try {
        const response = await fetch(`/search/intent?intent=${encodeURIComponent(intent)}&mode=${currentMode}`, {
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        const songs = data.songs;
        const searchLogId = data.search_log_id;

        if (songs.length === 0) {
            resultsList.innerHTML = `<div class="glass-card" style="grid-column: 1/-1; text-align: center;">No matches found for this intent in ${currentMode} mode. Try switching discovery modes or broadening your intent.</div>`;
            return;
        }

        renderSongCards(songs, 'results-list', searchLogId);
    } catch (err) {
        console.error(err);
        resultsList.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center; color: #ff4d4d;">Search failed. Analysis engine offline.</div>';
    }
});

async function saveToLibrary(songId, searchLogId = null) {
    try {
        const response = await fetch('/library/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ song_id: songId, search_log_id: searchLogId })
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
                card.className = 'glass-card song-card fade-in';
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

async function importExternal(artist, title) {
    await importTrack(artist, title);
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
loadExploreSongs();
