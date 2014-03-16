preview = $('<div/>').addClass('preview')
preview.insertAfter $('#input-url')

images = []

window.imagesLoading = false

$('#input-url').blur ->
    url = $(this).val()
    $('#input-link').val(url)

    if url.replace('https://', '').replace('http://', '').indexOf('/') == -1
        url += '/'

    window.imagesLoading = true
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
            images = []

            for src in data.images
                images.push src
                if first
                    img = $('<img/>').attr('src', src).attr('id', counter++).addClass('selected')
                    window.selected = src
                    first = false
                else
                    img = $('<img/>').attr('src', src).attr('id', counter++)

                preview.append img
                img.click ->
                    src = images[parseInt($(this).attr('id'))]
                    window.selected = src
                    preview.find('img').removeClass('selected')
                    $(this).addClass('selected')

        window.imagesLoading = false

$('#form').submit ->
    if window.imagesLoading
        alert("Please wait for all images to load.")
        return false

    if window.selected
        $('#input-url').val window.selected
    else
        alert("Please select at least one image.")
        return false

    true
