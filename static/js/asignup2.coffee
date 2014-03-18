pin_count = 0

$('body').on 'mouseleave', '.pin-add-button', ->
		console.log('remove')
		$(this).remove()
		return
		
$('body').on 'click', '.select_pins', (event) ->
    event.stopPropagation()
    click_to_add_pin($(this))
        
$('body').on 'click', '.pin-add-button', ->
	click_to_add_pin($(this))
	
$('img').load ->
	$(this).addClass('loaded_img')

click_to_add_pin = (elem) ->
        pin_id = elem.attr('pinid')
        console.log pin_id
        add_pin_to_user(pin_id)
        show_cover(pin_id)
        return
        
show_button_add = (original_div, pin_id) ->
	$('body').append('<div class="pin-add-button" pinid="' + pin_id + '">' +
		'<button class="select_pins" style="margin-bottom: 10px;" pinid="' + pin_id + '">Get it</button>' +
		'</div>')
	cover_div = $('.pin-add-button[pinid="' + pin_id + '"]')
	cover_div.offset(original_div.offset())
	cover_div.width(original_div.width() + 3)
	cover_div.height(original_div.height() + 3)
	cover_div.css( "z-index", pin_id)
	selection_button = $('.select_pins[pinid="' + pin_id + '"]')
	selection_button.css('margin-top', (original_div.height() / 2) - (selection_button.height() / 2))
	cover_div.css( "visibility", "visible")
	console.log('show')
	return

show_button_remove = (original_div, pin_id) ->
	return

hide_buttons = (pin_id) ->
    console.log('remove')
    cover_div = $('.pin-add-button[pinid="' + pin_id + '"]')
    cover_div.css( "visibility", "hidden")

$(".pin-image").mouseenter ->
        console.log('hover')
        image = $(this).children('img:first')
        if image.hasClass('loaded_img')
            pin_id = $(this).attr('pinid')
            if $(this).hasClass("selected")
        	    show_button_remove($(this), pin_id)
            else
        	    show_button_add($(this), pin_id)
        return
        
$('body').on 'click', '.cover', ->
        pin_id = $(this).attr('pinid')
        original_div = $(this)
        remove_pin_from_user(pin_id)
        original_div.remove()
        
show_cover = (pin_id) ->
    original_div = $('.pin-image[pinid="' + pin_id + '"]')
    $('body').append('<div class="cover" pinid="' + pin_id + '"><div class="txtselected">selected</div></div>')
    cover_div = $('div.cover[pinid="' + pin_id + '"]')
    cover_div.offset(original_div.offset())
    cover_div.width(original_div.width() + 3)
    cover_div.height(original_div.height() + 3)
    cover_div.css( "z-index", pin_id)
    cover_div.css( "visibility", "visible")
    return
                
add_pin_to_user = (pin_id) ->
        $('.pin-image[pinid="' + pin_id + '"]').addClass('selected')
        $.ajax "/register/api/users/me/coolpins/#{pin_id}/",
                        type: 'PUT'
                        dataType: 'json'
        pin_count += 1
        if pin_count > 4
                $('#continue_button').removeAttr('disabled')

remove_pin_from_user = (pin_id) ->
        $('.pin-image[pinid="' + pin_id + '"]').removeClass('selected')
        $.ajax "/register/api/users/me/coolpins/#{pin_id}/",
                        type: 'DELETE'
                        dataType: 'json'
        pin_count -= 1
        if pin_count < 5
                $('#continue_button').attr('disabled', 'disabled')

$("#continue_button").click ->
        window.location.href = '3'

$("#skip_button").click ->
	username = $(this).attr('username')
	window.location.href = '/' + username
