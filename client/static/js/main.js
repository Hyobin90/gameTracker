selected_game = {}
searchResult = {}

function changeTab(name) {
    document.getElementById('tab-search').classList.toggle('d-none', name !== 'search');
    document.getElementById('tab-tracker').classList.toggle('d-none', name !== 'tracker');
}

async function searchGame(e) {
    e.preventDefault();
    const searchKeyword = document.getElementById('search_keyword').value;
    const url = `/blog/search?search_keyword=${encodeURIComponent(searchKeyword)}`;
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        //searchResult = data; // stores the search result in the global variable.

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
        searchResult = tableBody
        });
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    })
}
// the transition screen should be called 
// /blog/add_game route should be called in the transition screen
// the transition screen has multiple layers -> multiple functions
// store the data selected by the user in the memory
// Send the data to a route
// create a route in the backend

async function setUserGameData(game) {
    const main = document.querySelector('main');
    const askingSection = document.createElement('div')
    askingSection.setAttribute('id', 'askingSection')

    const cancelButton = document.createElement('button');
    cancelButton.textContent = 'Go back to the list';

    askingSection.appendChild(cancelButton)
    main.appendChild(askingSection)

    game['purchased'] = await setPurchased()
    if (game['purchased']) {
        game['purchase_date'] = await setPurchaseDate()
    };
    // game['playing_platform'] = await setPlayingPlatform()
    // game['expectation_level'] = await setExpectionLevel()

    // const url = `/blog/add_game/?game=${game}`;
    // fetch(url)

    // const tableBody = document.querySelector('#game-table tbody');
    // tableBody.append(searchResult)
    console.log(game)
}

async function setPurchased() {
    const askingSection = document.getElementById('askingSection');

    const message = document.createElement('h1');
    message.textContent = 'Did you purchase this game?'

    const yesButton = document.createElement('button');
    const noButton = document.createElement('button');
    yesButton.textContent = 'YES';
    noButton.textContent = 'NO';
    
    askingSection.appendChild(message)
    askingSection.appendChild(yesButton)
    askingSection.appendChild(noButton)
    
    return new Promise((resolve) => {
        yesButton.onclick = () => resolve(true)
        noButton.onclick = () => resolve(false)
    })
}

async function setPurchaseDate() {
    const askingSection = document.getElementById('askingSection');

    const message = document.createElement('h1');
    message.textContent = 'When did you purchase this game?';
    askingSection.appendChild(message)

    const purchaseDate = prompt('Please put the purchase date in yyyy-mm-dd')

    return Promise.resolve(purchaseDate)
}

async function setPlayingPlatform() {
    
}

async function setExpectionLevel() {

}




