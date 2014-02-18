ids = []
picked = 0

$('.loldongs').click ->
  if $(this).is(':disabled')
    return

  ids.push $(this).attr('data-id')
  picked++
  $(this).prop('disabled', true)
  
  if picked == 3
    $('#lol').val(ids.join(','))
    $('#wat').submit()
