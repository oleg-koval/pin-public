pin_count = 0

$(".select_pins").click ->
	pin_id = $(this).attr('pinid')
	console.log pin_id
	if $(this).hasClass("selected")
		remove_pin_from_user(pin_id, $(this))
	else
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

remove_pin_from_user = (pin_id, button) ->
	$.ajax "/register/api/users/me/coolpins/#{pin_id}/",
			type: 'DELETE'
			dataType: 'json'
			success: (data) ->
				button.removeClass 'selected'
				pin_count -= 1
				if pin_count < 5
					$('#continue_button').attr('disabled', 'disabled')

$("#continue_button").click ->
	window.location.href = '3'