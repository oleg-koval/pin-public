$('.settings .nav span').click ->
    id = '#box-' + $(this).attr('data-id')
    $('#box').html($(id).html())
$('#box').html($('#box-profile').html())
