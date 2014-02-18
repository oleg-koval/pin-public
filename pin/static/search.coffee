window.addToUrl = (k, v) ->
    pairs = window.location.search.split '&'
    newSearch = []
    found = false

    for pair in pairs
        [key, value] = pair.split '='
        if k == key
            value = v
            found = true
        newSearch.push(key + '=' + value)

    if not found
        newSearch.push(k + '=' + v)

    window.location.search = newSearch.join '&'
