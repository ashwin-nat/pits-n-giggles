// This file will contain the drag-and-drop logic for time trial comparison cards.

document.addEventListener('DOMContentLoaded', () => {
    const comparisonContainer = document.querySelector('.tt-comparison-container');
    if (!comparisonContainer) {
        console.warn('Time trial comparison container not found.');
        return;
    }

    let draggedItem = null;

    // Function to save the current order to local storage
    const saveCardOrder = () => {
        const cardOrder = Array.from(comparisonContainer.children).map(card => card.dataset.cardId); // Get the data-card-id which identifies the card type
        localStorage.setItem('timeTrialCardOrder', JSON.stringify(cardOrder));
    };

    // Function to load and apply the order from local storage
    const loadCardOrder = () => {
        const savedOrder = JSON.parse(localStorage.getItem('timeTrialCardOrder'));
        if (savedOrder) {
            const cards = {};
            Array.from(comparisonContainer.children).forEach(card => {
                cards[card.dataset.cardId] = card;
            });

            savedOrder.forEach(cardId => {
                if (cards[cardId]) {
                    comparisonContainer.appendChild(cards[cardId]);
                }
            });
        }
    };

    // Add event listeners for drag and drop
    comparisonContainer.addEventListener('dragstart', (e) => {
        draggedItem = e.target.closest('.tt-comparison-card');
        if (draggedItem) {
            setTimeout(() => {
                draggedItem.style.opacity = '0.5';
            }, 0);
            e.dataTransfer.effectAllowed = 'move';
        }
    });

    comparisonContainer.addEventListener('dragend', (e) => {
        if (draggedItem) {
            draggedItem.style.opacity = '1';
            draggedItem = null;
            saveCardOrder(); // Save order after drag ends
        }
    });

    comparisonContainer.addEventListener('dragover', (e) => {
        e.preventDefault(); // Allow drop
        const targetCard = e.target.closest('.tt-comparison-card');
        if (targetCard && draggedItem && draggedItem !== targetCard) {
            const boundingBox = targetCard.getBoundingClientRect();
            const offset = boundingBox.y + (boundingBox.height / 2);
            if (e.clientY - offset > 0) {
                comparisonContainer.insertBefore(draggedItem, targetCard.nextSibling);
            } else {
                comparisonContainer.insertBefore(draggedItem, targetCard);
            }
        }
    });

    comparisonContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        // The reordering is already handled in dragover, so just ensure opacity is reset
        if (draggedItem) {
            draggedItem.style.opacity = '1';
        }
    });

    // Make card headers draggable
    // Make card headers draggable
    Array.from(comparisonContainer.children).forEach(card => {
        const header = card.querySelector('.tt-card-header');
        if (header) {
            header.setAttribute('draggable', 'true');
        }
    });
    // Set draggable attribute on the cards themselves
    Array.from(comparisonContainer.children).forEach(card => {
        card.setAttribute('draggable', 'true');
    });

    // Load card order on initial page load
    loadCardOrder();
});