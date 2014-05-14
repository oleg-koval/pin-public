jQuery ->
	$("#tabs").tabs()
	
	
	# check that the url for link and image seems valid
	$('.urllink,.imagelink,.urlproduct_url').change (e) ->
		i = $(this).attr('i')
		remove_error_from_field($(this), i)
		value = $(this).val().toLowerCase()
		if value != '' and value.indexOf('http://') != 0 && value.indexOf('https://') != 0
			if value.indexOf('//') == 0
				$(this).val('http:' + value)
			else
				$(this).val('http://' + value)
		return
			
	
	$('.titleentry').on 'change', ->
		i = $(this).attr('i')
		if $(this).val() != ''
			remove_error_from_field($(this), i)
		return
		
		
	$('.prodprice').on 'change', ->
		i = $(this).attr('i')
		have_valid_price($(this), i)
		return
	
	
	$('#form').submit (e) ->
		try
			# to see if we can submit this form
			can_submit = true
			remove_all_errors()
			# test each mini-form separately
			for i in [1..10]
				no_error = validate_errors(i)
				if can_submit
					can_submit = no_error
			if not category_selected('categories', 'category_check', $('#category_error_message'))
				can_submit = false
			if not can_submit
				window.alert('Errors pending, please check')
			if can_submit
				$('#wait_for_process_to_finish_layer').height($(window).innerHeight())
				$('#wait_for_process_to_finish_layer div').css('margin-top', ($(window).innerHeight() / 2) - 150)
				$('#wait_for_process_to_finish_layer').show()
			return can_submit
		catch error
			alert(error)
			return false
	
	
	# validates the errors for one of the mini-forms
	validate_errors = (i) ->
		no_error = true
		title = $('#title' + i)
		description = $('#description' + i)
		link = $('#link' + i)
		product_url = $('#product_url' + i)
		imageurl = $('#imageurl' + i)
		tags = $('#tags' + i)
		price = $('#price' + i)
		# if all of the fields are blank, no more test is needed
		if all_fields_blank(title, description, link, imageurl, tags, price, product_url)
			return no_error
		# should have title
		if title.val() == ''
			no_error = false
			show_error_for_field(title, 'Empty title', i)
		else
			remove_error_from_field(title, i)
		# should have tags
		if tags.val() == ''
			no_error = false
			show_error_for_field(tags, 'Empty tags', i)
		else
			remove_error_from_field(tags, i)
		# should have a valid price
		if not have_valid_price(price, i)
			no_error = false
		# should have a valid link or valid product
		if not validate_link_and_product(link, product_url, i)
			no_error = false
		# should have a price range
		if not selected_a_price_range(i)
			no_error = false
		# should have a valid image
		if not validate_image(imageurl, i)
			no_error = false
		return no_error
	
	
	# all of the fields are blank
	all_fields_blank = (title, description, link, imageurl, tags, price, product_url) ->
		return title.val() == '' && description.val() == '' and link.val() == '' and
			imageurl.val() == '' && tags.val() == '' and
			price.val() == '' and product_url.val() == ''
			
	
	# shows an error for the field
	show_error_for_field = (field, text, i) ->
		field.addClass('field_error')
		field.after('<div class="error_text">' + text + '</div>')
		
	
	# removes errors from the field
	remove_error_from_field = (field, i) ->
		field.removeClass('field_error')
		field.nextAll('.error_text').remove()
	
	
	remove_all_errors = () ->
		$('div.error_text').remove()
		
	
	# validates that link field
	validate_link_and_product = (link, product_url, i) ->
		remove_error_from_field(link, i)
		remove_error_from_field(product_url, i)
		if link.val() == '' and product_url.val() == ''
			message = 'Provide source link or product link'
			show_error_for_field(link, message, i)
			show_error_for_field(product_url, message, i)
			return false
		else
			value = link.val().toLowerCase()
			if value != '' and value.indexOf('http://') != 0 && value.indexOf('https://') != 0
				if value.indexOf('//') == 0
					link.val('http:' + value)
				else
					link.val('http://' + value)
			value = product_url.val().toLowerCase()
			if value != '' and value.indexOf('http://') != 0 && value.indexOf('https://') != 0
				if value.indexOf('//') == 0
					product_url.val('http:' + value)
				else
					product_url.val('http://' + value)
		return true
			
	
	# test if a valid image is provided
	validate_image = (imageurl, i) ->
		if imageurl.val() == ''
			show_error_for_field(imageurl, 'Empty image', i)
			return false
		else
			remove_error_from_field(imageurl, i)
			value = imageurl.val().toLowerCase()
			if value.indexOf('http://') != 0 && value.indexOf('https://') != 0
				if value.indexOf('//') == 0
					$(this).val('http:' + value)
				else
					$(this).val('http://' + value)
		return true
		
	
	# test price has format with only digits and decimal point
	price_regex  = /^\d+(?:\.?\d{0,2})$/;
	have_valid_price = (price, i) ->
		remove_error_from_field(price, i)
		if price.val() is ''
			# the field is optional, no validation is not given
			return true
		if price.val().indexOf('$') == 0
			price.val(price.val().substring(1, price.val().length))
		if not price_regex.test(price.val())
			show_error_for_field(price, 'Not a valid price. Use format: 8888.88', i)
			return false
		else
			value = price.val()
			if value.indexOf('.') == -1
				price.val(value + '.00')
			else if value.indexOf('.') == value.length - 1
				price.val(value + '00')
			else if value.indexOf('.') == value.length - 2
				price.val(value + '0')
		return true
			
			
	# ensure a price range is selected
	selected_a_price_range = (i) ->
		remove_error_from_field($('#price_range' + i), i) 
		price_range = $('input[name=price_range' + i + ']:checked').val()
		if price_range is undefined
			show_error_for_field($('#price_range' + i), 'Select a price range')
			return false
		return true


	category_selected = (field_to_fill_name, check_fields_name, error_object) ->
		checked_categories = $('input[name="' + check_fields_name + '"]:checked')
		error_object.hide()
		if checked_categories.length > 0
			category_value = ''
			for c in checked_categories
				value = c.value
				if category_value isnt '' and category_value.lastIndexOf(',') isnt category_value.length - 1
					category_value = category_value + ','
				category_value = category_value + value
			$('input[name=' + field_to_fill_name + ']').val(category_value)
			return true
		else
			error_object.show()
			return false
			
	
	# creates the HTML to show one pin in the list
	get_pin_html_text = (pin) ->
		start = true
		pin['categories_list'] = ''
		for cat in pin['categories']
			if start
				start = false
			else
				pin['categories_list'] = pin['categories_list'] + '<br>'
			pin['categories_list'] = pin['categories_list'] + cat['name']
		pin['separate_product'] = separate_link_to_fit_small_space(pin['product_url'])
		pin['separate_link'] = separate_link_to_fit_small_space(pin['link'])
		base_html = $('#pin_template').html()
		html = _.template(base_html, pin)
		return html
		
	
	# delete one pin from the list
	$('body').on 'click', '.button_pin_delete', ->
		confirmation = window.confirm('Are you sure to delete this pin?')
		if confirmation
			pinid = $(this).attr('pinid')
			$.ajax type: 'DELETE'
				,url: '/admin/input/pins/' + pinid + '/'
			$('tr[pinid="' + pinid + '"]').remove()
		$.pagination_grid.g.unSelectAll()
		return
	
	
	# dialog div to edit the pin, only configuration here
	$('#pin_edit_dialog').dialog autoOpen: false
								,minWidth: 500
	
	
	# opens the dialog to edit a pin
	$('body').on 'click', '.button_pin_edit', (event) ->
		event.stopPropagation()
		pinid = $(this).attr('pinid')
		$.ajax type: 'GET'
			,url: '/admin/input/pins/' + pinid + '/'
			,dataType: 'json'
			,cache: false
			,success: (pin) ->
				open_edit_dialog_for(pin)
				return
			,error: (x, textStatus, errorThrown) ->
				$.loading_more_pins = false
				console.log("Error:" + textStatus + ', ' + errorThrown)
				return
		$.pagination_grid.g.unSelectAll()
		return
		
		
	# opens the dialog to edit the requested pin
	open_edit_dialog_for = (pin) ->
		$("#id11").val(pin['id'])
		$("#title11").val(pin['name'])
		$("#description11").val(pin['description'])
		$("#link11").val(pin['link'])
		$("#product_url11").val(pin['product_url'])
		$("#tags11").val($.put_hash_symbol(pin['tags']))
		$("#imgtag11").attr('src', pin['image_202_url'] + '?_=' + new Date().getTime())
		$("#imgfulllink11").attr('href', '/p/' + pin['external_id'])
		$("#category11").val('')
		$("#imageurl11").val('')
		if pin['price'] isnt 'None'
			$("#price11").val(pin['price'])
		else
			$("#price11").val('')
		$("#previmageurl11").attr('href', pin['image_url'])
		$('input[name=price_range11]').prop('checked', false)
		$('input[name=price_range11][value=' + pin['price_range'] + ']').prop('checked', true)
		$('input[name=category_check11]:checked').prop('checked', false)
		for cat in pin['categories']
			$('input[name=category_check11][value=' + cat['id'] + ']').prop('checked', true)
		remove_all_errors()
		$('#pin_edit_dialog').dialog('open')
		return
		
	
	# edits the pin. Edit in the background with AJAX.
	$('#pin_edit_form').submit ->
		no_error = true
		pinid = $('#id11')
		title = $('#title11')
		description = $('#description11')
		link = $('#link11')
		product_url = $('#product_url11')
		imageurl = $('#imageurl11')
		tags = $('#tags11')
		category = $('#categories11')
		price = $('#price11')
		price_range = $('input[name=price_range11]:checked')
		# should have title
		if title.val() == ''
			no_error = false
			show_error_for_field(title, 'Empty title', 11)
		else
			remove_error_from_field(title, 11)
		# should have description
		# should have tags
		if tags.val() == ''
			no_error = false
			show_error_for_field(tags, 'Empty tags', 11)
		else
			remove_error_from_field(tags, 11)
		# should have a valid price
		if not have_valid_price(price, 11)
			no_error = false
		# should have a valid source link or product link
		if not validate_link_and_product(link, product_url, 11)
			no_error = false
		# should select a price range
		if not selected_a_price_range(11)
			no_error = false
		if not category_selected('categories11', 'category_check11', $('#category_error_message11'))
			no_error = false
		if no_error
			update_pin_in_backgroud(pinid, title, description, link, product_url, imageurl, tags, category, price, price_range)
			$('#pin_edit_dialog').dialog('close')
		return false
		
		
	# updates the pin from the edit dialog using ajax, in the background
	# after changing the item, it is reloaded in the page
	update_pin_in_backgroud = (pinid, title, description, link, product_url, imageurl, tags, category, price, price_range) ->
		pin_data = 'title': title.val()
			,'description': description.val()
			,'link': link.val()
			,'product_url': product_url.val()
			,'imageurl': imageurl.val()
			,'tags': tags.val()
			,'categories': category.val()
			,'price': price.val()
			,'price_range': price_range.val()
		$.ajax type: 'POST'
			,url: '/admin/input/pins/' + pinid.val() + '/'
			,data: pin_data
			,dataType: 'json'
			,cache: false
			,success: (data) ->
				if data['status'] isnt 'ok'
					window.alert('Server error in your last update: ' + data['status'])
				else
					refresh_pin(pinid.val())
			,error: (x, err, ex) ->
				window.alert('Server error in your last update: ' + err + ' ' + ex)
		return
	
	
	# refresh the pin in the page after edition
	refresh_pin = (pin_id) ->
		$.ajax type: 'GET'
			,url: '/admin/input/pins/' + pin_id + '/'
			,dataType: 'json'
			,cache: false
			,success: (pin) ->
				box = $('tr[pinid="' + pin_id + '"]')
				text = get_pin_html_text(pin)
				box.html(text)
				return
			,error: (x, textStatus, errorThrown) ->
				console.log("Error:" + textStatus + ', ' + errorThrown)
				return
		return
	
	
	separate_link_to_fit_small_space = (url) ->
		sep = Array()
		last_val = 0
		for i in [0..url.length] by 16
			last_val = i
			slice = url.slice(i, i + 16)
			sep.push(slice)
		return sep.join(' ')


	$.put_hash_symbol = (tags) ->
		result = ''
		for tag in tags
			if result isnt ''
				result = result + ' '
			result = result + '#' + tag
		return result


	$.put_failed_pin_to_edit = (pin) ->
		if pin['imageurl'] isnt ''
			$('#imageurl' + pin['index']).val(pin['imageurl'])
		if pin['link'] isnt ''
			$('#link' + pin['index']).val(pin['link'])
		if pin['title'] isnt ''
			$('#title' + pin['index']).val(pin['title'])
		if pin['description'] isnt ''
			$('#description' + pin['index']).val(pin['description'])
		if pin['product_url'] isnt ''
			$('#product_url' + pin['index']).val(pin['product_url'])
		if pin['tags'] isnt ''
			$('#tags' + pin['index']).val(pin['tags'])
		if pin['price'] isnt ''
			$('#price' + pin['index']).val(pin['price'])
		if pin['price_range'] isnt ''
			$('input[name=price_range' + pin['index'] + '][value=' + pin['price_range'] + ']').attr('checked', 'checked')
		$('#imageurl' + pin['index']).before('<div class="error_text">' + pin['error'] + '</div>')
		return


	$('input[name=category_check]').change (event) ->
		parent_category = $(this).attr('parent-category')
		if parent_category isnt undefined
			if $(this).prop('checked')
				$('input[name=category_check][value=' + parent_category + ']').prop('checked', true)
		return
	
	
	
	
	
	# dialog to change the categories of many pins in bulk
	$('#change_categories_dialog').dialog autoOpen: false
								,minWidth: 500
								
	
	$('#change_categories_button').on 'click', (event) ->
		categories_not_selected = true
		for row in $.pagination_grid.g.getSelectedRows()
			categories_not_selected = false
			break
		if categories_not_selected
			return
		$('input[name=category_change_check]').prop('checked', false)
		$('#change_categories_dialog').dialog('open')
		return


	$('#change_pins_categories_form').on 'submit', (event) ->
		event.preventDefault()
		$('#category_change_error_message').hide()
		if not category_selected('categories_to_change', 'category_change_check', $('#category_change_error_message'))
			$('#category_change_error_message').show()
			return false
		ids = ''
		for row in $.pagination_grid.g.getSelectedRows()
			pinid = $(row).attr('pinid')
			if ids isnt ''
				ids = ids + ','
			ids = ids + pinid
		data = 
			'ids': ids,
			'categories': $('#categories_to_change').val()
		$.ajax
			type: 'POST',
			url: '/admin/input/change_pin_categories',
			data: data,
			dataType: 'json',
			success: ->
				for row in $.pagination_grid.g.getSelectedRows()
					pinid = $(row).attr('pinid')
					refresh_pin(pinid)
				return
		$('#change_categories_dialog').dialog('close')
		return false
	
	
	$('#select_all_pins_button').click ->
		$.pagination_grid.g.selectAll()
	
	
	$('#unselect_all_pins_button').click ->
		$.pagination_grid.g.unSelectAll()
	
	
	# to make the pin loaded items wider and moved
	# to the right
	previous_position = $('#tabs').offset()
	margin_to_subtract = previous_position.left
	$('#pins_container_layer').css('margin-left', (- margin_to_subtract) + 'px')
	$('#pins_container_layer').css('width', $(window).innerWidth() - 80)
	
	
	# change the page size for loaded item
	$('#page_size_form').on 'submit', (event) ->
		event.stopPropagation()
		event.preventDefault()
		$.get '/admin/input/change_page_size_for_loaded_items?size=' + $('#page_size_field').val(), ->
			$.pagination_grid.g.load()
		return
	
	
	# perform a search from the tagcloud
	$('#tagcloud span').on 'click', (event) ->
		event.stopPropagation()
		event.preventDefault()
		tag_to_search = $(this).attr('search')
		$.get '/admin/input/change_filter_by_tag_for_loaded_items?tag=' + tag_to_search, ->
			$.pagination_grid.g.load()
			index = $('#tabs a[href="#added"]').parent().index();
			$("#tabs").tabs("option", "active", index)
			return
		return
		
		
	$('#clear_tag_filter').on 'click', (event) ->
		event.stopPropagation()
		event.preventDefault()
		tag_to_search = $(this).attr('search')
		$.get '/admin/input/change_filter_by_tag_for_loaded_items?tag=', ->
			$.pagination_grid.g.load()
			index = $('#tabs a[href="#added"]').parent().index();
			$("#tabs").tabs("option", "active", index)
			return
		return

	
	return