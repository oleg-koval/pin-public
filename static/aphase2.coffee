$('.pick-people .user').click ->
    $(this).toggleClass('selected')

$('#herp').submit ->
    ids = []
    $('.pick-people .user').each ->
        if $(this).hasClass('selected')
            ids.push($(this).attr('data-id'))

    $('#derp').val(ids.join(','))
