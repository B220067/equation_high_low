const hand = document.getElementById('hand');
const equationArea = document.getElementById('equation-area');
const liveOutput = document.getElementById('live-output');
const submitBtn = document.getElementById('submit-btn');
const bestResult = document.getElementById('best-result');
let dragged = null;

document.addEventListener('dragstart', function(e) {
    if (e.target.classList.contains('card')) {
        dragged = e.target;
    }
});
document.addEventListener('dragend', function() {
    dragged = null;
});
[hand, equationArea].forEach(zone => {
    zone.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        if (dragged && dragged.parentNode !== zone) {
            zone.appendChild(dragged);
            updateLiveOutput();
        }
    });
});
function getCardData() {
    return Array.from(equationArea.children).map(card => ({
        card_type: card.dataset.type,
        value: card.dataset.value,
        set_name: card.dataset.set
    }));
}
function updateLiveOutput() {
    fetch('/evaluate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({card_order: getCardData()})
    })
    .then(response => response.json())
    .then(data => {
        liveOutput.textContent = data.expr ? `Current: ${data.expr} = ${data.value}` : '';
    });
}

submitBtn.addEventListener('click', function() {
    fetch('/best', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({card_order: getCardData()})
    })
    .then(response => response.json())
    .then(data => {
        bestResult.innerHTML = '';
        Object.entries(data).forEach(([target, result]) => {
            if (result[0]) {
                bestResult.innerHTML += `Best for ${target}: ${result[0]} (diff: ${parseFloat(result[1]).toFixed(4)})<br>`;
            } else {
                bestResult.innerHTML += `No valid expression for target ${target}.<br>`;
            }
        });
    });
});