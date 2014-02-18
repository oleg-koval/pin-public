messages = [
  "Let's get you started! Under this box, we have Pins.",
  "You can add these items to your Getlist.",
  "Doing so is easy. Just click the thumbtack button in the top-left of any Pin.",
  "Try adding five items to your Getlist!"
]

counter = 0
$notice = $('.notice')
$firstTime = $('.first-time')

showNext = ->
  $notice.text(messages[counter])
  counter++
  if counter == messages.length
    $('#next').text('Finish')
    $('#skip').hide()
  else if counter > messages.length
    $firstTime.hide()

$('#skip').click ->
  $firstTime.hide()

$('#next').click ->
  showNext()
showNext()
