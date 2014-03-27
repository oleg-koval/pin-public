offset = 0
loading = false

$box = $('#pin-box')
$box.masonry({gutter: 20,transitionDuration: 0})
$button = $('#button-more')
$buffer = $('#pin-buf')


count = 0
$buffer.find('.pin').each ->
  count++


addItem = (box, item) ->
  box.append(item).masonry('appended', item).masonry('layout')

numPins = 0

$buffer.find('.pin').each ->
  $pin = $(this)
  i = 0
  
  imagesLoaded $pin,  ->
    $clone = $pin.clone()
    $pin.remove()
    $clone.find('.count').text(++numPins)
    addItem($box, $clone)
    if (++i) == count
      $box.masonry('layout')


appendPin = (jElem) ->
  $buffer.append(jElem)
  imagesLoaded jElem, ->
    clone = jElem.clone()
    jElem.remove()
    clone.find('.count').text(++numPins)
    addItem($box, clone)


getMorePosts = ->
  offset++
  loading = true
  $.getJSON '', {offset: offset, ajax: 1}, (data) ->
    loading = false
    count = 0

    if data.length > 0
      $button.prop('disabled', false)
      for pin in data
        appendPin $(pin)
    else
      $button[0].outerHTML = 'No more items to show!'


$button.click ->
  $button.prop('disabled', true)
  if not loading
    getMorePosts()

$button.prop('disabled', false)

setInterval (->
  $box.masonry('layout')
), 100
