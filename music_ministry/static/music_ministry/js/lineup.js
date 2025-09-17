document.addEventListener('DOMContentLoaded', function () {
    const setListSelect = document.getElementById('setListType');
    if (setListSelect) {
        setListSelect.addEventListener('change', updateSongFields);
        updateSongFields();
    }

    let customSongCount = 1;
    const addCustomSongBtn = document.getElementById('addCustomSong');
    if (addCustomSongBtn) {
        addCustomSongBtn.addEventListener('click', addCustomSong);
    }
});

function updateSongFields() {
    const setListType = document.getElementById('setListType').value;
    const songSets = document.querySelectorAll('.song-set');

    songSets.forEach(set => {
        set.style.display = 'none';
        const inputs = set.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.removeAttribute('required');
        });
    });

    if (setListType) {
        const targetSet = document.getElementById(setListType);
        if (targetSet) {
            targetSet.style.display = 'block';
            const inputs = targetSet.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                if (input.name.includes('_title')) {
                    input.setAttribute('required', 'required');
                }
            });
        }
    }
}

function addCustomSong() {
    const customSongs = document.getElementById('customSongs');
    if (!customSongs) return;

    const songCount = customSongs.children.length + 1;
    const newSongItem = document.createElement('div');
    newSongItem.className = 'custom-song-item';
    newSongItem.innerHTML = `
        <div class="form-group">
            <label class="form-label">Song Type</label>
            <select name="custom_song_type_${songCount}" class="form-input form-select">
                <option value="praise">Praise</option>
                <option value="high_praise">High Praise</option>
                <option value="worship">Worship</option>
                <option value="high_worship">High Worship</option>
                <option value="fellowship">Fellowship</option>
            </select>
        </div>
        <div class="form-group">
            <label class="form-label">Song Title</label>
            <input type="text" name="custom_song_title_${songCount}" class="form-input" placeholder="Song title" required>
        </div>
        <div class="form-group">
            <label class="form-label">Song Link</label>
            <input type="url" name="custom_song_link_${songCount}" class="form-input" placeholder="Song link (optional)">
        </div>
    `;
    customSongs.appendChild(newSongItem);
}
