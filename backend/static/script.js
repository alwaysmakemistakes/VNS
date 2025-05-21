
function shuffleImages() {
    const gallery = document.querySelector('.gallery');
    const images = Array.from(gallery.children);
    images.sort(() => Math.random() - 0.5);
    images.forEach(img => gallery.appendChild(img));
}
