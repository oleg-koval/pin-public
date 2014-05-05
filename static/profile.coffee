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
        $(id).fadeOut()
      return



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



# ******** edit pin
$('.editPinModal').on 'submit', (event) ->
	form = $(this)
	if validate_edit_pin_form(form)
		return true
	return false
	
validate_edit_pin_form = (form) ->
	is_ok = true
	clear_all_error_messages(form)
	if form.find('#link').val() is '' and form.find('#product_url').val() is ''
		add_error_message(form.find('#link'), 'Provide a link')
		add_error_message(form.find('#product_url'), 'Provide a link')
		is_ok = false
	if form.find('#board_id').val() is '' and form.find('#board_name').val() is ''
		add_error_message(form.find('#layer_add_new_board'), 'Select a board or create a new one')
		is_ok = false
	if form.find('#title').val() is ''
		add_error_message(form.find('#title'), 'Provide a title')
		is_ok = false
	if form.find('input[name="price_range"]:checked').val() is undefined
		add_error_message(form.find('#price_range'), 'Select a price range')
		is_ok = false
	return is_ok


add_error_message = (item, message) ->
	item.after('<div class="red">' + message + '</div>');
	return
	

clear_all_error_messages = (form) ->
	form.find('div.red').remove()
	return


# ******** boards (lists) related code
$('#profile_lists_tabs').tabs()
$.offsetctrl = Array()
$.loading = Array()
$.column = Array()
$.pin_template = _.template($('#pin_template').html())
$.current_board = $('.profile_list_subtab:first').attr('boardid')

$('.profile_list_subtab').on 'click', (event) ->
	boardid = $(this).attr('boardid')
	loading = $.loading[boardid]
	if loading is true
		return
	$.current_board = boardid
	get_more_items()
	return
	

get_more_items = (show_images) ->
	boardid = $.current_board
	$.loading[boardid] = true
	offset = $.offsetctrl[boardid]
	if offset is undefined
		offset = 0
		$.offsetctrl[boardid] = 0
	else
		offset += 1
		$.offsetctrl[boardid] += 1
	$.getJSON '/lists/' + boardid + '/items/?offset=' + offset, (data) ->
		for pin in data
			column = $.column[boardid]
			if column is undefined
				column = 1
				$.column[boardid] = 1
			pin['simplifiedurl'] = simplify_url(pin['link'])
			if pin['tags'] isnt null
				pin['taglist'] = pin['tags']
			if show_images isnt null and show_images
				pin['image_loading'] = pin['image_212_url']
			else
				pin['image_loading'] = ''
			html_text = $.pin_template(pin)
			selector = '#column_' + boardid + '_' + column
			$(selector).append(html_text)
			if $.column[boardid] is 5
				$.column[boardid] = 1
			else
				$.column[boardid] += 1
		$.loading[boardid] = false
		setTimeout($('img.lazy').lazyload({
				failure_limit: 100}), 100)
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
	sensitivity = 1000
	if top + height + sensitivity > doc_height
		get_more_items()
	return
	
	
$(document).on 'click', '.category_pin_image', (event) ->
	event.preventDefault()
	pinid = $(this).attr('pinid')
	open_pin_detail(pinid)
	return


open_pin_detail = (pinid) ->
	$.get '/p/' + pinid + '?embed=true',
		(data) ->
			$('#show_pin_layer_content').html(data)
			current_position = $('#show_pin_layer_content').position()
			current_position.top = $(window).scrollTop()
			$('#show_pin_layer_content').css(current_position)
			$('#show_pin_layer').width($(window).width())
			$('#show_pin_layer').height($(window).height())
			$('#show_pin_layer').show()
			disable_scroll()
			try
				if window.history.state is null
					window.history.pushState(pinid, '', '/p/' + pinid);
				else
					window.history.replaceState(pinid, '', '/p/' + pinid);
			catch error
				print(error)
			return
	return

$('#show_pin_layer').on 'click', (event) ->
	if event.target.id is 'input-comment'
		$('#input-comment').focus()
		return
	event.preventDefault()
	$(this).hide()
	enable_scroll()
	try
		window.history.back();
	catch error
		$.noop()
	return
	
	
$('#show_pin_layer_content').on 'click', (event) ->
	event.stopPropagation()
	try
		event.stopInmediatePropagation()
	catch error
		$.noop()
	if event.target.id is 'input-comment'
		$('#input-comment').focus()
	return
	
	
window.onpopstate = (event)->
	path = document.location.pathname
	if path.substring(0, 3) is '/p/'
		pinid = path.substring(3, path.length)
		open_pin_detail(pinid)
	else
		$('#show_pin_layer').hide()
		enable_scroll()
	return
		
		
disable_scroll = () ->
	$(document).on('mousedown',disableMiddleMouseButtonScrolling)
	$(document).on('mousewheel DOMMouseScroll wheel',disableNormalScroll)
	$(window).on('scroll',disableNormalScroll)
	$.oldScrollTop = $(document).scrollTop()
	return


enable_scroll = () ->
	$(document).off('mousedown',disableMiddleMouseButtonScrolling)
	$(document).off('mousewheel DOMMouseScroll wheel',disableNormalScroll)
	$(window).off('scroll',disableNormalScroll)
	return
	

disableMiddleMouseButtonScrolling = (e) ->
	if e.which == 2
		if e.target.id isnt 'show_pin_layer'
			$('html, body').scrollTop($.oldScrollTop)
			return true
		e.preventDefault()
	return false


disableNormalScroll = (e) ->
	if e.target.id isnt 'show_pin_layer'
		$('html, body').scrollTop($.oldScrollTop)
		return true
	e.preventDefault()
	$('html, body').scrollTop($.oldScrollTop)
	return false


$('#list-box-wrapper-link').on 'click', ->
	get_more_items(true)
	setTimeout(scrollToShowImages(), 200)
	return
	

scrollToShowImages = ->
	$(window).scroll(10)
	$(window).scroll(0)
	return


jQuery ->
	$.ajaxSetup({ cache: false })
	return