jQuery ->
	$.loading_items = false
	$.current_page = 0
	$.current_column = 1
	$.pin_template = _.template($('#pin_template').html())
	$.no_data = true

	load_more_items = ->
		if $.loading_items
			return
		$.loading_items = true
		url = '/admin/remove_from_category/items?page=' + $.current_page
		$.getJSON url, (data) ->
			$.no_data = true
			for pin in data
				$.no_data = false
				if $.current_column > 4
					$.current_column = 1
				pin['simplifiedurl'] = simplify_url(pin['link'])
				if pin['tags'] isnt null
					pin['taglist'] = pin['tags']
				pin_html = $.pin_template(pin)
				$('#column' + $.current_column).append(pin_html)
				$.current_column += 1
			$.loading_items = false
			if $.no_data
				$('#no-items-found-layer').show()
			else
				$('#no-items-found-layer').hide()
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
	
	
	$(document).on 'click', 'div.category_pin', (event) ->
		pin = $(this)
		pin_id = $(this).attr('pin_id')
		url = '/admin/remove_from_category/' + pin_id
		$.ajax
			url: url,
			type: 'delete',
			success: ->
				pin.remove()
				return
		return
	
	
	$('a.category_change').on 'click', (event) ->
		event.preventDefault()
		event.stopPropagation()
		$.ajax
			url: '/admin/remove_from_category/set_category/' + $(this).attr('catid')
			success: ->
				$.current_page = 0
				$.current_column = 1
				$('#column1').find('*').remove()
				$('#column2').find('*').remove()
				$('#column3').find('*').remove()
				$('#column4').find('*').remove()
				load_more_items()
				return
		return
		
		
	# detect when scrolling to bottom to load more items
	$(window).scroll ->
		if $.no_data
			return
		top = $(window).scrollTop()
		height = $(window).innerHeight();
		doc_height = $(document).height()
		sensitivity = 10
		if top + height + sensitivity > doc_height
			$.current_page += 1
			load_more_items()
		return
	

	# position category change layer fixed at bottom
	$('div.category_selection_list').show()
	top = $(window).height() - $('div.category_selection_list').height();
	left = ($(window).width() - $('div.category_selection_list').width()) / 2;
	$('div.category_selection_list').offset({'top': top; 'left': left})
	
	return