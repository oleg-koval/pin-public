$('#file').change ->
  $('#form').submit()

upload = true

$('.user-heading').click ->
  if $(this).attr('id') == 'lolbg'
    if upload
      $('#form').attr('action', '/changebg')
      $('#file').click()
    else
      upload = true

$('.user-heading .back').click (e) ->
  e.stopPropagation()

$('#lolimage').click ->
  $('#form').attr('action', '/changeprofile')
  $('#file').click()

dragging = false
x = 0
y = 0
otherX = 0
otherY = 0

$('#lolbg').mousedown (e) ->
  if $(this).attr('data-nobg') != 'true'
    x = e.pageX
    y = e.pageY
    [otherX, otherY] = $(this).css('background-position').split(' ')
    dragging = true

$('body').mouseup ->
  if dragging
    dragging = false
    [otherX, otherY] = $('#lolbg').css('background-position').split(' ')
    tempX = parseInt(otherX[0..otherX.length - 2])
    tempY = parseInt(otherY[0..otherY.length - 2])
    $.post('/changebgpos', {x: tempX, y: tempY})

$('#lolbg').mousemove (e) ->
  if dragging
    upload = false
    tempY = parseInt(otherY[0..otherY.length - 2])
    if tempY + (e.pageY - y) < 0
      $(this).css('background-position', otherX + ' ' + (tempY + (e.pageY - y)) + 'px')
