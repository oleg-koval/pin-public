category_count = 0
$('.loldongs').on 'click', ->
        category_id = $(this).attr('categoryid')
        original_div = $(this)
        add_category_to_user(category_id, $(this))
        show_cover(original_div, category_id)

$('body').on 'click', '.cover', ->
        category_id = $(this).attr('categoryid')
        original_div = $(this)
        remove_category_from_user(category_id, $(this))
        original_div.remove()
        
show_cover = (original_div, category_id) ->
    $('body').append('<div class="cover" categoryid="' + category_id + '"><div class="txtselected">selected</div></div>')
    cover_div = $('div.cover[categoryid="' + category_id + '"]')
    cover_div.offset(original_div.offset())
    cover_div.width(original_div.width() + 3)
    cover_div.height(original_div.height() + 3)
    cover_div.css( "z-index", category_id)
    cover_div.css( "visibility", "visible")
    return

add_category_to_user = (category_id, button) ->
        $.ajax "/register/api/users/me/category/#{category_id}/",
                        type: 'PUT'
                        dataType: 'json'
        button.addClass 'selected'
        category_count += 1
        if category_count > 2
                $('#continue_button').removeAttr('disabled')

remove_category_from_user = (category_id, button) ->
        $.ajax "/register/api/users/me/category/#{category_id}/",
                        type: 'DELETE'
                        dataType: 'json'
        button.removeClass 'selected'
        category_count -= 1
        if category_count < 3
                $('#continue_button').attr('disabled', 'disabled')

$("#continue_button").click ->
        window.location.href = 'after-signup/2'

$("#skip_button").click ->
	username = $(this).attr('username')
	window.location.href = '/' + username
