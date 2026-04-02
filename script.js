const tg = window.Telegram.WebApp;
tg.expand(); // Разворачиваем на все окно

// Пример данных (потом можно будет подгружать из твоей БД)
const movies = [
    { id: 1, title: "The Visitor", img: "https://via.placeholder.com/150/8b0000/ffffff?text=Horror" },
    { id: 2, title: "Mendix Origins", img: "https://via.placeholder.com/150/444444/ffffff?text=Code" },
    { id: 3, title: "Midnight Walk", img: "https://via.placeholder.com/150/000000/ffffff?text=Scary" }
];

const grid = document.getElementById('movieGrid');

function renderMovies(list) {
    grid.innerHTML = '';
    list.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <img src="${movie.img}">
            <div class="movie-info">
                <h3>${movie.title}</h3>
            </div>
        `;
        // При клике отправляем ID фильма боту и закрываем окно
        card.onclick = () => {
            tg.sendData(`movie_id:${movie.id}`); 
            tg.close();
        };
        grid.appendChild(card);
    });
}

renderMovies(movies);