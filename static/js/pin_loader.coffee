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