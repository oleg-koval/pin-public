(->
  dragging = undefined
  otherX = undefined
  otherY = undefined
  upload = undefined
  x = undefined
  y = undefined
  $("#save_thumbnail_edit").click ->
    location.reload true
    return

  $("#set_as_profile_pic").click ->
    picid = $(".modal .active img").attr("picid")
    $.get "/setprofilepic/" + picid, (response) ->
      location.reload true
      return


  dragging = false
  x = 0
  y = 0
  otherX = 0
  otherY = 0
  $("#user_pic_placeholder").mousedown (e) ->
    _ref = undefined
    x = e.pageX
    y = e.pageY
    _ref = $(this).css("background-position").split(" ")
    otherX = _ref[0]
    otherY = _ref[1]

    dragging = true

  $("body").mouseup ->
    tempX = undefined
    tempY = undefined
    _ref = undefined
    if dragging
      dragging = false
      _ref = $("#user_pic_placeholder").css("background-position").split(" ")
      otherX = _ref[0]
      otherY = _ref[1]

      tempX = parseInt(otherX.slice(0, +(otherX.length - 2) + 1 or 9e9))
      tempY = parseInt(otherY.slice(0, +(otherY.length - 2) + 1 or 9e9))
      $.post "/changebgpos",
        x: tempX
        y: tempY


  $("#user_pic_placeholder").mousemove (e) ->
    tempY = undefined
    if dragging
      upload = false
      tempY = parseInt(otherY.slice(0, +(otherY.length - 2) + 1 or 9e9))
      $(this).css "background-position", otherX + " " + (tempY + (e.pageY - y)) + "px"  if tempY + (e.pageY - y) < 0

  $("#switch5_wrapper").mouseover ->
    $("#menu5").show()

  $("#switch5_wrapper").mouseout ->
    $("#menu5").hide()

  return
).call this