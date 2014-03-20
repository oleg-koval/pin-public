jQuery ->
	$("#tabs").tabs()
	
	
	# check that the url for link and image seems valid
	$('.urllink,.imagelink').change (e) ->
		i = $(this).attr('i')
		remove_error_from_field($(this), i)
		value = $(this).val().toLowerCase()
		if value.indexOf('http://') != 0 && value.indexOf('https://') != 0
			show_error_for_field($(this), 'Link lacks http:// or https://, seems invalid', i)
		return
			
	
	# check that the name of the file to upload seems valid
	$('.imagefile').on 'change', (e) ->
		i = $(this).attr('i')
		remove_error_from_field($(this), i)
		value = $(this).val().toLowerCase()
		if value.indexOf('.png') == -1 && value.indexOf('.jpg') == -1 && value.indexOf('.jpeg') == -1 && value.indexOf('.gif') == -1 &&
			 	value.indexOf('.svg') == -1
			show_error_for_field($(this), 'Image doesn\'t seem to be in a internet friendly format: .png, ,jpg, .gif, .svn', i)
		return
			
			
	$('.titleentry,.descrentry').on 'change', ->
		i = $(this).attr('i')
		if $(this).val() != ''
			remove_error_from_field($(this), i)
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
		imageurl = $('#imageurl' + i)
		image = $('#image' + i)
		tags = $('#tags' + i)
		# if all of the fields are blank, no more test is needed
		if all_fields_blank(title, description, link, imageurl, image, tags)
			return no_error
		# should have title
		if title.val() == ''
			no_error = false
			show_error_for_field(title, 'Empty title', i)
		else
			remove_error_from_field(title, i)
		# should have description
		if description.val() == ''
			no_error = false
			show_error_for_field(description, 'Empty description', i)
		else
			remove_error_from_field(description, i)
		# should have tags
		if tags.val() == ''
			no_error = false
			show_error_for_field(tags, 'Empty tags', i)
		else
			remove_error_from_field(tags, i)
			ensure_tags_has_hash_symbol(tags)
		# should have a valid link
		if not validate_link(link, i)
			no_error = false
		# should have a valid image
		if not validate_image(imageurl, image, i)
			no_error = false
		return no_error
	
	
	# all of the fields are blank
	all_fields_blank = (title, description, link, imageurl, image, tags) ->
		return title.val() == '' && description.val() == '' and link.val() == '' and
			imageurl.val() == '' && tags.val() == '' && image.val() == ''
			
	
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
	validate_link = (field, i) ->
		if field.val() == ''
			show_error_for_field(field, 'Empty link', i)
			return false
		else
			remove_error_from_field(field, i)
			if field.val().toLowerCase().indexOf('http://') != 0 && field.val().toLowerCase().indexOf('https://') != 0
				show_error_for_field(field, 'Link lacks http:// or https://, seems invalid', i)
		return true
			
	
	# test if a valid image is provided
	validate_image = (imageurl, image, i) ->
		if imageurl.val() == '' and image.val() == ''
			show_error_for_field(imageurl, 'Empty image', i)
			show_error_for_field(image, 'Empty image', i)
			return false
		else
			remove_error_from_field(imageurl, i)
			remove_error_from_field(image, i)
			value = imageurl.val().toLowerCase()
			if value
				if value.indexOf('http://') != 0 && value.indexOf('https://') != 0
					show_error_for_field(imageurl, 'Link lacks http:// or https://, seems invalid', i)
			else
				value = image.val().toLowerCase()
				if value.indexOf('.png') == -1 && value.indexOf('.jpg') == -1 && value.indexOf('.jpeg') == -1 && value.indexOf('.gif') == -1 &&
					 	value.indexOf('.svg') == -1
					show_error_for_field(image, 'Image doesn\'t seem to be in a internet friendly format: .png, ,jpg, .gif, .svn', i)
		return true
		
		
	ensure_tags_has_hash_symbol = (field) ->
		value = field.val()
		new_value = ''
		some_has_no_hash_symbol = false
		for tag in value.split(" ")
			if tag.indexOf('#') isnt 0
				some_has_no_hash_symbol = true
				new_tag = '#' + tag
			else
				new_tag = tag
			if new_value is ''
				new_value = new_tag
			else
				new_value = new_value + ' ' + new_tag
		if some_has_no_hash_symbol
			field.val(new_value)
		return

		
	$('.tagwords').on 'change', ->
		if $(this).val() isnt ''
			ensure_tags_has_hash_symbol($(this))
			
			
	$(window).scroll ->
		top = $(window).scrollTop()
		height = $(window).innerHeight();
		doc_height = $(document).height()
		sensitivity = 300
		console.log('top' + top)
		console.log('h' + height)
		console.log('dh' + doc_height)
		if top + height + sensitivity > doc_height
			console.log('load more')
			load_more_pins()
		return
			
			
	$.loading_more_pins = true
	$.ajax type: 'GET'
		,url: '/admin/input/pins/'
		,dataType: 'json'
		,data: {'offset': '0'}
		,success: (d)->
			put_more_pins_into_the_page(d)
			return
		,error: (x, textStatus, errorThrown) ->
			$.loading_more_pins = false
			console.log("Error:" + textStatus + ', ' + errorThrown)
			return
	
	load_more_pins = ->
		if not $.loading_more_pins
			$.loading_more_pins = true
			$.ajax type: 'GET'
				,url: '/admin/input/pins/'
				,dataType: 'json'
				,success: (d)->
					put_more_pins_into_the_page(d)
					return
				,error: (x, textStatus, errorThrown) ->
					$.loading_more_pins = false
					console.log("Error:" + textStatus + ', ' + errorThrown)
					return
			return
		return
		
	
	$.column_control = 1
	put_more_pins_into_the_page = (data) ->
		for pin in data
			column = $('.column' + $.column_control)
			column.append('<div class="pinbox" pinid="' + pin['id'] + '">'+
				'<div class="pin_image"><img src="/static/tmp/pinthumb' + pin['id'] + '.png"></div>' +
				'<table>' +
				'<tr><th>Title</th><td>' + pin['name'] + '</td></tr>' +
				'<tr><th>Descr.</th><td>' + pin['description'] + '</td></tr>' +
				'<tr><th>Link</th><td><a href="' + pin['link'] + '" title="' + pin['link'] + '">link</a></td></tr>' +
				'<tr><th>Tags</th><td>' + pin['tags'] + '</td></tr>' +
				'<tr><td colspan="2"><button class="button_pin_edit" pinid="' + pin['id'] + '">Edit</button> '+
				'<button class="button_pin_delete" pinid="' + pin['id'] + '">Delete</button></td></tr>' +
				'</table></div>')
			$.column_control += 1
			if $.column_control > 4
				$.column_control = 1
		$.loading_more_pins = false
		return
		
		
	$('body').on 'click', '.button_pin_delete', ->
		confirmation = window.confirm('Are you sure to delete this pin?')
		if confirmation
			pinid = $(this).attr('pinid')
			$.ajax type: 'DELETE'
				,url: '/admin/input/pins/' + pinid + '/'
			$('div.pinbox[pinid="' + pinid + '"]').remove()
		return
	
	
	$('#pin_edit_dialog').dialog autoOpen: false
								,minWidth: 500
	
	
	$('body').on 'click', '.button_pin_edit', ->
		pinid = $(this).attr('pinid')
		$.ajax type: 'GET'
			,url: '/admin/input/pins/' + pinid + '/'
			,dataType: 'json'
			,success: (pin) ->
				open_edit_dialog_for(pin)
				return
			,error: (x, textStatus, errorThrown) ->
				$.loading_more_pins = false
				console.log("Error:" + textStatus + ', ' + errorThrown)
				return
		return
		
		
	open_edit_dialog_for = (pin) ->
		$("#id11").val(pin['id'])
		$("#title11").val(pin['name'])
		$("#description11").val(pin['description'])
		$("#link11").val(pin['link'])
		$("#tags11").val(pin['tags'])
		$("#imgtag11").attr('src', '/static/tmp/pinthumb' + pin['id'] + '.png')
		$("#category11").val(pin['category'])
		$('#pin_edit_dialog').dialog('open')
		
		
	$('#pin_edit_form.submit').submit ->
		no_error = true
		pinid = $('#id11')
		title = $('#title11')
		description = $('#description11')
		link = $('#link11')
		imageurl = $('#imageurl11')
		image = $('#image11')
		tags = $('#tags11')
		# should have title
		if title.val() == ''
			no_error = false
			show_error_for_field(title, 'Empty title', 11)
		else
			remove_error_from_field(title, 11)
		# should have description
		if description.val() == ''
			no_error = false
			show_error_for_field(description, 'Empty description', 11)
		else
			remove_error_from_field(description, 11)
		# should have tags
		if tags.val() == ''
			no_error = false
			show_error_for_field(tags, 'Empty tags', 11)
		else
			remove_error_from_field(tags, 11)
			ensure_tags_has_hash_symbol(tags)
		# should have a valid link
		if not validate_link(link, 11)
			no_error = false
		if no_error
			if image.val() != '' and imageurl.val() == ''
				# submit to upload the image
				return true
			else
				update_pin_in_backgroud(pinid, title, description, link, imageurl, tags)
				$('#pin_edit_dialog').dialog('close')
		return false
		
		
	update_pin_in_backgroud = (pinid, title, description, link, imageurl, tags) ->
		pin_data = 'title': title
			,'description': description
			,'link': link
			,'imageurl': imageurl
			,'tags': tags
		$.ajax type: POST
			,data: pin_data
			,url: '/admin/input/pins/' + pinid + '/'
		return
	
	
	return