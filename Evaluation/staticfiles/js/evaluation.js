$(document).ready(function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap4',
        placeholder: 'Sélectionner une formation',
        width: '100%'
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Character count for comment
    const commentArea = $('textarea[name="commentaire"]');
    const charCountDisplay = $('#charCount');
    const minChars = 50;
    const maxLength = 500;

    function updateCharCount() {
        const charCount = commentArea.val().length;
        const remaining = minChars - charCount;
        
        charCountDisplay.text(charCount);

        if (charCount >= maxLength) {
            charCountDisplay.addClass('text-danger');
        } else {
            charCountDisplay.removeClass('text-danger');
        }

        if (remaining > 0) {
            charCountDisplay
                .html(`${remaining} caractères minimum requis`)
                .removeClass('text-success')
                .addClass('text-muted');
        } else {
            charCountDisplay
                .html('Nombre de caractères suffisant')
                .removeClass('text-muted')
                .addClass('text-success');
        }
    }

    commentArea.on('input', updateCharCount);
    updateCharCount(); // Initial count

    // Form validation
    $('#evaluationForm').on('submit', function(e) {
        const commentaire = commentArea.val();
        if (commentaire.length < minChars) {
            e.preventDefault();
            Swal.fire({
                icon: 'error',
                title: 'Commentaire trop court',
                text: `Le commentaire doit contenir au moins ${minChars} caractères.`
            });
            return false;
        }

        // Vérifier que tous les critères sont notés
        const criteresNonNotes = $('.evaluation-criteria select').filter(function() {
            return !$(this).val();
        });

        if (criteresNonNotes.length > 0) {
            e.preventDefault();
            Swal.fire({
                icon: 'error',
                title: 'Critères incomplets',
                text: 'Veuillez noter tous les critères.'
            });
            return false;
        }
    });
});