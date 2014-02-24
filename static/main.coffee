(->
  $("#switch1").mouseover ->
    $("#menu1").show()

  $("#switch1").mouseout ->
    $("#menu1").hide()

  $("#switch2").mouseover ->
    $("#menu2").show()

  $("#switch2").mouseout ->
    $("#menu2").hide()

  $("#switch3").mouseover ->
    $("#menu3").show()

  $("#switch3").mouseout ->
    $("#menu3").hide()

  return
).call this
$(document).ready ->
  $("#remove_photo").click (e) ->
    
    #$(this).preventDefault();
    result = window.confirm("Are you sure you want to delete this Photo ?")
    unless result
      e.preventDefault()
      e.event.stopPropagation()
      return false
    e.event.stopPropagation()
    return

  $(".carousel").carousel interval: false
  return