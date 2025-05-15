var searchResult = []

function changeTab(name) {
    document.getElementById('tab-search').classList.toggle('d-none', name !== 'search');
    document.getElementById('tab-tracker').classList.toggle('d-none', name !== 'tracker');
}

async function searchGame(e) {
    e.preventDefault();
    const askingSection = document.getElementById('askingSection');
    if (askingSection) {
        askingSection.remove();
    }
    const searchKeyword = document.getElementById('search_keyword').value;
    const url = `/blog/search?search_keyword=${encodeURIComponent(searchKeyword)}`;
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        searchResult = data; // stores the search result in the global variable.

        const tableBody = document.querySelector('#game-table tbody');
        tableBody.innerHTML = '';
        createTable(data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    })
}

function createTable(data) {
    const tableBody = document.querySelector('#game-table tbody');
    tableBody.innerHTML = '';

    data.forEach(game => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
        <td></td>
        <td>${game.title}</td>
        <td>${game.platforms}</td>
        <td>${game.release_date}</td>
        <td>${game.genres}</td>
        <td>${game.developers}</td>
        <td><a href="https://wikidata.org/wiki/${game.wikidata_code}">LINK</a></td>
        `;
        
        const button = document.createElement('button');
        button.textContent = 'ADD'
        button.onclick = (e) => {
            const currentRow = e.target.closest('tr');
            button.disabled = true;
            
            const table = currentRow.parentElement;

            Array.from(table.children).forEach(row => {
                if (row !== currentRow) {
                    row.remove();
                }
            })
            setUserGameData(game)
        }
        row.children[0].appendChild(button)
        tableBody.appendChild(row);
    });

    preservedTable = tableBody;
}

function cleanAskingSection() {
    const askingSection = document.getElementById('askingSection');
    Array.from(askingSection.children)
    .filter(item => item.getAttribute('id') !== 'cancelButton')
    .filter(item => item.getAttribute('id') !== 'question')
    .forEach(item => {
        item.remove();
    });
};

async function setUserGameData(game) {
    const main = document.querySelector('main');
    const askingSection = document.createElement('div')
    askingSection.setAttribute('id', 'askingSection')

    const cancelButton = document.createElement('button');
    cancelButton.setAttribute('id', 'cancelButton')
    cancelButton.textContent = 'Go back to the list';
    cancelButton.onclick = () => {
        document.getElementById('askingSection').remove();
        createTable(searchResult);
    };
    const question = document.createElement('h1');
    question.setAttribute('id', 'question');

    askingSection.appendChild(cancelButton);
    askingSection.appendChild(question);
    main.appendChild(askingSection);

    game['purchased'] = await setPurchased();
    if (game['purchased']) {
        game['purchase_date'] = await setPurchaseDate();
    }
    game['playing_platform'] = await setPlayingPlatform();
    game['expectation_level'] = await setExpectionLevel();


    fetch('/blog/add_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(game)
    })
    .then(response => response.json())
    .then(() => {
        console.log('done');
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    })
}

async function setPurchased() {
    // Fill up the HTML page
    const purchasedDiv = document.createElement('div');
    purchasedDiv.setAttribute('id', 'purchasedDiv')
    const question = document.getElementById('question');
    question.textContent = 'Did you purchase this game?'
    const yesButton = document.createElement('button');
    const noButton = document.createElement('button');
    yesButton.textContent = 'YES';
    noButton.textContent = 'NO';
    
    purchasedDiv.appendChild(yesButton);
    purchasedDiv.appendChild(noButton);

    const askingSection = document.getElementById('askingSection');
    askingSection.appendChild(purchasedDiv);
    
    // Pause until the user clicks a button
    return new Promise((resolve) => {
        yesButton.onclick = () => resolve(true)
        noButton.onclick = () => resolve(false)
    })
};

async function setPurchaseDate() {
    cleanAskingSection();

    var purchaseDate = prompt('Please put the purchase date in yyyy-mm-dd');
    while (!purchaseDate.match(new RegExp('\\d{4}-\\d{2}-\\d{2}'))) {
        purchaseDate = prompt('Please put the purchase date in yyyy-mm-dd');
    }
    return purchaseDate;
};

async function setPlayingPlatform() {
    cleanAskingSection();

    // Fill up the HTML page
    const platformDiv = document.createElement('div');
    platformDiv.setAttribute('id', 'platformDiv');
    const question = document.getElementById('question');
    question.textContent = 'On which platform do you play this game?';
    const ps5Button = document.createElement('button');
    const ps5ProButton = document.createElement('button');
    ps5Button.textContent = 'PS5';
    ps5ProButton.textContent = 'PS5Pro';

    platformDiv.appendChild(ps5Button);
    platformDiv.appendChild(ps5ProButton);

    const askingSection = document.getElementById('askingSection');
    askingSection.appendChild(platformDiv)

    return new Promise((resolve) => {
        ps5Button.onclick = () => resolve('PS5');
        ps5ProButton.onclick = () => resolve('PS5Pro');
    })
};

async function setExpectionLevel() {
    cleanAskingSection();

    // Fill up the HTML page
    const expectionDiv = document.createElement('div');
    expectionDiv.setAttribute('id', 'expectionDiv');
    const question = document.getElementById('question');
    question.textContent = 'How much are you hype on this game?';
    const noticedButton = document.createElement('button');
    const interestedButton = document.createElement('button');
    const lookingForwardButton = document.createElement('button');
    const hypedButton = document.createElement('button');
    const mustPlayButton = document.createElement('button');
    noticedButton.textContent = 'Noticed';
    interestedButton.textContent = 'Interested';
    lookingForwardButton.textContent = 'Looking Forward';
    hypedButton.textContent = 'Hyped';
    mustPlayButton.textContent = 'Must Play';

    expectionDiv.appendChild(noticedButton);
    expectionDiv.appendChild(interestedButton);
    expectionDiv.appendChild(lookingForwardButton);
    expectionDiv.appendChild(hypedButton);
    expectionDiv.appendChild(mustPlayButton);

    const askingSection = document.getElementById('askingSection');
    askingSection.appendChild(expectionDiv)

    return new Promise((resolve) => {
        noticedButton.onclick = () => resolve(0);
        interestedButton.onclick = () => resolve(1);
        lookingForwardButton.onclick = () => resolve(2);
        hypedButton.onclick = () => resolve(3);
        mustPlayButton.onclick = () => resolve(4);
    })
}; 