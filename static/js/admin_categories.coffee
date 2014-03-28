jQuery ->
	$('#button_add_sub_category').on 'click', (event) ->
		event.preventDefault()
		index = parseInt($('#number_of_sub_categories').val())
		form_template = $('#inline_form_add_subcategory').html()
		data = {i: index}
		html = _.template(form_template, data)
		$('#inline_forms_container').append(html)
		$('#number_of_sub_categories').val(index + 1)
		return
		
	
	$('body').on 'click', '.button_remove_subcategory', (event) ->
		event.preventDefault()
		i = $(this).attr('i')
		$('#subcategory_form' + i).remove()
		return
		
	
	$('.button_remove_category').on 'click', (event) ->
		event.preventDefault()
		category_id = $(this).attr('category_id')
		window.location = '/admin/categories/' + category_id + '/delete/'
		return