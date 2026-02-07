document.getElementById('search-btn').addEventListener('click', async () => {
    const genre = document.getElementById('genre').value;
    const tempo = document.getElementById('tempo').value;
    const loudness = document.getElementById('loudness').value;

    const resultsList = document.getElementById('results-list');
    resultsList.innerHTML = 'Searching...';

    const params = new URLSearchParams();
    if (genre) params.append('genre', genre);
    if (tempo !== 'any') params.append('tempo', tempo);
    if (loudness !== 'any') params.append('loudness', loudness);

    try {
        const response = await fetch(`/search/objective?${params.toString()}`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Search failed');

        const songs = await response.json();

        if (songs.length === 0) {
            resultsList.innerHTML = 'No songs found matching your criteria.';
            return;
        }

        resultsList.innerHTML = songs.map(song => `
            <div class="song-card">
                <strong>${song.artist || 'Unknown Artist'} - ${song.title || 'Untitled'}</strong><br>
                <small>Genre: ${song.genre} | Year: ${song.year} | ID: ${song.id}</small><br>
                BPM: ${song.bpm} | Peak: ${song.decibel_peak}dB | Mainstream: ${song.mainstream_score}
                <div style="margin-top: 5px;">
                    ${song.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <button class="save-btn" onclick="saveSong(${song.id})">Save to Library</button>
            </div>
        `).join('');

    } catch (error) {
        console.error(error);
        resultsList.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
    }
});

window.addEventListener('load', async () => {
    try {
        const res = await fetch('/me', { credentials: 'include' });
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('user-display').textContent = `Logged in as: ${data.username}`;
        }
    } catch (e) {
        console.error("Session check failed", e);
    }
});

async function saveSong(songId) {
    const res = await fetch(`/library/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ song_id: songId })
    });
    const data = await res.json();
    alert(data.message || data.error);
}
