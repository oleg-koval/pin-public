offset = 0

$pins = $('#pins')

$('#more').click ->
  $(this).prop('disabled', true)
  offset++

  $.getJSON '', {offset: offset, ajax: 1}, (data) =>
    if data.length > 0
      $(this).prop('disabled', false)
      for pin in data
        $pins.append(pin)
    else
      $(this)[0].outerHTML = 'No more items could be found.'
