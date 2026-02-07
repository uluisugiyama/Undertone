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
        const response = await fetch(`http://127.0.0.1:5001/search/objective?${params.toString()}`);
        if (!response.ok) throw new Error('Search failed');
        
        const songs = await response.json();
        
        if (songs.length === 0) {
            resultsList.innerHTML = 'No songs found matching your criteria.';
            return;
        }

        resultsList.innerHTML = songs.map(song => `
            <div class="song-card">
                <strong>ID: ${song.id}</strong> | Genre: ${song.genre} | Year: ${song.year}<br>
                BPM: ${song.bpm} | Peak: ${song.decibel_peak}dB | Mainstream: ${song.mainstream_score}
            </div>
        `).join('');

    } catch (error) {
        console.error(error);
        resultsList.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
    }
});
