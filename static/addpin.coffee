preview = $('#preview')

images = []

window.imagesLoading = false

$('#link,#product_url').change ->
    value = $(this).val()
    if value isnt '' and (value.indexOf('http://') isnt 0 or value.indexOf('http://') isnt 0)
        if value.indexOf('//') == 0
            $(this).val('http:' + value)
        else
            $(this).val('http://' + value)
    if value isnt ''
    	clear_error_for_field($('#link,#product_url'))
    if window.imagesLoading
        return false
    if $('#image_url').val() == undefined
    	return false
    window.imagesLoading = true
    url = $(this).val()
    $('#input-link').val(url)

    if url.replace('https://', '').replace('http://', '').indexOf('/') == -1
        url += '/'

    preview.html 'loading images&hellip;'
    $('#btn-add').prop('disabled', true)

    $.getJSON '/preview?url=' + url, (data) ->
        $('#btn-add').prop('disabled', false)
        preview.html ''

        if 'title' of data
            $('#input-desc').val data.title

        if 'images' of data
            first = true
            counter = 0
            preview.html '<h4>Choose an image:</h4>'

            for src in data.images
                image_source = {'src': src}
                img = _.template($('#image-template').html(), image_source)
                if first
                    if $('#image_url').val() is ''
                        $('#image_url').val(src)
                        $('#image_url').change()
                    first = false

                preview.append img
        window.imagesLoading = false
        return


$('#image_url').on 'change', ->
    value = $(this).val()
    if value isnt '' and (value.indexOf('http://') isnt 0 or value.indexOf('http://') isnt 0)
        if value.indexOf('//') == 0
            $(this).val('http:' + value)
        else
            $(this).val('http://' + value)
    if value isnt ''
    	clear_error_for_field($(this))
    	$('#preview_of_selected_image').prop('src', value)
    	$('#layer_preview_of_selected_image').show()
    else
    	$('#layer_preview_of_selected_image').hide()
    return
    	
    	
$('#tags,#title').on 'change', ->
	if $(this).val() isnt ''
		clear_error_for_field($(this))
	return


$('#preview').on 'click', 'img', ->
    src = $(this).attr('src')
    $('#image_url').val(src)
    $('#image_url').change()
    $('img.clickable').removeClass('selected')
    $(this).addClass('selected')
    return
    
    
$('input[name=price_range]').on 'change', ->
	clear_error_for_field($('#price_range'))
	return
    
    
$('input[name=category_check]').on 'change', ->
	clear_error_for_field($('#categories'))
	return


$('#form').submit ->
    if window.imagesLoading
        alert("Please wait for all images to load.")
        return false

    clear_all_error_messages()
    errors = false
    if $('#product_url').val() is '' and $('#link').val() is ''
        show_error_for_field($('#product_url'), 'Please provide a Product URL or Source URL')
        show_error_for_field($('#link'), 'Please provide a Product URL or Source URL')
        errors = true
    if $('#title').val() is ''
        show_error_for_field($('#title'), 'Please provide a title')
        errors = true
    if $('#tags').val() is ''
        show_error_for_field($('#tags'), 'Please provide tag words')
        errors = true
    if not have_valid_price()
        show_error_for_field($('#price'), 'Only numbers and decimal point')
        errors = true
    if not selected_a_price_range()
        errors = true
    if not category_selected()
        show_error_for_field($('#categories'), 'Select one or more categories for this product')
        errors = true

    if $('#image_url').val() isnt undefined
        if $('#image_url').val() is ''
            show_error_for_field($('#image_url'), 'Provide the image URL or select an image from the right (if available)')
            errors = true
    else if $('#image').val() is ''
        show_error_for_field($('#image'), 'Provide the image file to upload')
        errors = true
        
    if $('#board_id').val() is '' and $('#board_name').val() is ''
    	errors = true
    	show_error_for_field($('#layer_add_new_board'), 'Select or create a new getlist')
    	$('#button_change_layer_to_select_existing_board').click()

    if errors
        alert("Ooops, there are missing fields to fill, please review...")
        return false
    true


# test price has format with only digits and decimal point
price_regex  = /^\d+(?:\.?\d{0,2})$/;
have_valid_price = ->
	price = $('#price')
	if price.val() is ''
		# the field is optional, no validation is not given
		return true
	new_val = price.val().replace(/[^\d\.]/g, '')
	price.val(new_val)
	if not price_regex.test(price.val())
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
selected_a_price_range = ->
	price_range = $('input[name=price_range]:checked').val()
	if price_range is undefined
		show_error_for_field($('#price_range'), 'Select a price range')
		return false
	return true


# shows an error for the field
show_error_for_field = (field, text) ->
	field.addClass('field_error')
	field.after('<div class="error_text">' + text + '</div>')
	return


clear_error_for_field = (field) ->
	field.removeClass('field_error')
	field.next('div.error_text').remove()
	return


clear_all_error_messages = ->
	$('input').removeClass('field_error')
	$('div.error_text').remove()
	return

	
category_selected =  ->
	checked_categories = $('input[name=category_check]:checked')
	if checked_categories.length > 0
		category_value = ''
		for c in checked_categories
			value = c.value
			if category_value isnt '' and category_value.lastIndexOf(',') isnt category_value.length - 1
				category_value = category_value + ','
			category_value = category_value + value
		$('#categories').val(category_value)
		return true
	else
		return false

		
$('#button_change_layer_to_add_new_board').on 'click', (event) ->
	event.preventDefault()
	$('#board_id').val('')
	$('#layer_select_existing_board').hide()
	$('#layer_add_new_board').show()
	
	
$('#button_change_layer_to_select_existing_board').on 'click', (event) ->
	event.preventDefault()
	$('#board_name').val('')
	$('#layer_add_new_board').hide()
	$('#layer_select_existing_board').show()