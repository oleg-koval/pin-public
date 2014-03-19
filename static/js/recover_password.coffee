jQuery ->
	$.verification_running = false
	$.last_value_verified = ''
	
	
	$('#username').keyup ->
		if not $.verification_running
			value = $(this).val()
			if value isnt ''
				verify_username()
			else
				clear_any_notification()
		return
		
	
	verify_username = () ->
		$.verification_running = true
		current_value = $('#username').val()
		if current_value == ''
			clear_any_notification()
			$.verification_running = false
			$.last_value_verified = ''
		else
			if current_value != $.last_value_verified
				$.last_value_verified = current_value
				show_verifying()
				$.ajax method: 'GET'
					,url: '/recover_password_username_test/'
					,dataType: 'json'
					,data: {'username': current_value}
					,success: verification_callback
					,error: verification_error_callback
			else
				$.verification_running = false
		return
		
	verification_callback = (data) ->
		status = data['status']
		switch status
			when 'ok' then show_verification_ok()
			when 'notfound' then show_verification_notfound()
			else clear_any_notification()
		$.verification_running = false
		current_value = $('#username').val()
		if current_value != '' && current_value != $.last_value_verified
			verify_username()
		return
		
		
	verification_error_callback = (jqXHR, textStatus, errorThrown) ->
		$.verification_running = false
		clear_any_notification()
		
	
	show_verification_ok = ->
		clear_any_notification()
		$('#username').after('<span class="green">Looks good!</span>')
		return
		
		
	show_verification_notfound = ->
		clear_any_notification()
		$('#username').after('<span class="red">Invalid username or email</span>')
		return
		
		
	show_verifying = ->
		clear_any_notification()
		$('#username').after('<span class="black">Verifying</span>')
		return
	
	
	clear_any_notification = ->
		$('#username').nextAll('span.green,span.red,span.black').remove()
		return
	
	
	return