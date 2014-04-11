removeRePin = (e, y) ->
  result = window.confirm("Are you sure you want to remove this picture ?")
  if result
    $.get "/remove-from-own-getlist",
      pinid: e
      repinid: y
    , (response) ->
      if response.error
        alert "An error occured, please refresh the page and try again later"
      else
        id = "#horz-pin" + e
        $(id).slideToggle()
      return

jQuery ->
  $("#save_thumbnail_edit").click ->
    location.reload true
    return

  $("#set_as_profile_pic").click ->
    picid = $(".modal .active img").attr("picid")
    $.get "/setprofilepic/" + picid, (response) ->
      location.reload true
      return


  dragging_header_background = false
  x = 0
  y = 0
  otherX = 0
  otherY = 0
  $("#header_background").mousedown (e) ->
    _ref = undefined
    x = e.pageX
    y = e.pageY
    _ref = $(this).css("background-position").split(" ")
    otherX = _ref[0]
    otherY = _ref[1]

    dragging_header_background = true

  $("body").mouseup ->
    tempX = undefined
    tempY = undefined
    _ref = undefined
    if dragging_header_background
      dragging_header_background = false
      _ref = $("#header_background").css("background-position").split(" ")
      otherX = _ref[0]
      otherY = _ref[1]

      tempX = parseInt(otherX.slice(0, +(otherX.length - 2) + 1 or 9e9))
      tempY = parseInt(otherY.slice(0, +(otherY.length - 2) + 1 or 9e9))
      $.post "/changebgpos",
        x: tempX
        y: tempY


  $("#header_background").mousemove (e) ->
    tempY = undefined
    if dragging_header_background
      upload = false
      tempY = parseInt(otherY.slice(0, +(otherY.length - 2) + 1 or 9e9))
      $(this).css "background-position", otherX + " " + (tempY + (e.pageY - y)) + "px"  if tempY + (e.pageY - y) < 0

  $("#switch5_wrapper").mouseover ->
    $("#menu5").show()

  $("#switch5_wrapper").mouseout ->
    $("#menu5").hide()


  $("#myTab a").click (e) ->
    e.preventDefault()
    $(this).tab "show"
    return


# ******** boards (lists) related code
	$('#profile_lists_tabs').tabs()
	$.offset = Array()
	$.loading = Array()
	$.column = Array()
	$.pin_template = _.template($('#pin_template').html())
	$.current_board = 0
	
	$('.profile_list_subtab').on 'click', (event) ->
		boardid = $(this).attr('boardid')
		loading = $.loading[boardid]
		if loading is true
			return
		$.current_board = boardid
		get_more_items()
		
	
	get_more_items = ->
		boardid = $.current_board
		$.loading[boardid] = true
		offset = $.offset[boardid]
		if offset is undefined
			offset = 0
			$.offset[boardid] = 0
		else
			offset += 1
			$.offset[boardid] += 1
		$.getJSON '/lists/' + boardid + '/items/?offset=' + offset, (data) ->
			for pin in data
				column = $.column[boardid]
				if column is undefined
					column = 1
					$.column[boardid] = 1
				pin['simplifiedurl'] = simplify_url(pin['link'])
				if pin['tags'] isnt null
					pin['taglist'] = pin['tags'].split(' ')
				html_text = $.pin_template(pin)
				selector = '#column_' + boardid + '_' + column
				$(selector).append(html_text)
				if $.column[boardid] is 5
					$.column[boardid] = 1
				else
					$.column[boardid] += 1
			$.loading[boardid] = false
			return
		return


	simplify_url = (url) ->
		simplified = url
		if simplified.indexOf('http:') is 0
		   simplified = simplified.substring(6, simplified.length - 1)
		if simplified.indexOf('https:') is 0
		   simplified = simplified.substring(7, simplified.length - 1)
		if simplified.indexOf('//') is 0
		   simplified = simplified.substring(2, simplified.length - 1)
		if simplified.indexOf('/') is 0
		   simplified = simplified.substring(1, simplified.length - 1)
		first_slash_position = simplified.indexOf('/')
		if first_slash_position > 0
			simplified = simplified.substring(0, first_slash_position)
		return simplified


	# detect when scrolling to bottom to load more items
	$(window).scroll ->
		top = $(window).scrollTop()
		height = $(window).innerHeight();
		doc_height = $(document).height()
		sensitivity = 600
		if top + height + sensitivity > doc_height
			get_more_items()
		return
		
		
	$(document).on 'click', '.category_pin_image', (event) ->
		event.preventDefault()
		pinid = $(this).attr('pinid')
		$.get '/item/' + pinid + '?embed=true',
			(data) ->
				$('#show_pin_layer_content').html(data)
				current_position = $('#show_pin_layer_content').position()
				current_position.top = $(window).scrollTop()
				$('#show_pin_layer_content').css(current_position)
				$('#show_pin_layer').width($(window).width())
				$('#show_pin_layer').height($(window).height())
				$('#show_pin_layer').show()
				return
		return
	
	
	$('#show_pin_layer').on 'click', (event) ->
		event.preventDefault()
		$(this).hide()
		return
		
		
	$('#show_pin_layer_content').on 'click', (event) ->
		event.stopPropagation()
		event.stopInmediatePropagation()
		return


	return