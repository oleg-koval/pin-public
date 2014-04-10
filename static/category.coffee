jQuery ->
	get_more_items = (start) ->
		$.getJSON '', {ajax: 1, 'start': start}, (data) =>
			for pin in data
				pin['simplifiedurl'] = simplify_url(pin['link'])
				if pin['tags'] isnt null
					pin['taglist'] = pin['tags'].split(' ')
				html_text = $.pin_template(pin)
				$('#category_column_' + $.column_control).append(html_text)
				if $.column_control is 5
					$.column_control = 1
				else
					$.column_control += 1
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

	
	$.pin_template = _.template($('#pin_template').html())
	$.column_control = 1
	get_more_items(true)
	return