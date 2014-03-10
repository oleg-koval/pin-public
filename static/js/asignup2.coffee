pin_count = 0

$(".select_pins").click ->
	pin_id = $(this).attr('pinid')
	console.log pin_id
	add_pin_to_user(pin_id, $(this))
		
add_pin_to_user = (pin_id, button) ->
	$.ajax "/register/api/users/me/coolpins/#{pin_id}/",
			type: 'PUT'
			dataType: 'json'
			success: (data) ->
				button.addClass 'selected'
	pin_count += 1
	if pin_count > 4
		$('#continue_button').removeAttr('disabled')

$("#continue_button").click ->
	window.location.href = '3'