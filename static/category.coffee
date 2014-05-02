jQuery ->
	$.ajaxSetup({ cache: false })
	
	
	get_more_items = (start) ->
		if $.loading_more
			return
		$.loading_more = true
		$.getJSON '', {ajax: 1, 'start': start}, (data) =>
			for pin in data
				pin['simplifiedurl'] = simplify_url(pin['link'])
				if pin['tags'] isnt null
					pin['taglist'] = pin['tags']
				pin['image_loading'] = ''
				html_text = $.pin_template(pin)
				$('#category_column_' + $.column_control).append(html_text)
				if $.column_control is 5
					$.column_control = 1
				else
					$.column_control += 1
			$.loading_more = false
			window.setTimeout($('img.lazy').lazyload({
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


	$(document).on 'mouseenter', '.category_pin', (event) ->
		event.preventDefault()
		buttons = $(this).children('.category_pins_buttons')
		buttons.css($(this).offset())
		buttons.show()
		return


	$(document).on 'mouseleave', '.category_pin', (event) ->
		event.preventDefault()
		buttons = $(this).children('.category_pins_buttons')
		buttons.hide()
		return
		
		
	$(document).on 'click', '.category_pin_image', (event) ->
		event.preventDefault()
		pinid = $(this).attr('pinid')
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
				return
		return
	
	
	$('#show_pin_layer').on 'click', (event) ->
		event.preventDefault()
		$(this).hide()
		enable_scroll()
		return
		
		
	$('#show_pin_layer_content').on 'click', (event) ->
		event.stopPropagation()
		event.stopInmediatePropagation()
		return
		
		
	disable_scroll = () ->
		$(document).on('mousedown',disableMiddleMouseButtonScrolling)
		$(document).on('mousewheel DOMMouseScroll wheel',disableNormalScroll)
		$(window).on('scroll',disableNormalScroll)
		$.oldScrollTop = $(document).scrollTop()
	
	
	enable_scroll = () ->
		$(document).off('mousedown',disableMiddleMouseButtonScrolling)
		$(document).off('mousewheel DOMMouseScroll wheel',disableNormalScroll)
		$(window).off('scroll',disableNormalScroll)
		
	
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
		
	
	$.pin_template = _.template($('#pin_template').html())
	$.column_control = 1
	$.loading_more = false
	get_more_items(true)
	
	
	$('#repin-form').on 'submit', ->
		clear_repin_form_notifications()
		form_has_errors = false
		if $(this).find('#description').val() is ''
			form_has_errors = true
			show_error($(this).find('#description_error'), 'Please add a description')
		if $(this).find('#board_name').val() is '' and $(this).find('#board').val() is ''
			form_has_errors = true
			show_error($(this).find('#board_creation_layer'), 'Please select or add a list')
		if form_has_errors
			return false
		return true
	
	
	show_error = (element, message) ->
		element.after('<span class="red">' + message + '</span>')
	
	
	clear_repin_form_notifications = ->
		$('span.red').remove()
	
	
	return