// Easter egg: /?replace=true swaps the hero video for a note about grid load.
function replaceVideoWithText() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('replace') !== 'true') return;

    const block2 = document.getElementById('block-2');
    if (!block2) return;

    const staticText = document.createElement('p');
    staticText.textContent =
        'Ruh-roh! Looks like there is high power consumption in my region today. ' +
        'Photos and videos have been temporarily disabled to reduce demand and conserve energy.';

    block2.innerHTML = '';
    block2.appendChild(staticText);
}

window.addEventListener('load', replaceVideoWithText);
