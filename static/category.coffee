jQuery ->
	get_more_items = (start) ->
		$.getJSON '', {ajax: 1, 'start': start}, (data) =>
			for pin in data
				html_text = $.pin_template(pin)
				$('#category_column_' + $.column_control).append(html_text)
				if $.column_control is 5
					$.column_control = 1
				else
					$.column_control += 1
			return
		return


	# detect when scrolling to bottom to load more items
	$(window).scroll ->
		top = $(window).scrollTop()
		height = $(window).innerHeight();
		doc_height = $(document).height()
		sensitivity = 600
		if top + height + sensitivity > doc_height
			get_more_items()
		return

	
	$.pin_template = _.template($('#pin_template').html())
	$.column_control = 1
	get_more_items(true)
	return