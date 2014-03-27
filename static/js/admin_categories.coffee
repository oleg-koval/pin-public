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
		