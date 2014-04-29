jQuery ->
	$.loading_items = false
	$.current_page = 0
	$.current_column = 1
	$.pin_template = _.template($('#pin_template').html())

	load_more_items = ->
		if $.loading_items
			return
		$.loading_items = true
		url = '/admin/selection/pending_items?page=' + $.current_page
		$.getJSON url, (data) ->
			for pin in data
				if $.current_column > 3
					$.current_column = 1
				pin['simplifiedurl'] = simplify_url(pin['link'])
				if pin['tags'] isnt null
					pin['taglist'] = pin['tags'].split(' ')
				pin['image_loading'] = '/static/img/loading.png'
				pin_html = $.pin_template(pin)
				$('#column' + $.current_column).append(pin_html)
				$.current_column += 1
			$.loading_items = false
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
	
	
	$(document).on 'click', 'div.category_pin', (event) ->
		categories = Array()
		for checkbox in $('input.category_check:checked')
			categories.push(checkbox.value)
		if categories.length > 0
			categories_string = categories.join(',')
			console.log(categories_string)
			pin = $(this)
			pin_id = $(this).attr('pin_id')
			data = {pin_id: pin_id, categories: categories_string}
			url = '/admin/selection/add_to_categories'
			console.log(url)
			$.ajax
				dataType: 'json',
				data: data,
				url: url,
				type: 'POST',
				success: ->
					pin.remove()
		return

	
	load_more_items()
	return