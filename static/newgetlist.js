(function() {
var imagedata = new Array();
$(document).ready(function() {
    function getMeta(url) {
        var img = new Image();
       img.src = url;
       img.onload = function(){gallery.setdata({url: url, w: this.width, h: this.height});}
    }
    $( "#dialog-form" ).dialog({
	        autoOpen: false,
	        height: 250,
	        width: 450,
	        modal: true,
	        show: {
                effect: "clip",
                duration: 200
              }
	        });
	$( "#getlist-from-web" ).dialog({
	        autoOpen: false,
	        height: 200,
	        width: 450,
	        modal: true,
	        show: {
                effect: "clip",
                duration: 200
              }
	        });
    $("#web_getlist_link").click(function(){
        $( "#getlist-from-web" ).dialog( "open" );
    });
    $("#add_getlist_link").click(function(){
        $( "#dialog-form" ).dialog( "open" );
    });

    $("#upload_cancel").click(function(){
        $( "#dialog-form" ).dialog( "close" );
    });

    $("#get_cancel").click(function(){
        $( "#getlist-from-web" ).dialog( "close" );
    });

    $( "#addpindialogform" ).dialog({
	        autoOpen: false,
	        height:650,
	        width: 700,
	        modal: true
	        });
	$( "#addpindialogformweb" ).dialog({
	        autoOpen: false,
	        height:700,
	        width: 800,
	        modal: true
	        });
    function validate(){
        if ($("#image").val() === ''){
            $("#status").html("please choose a file");
            return false;
        }else{
            return true
        }
    }
    var bar = $('.bar');
    var percent = $('.percent');

    $('#upload_form').ajaxForm({
        beforeSend: function(xhr, opts) {

            $(".progress").show();
            var percentVal = '0%';
            bar.width(percentVal)
            percent.html(percentVal);
            if  (!validate()){
                xhr.abort();
            }else{
                return true
            }

        },
        uploadProgress: function(event, position, total, percentComplete) {
            $(".progress").show();
            var percentVal = percentComplete + '%';
            bar.width(percentVal)
            percent.html(percentVal);
        },
        success: function() {
            $(".progress").show();
            var percentVal = '100%';
            bar.width(percentVal)
            percent.html(percentVal);
        },
	    complete: function(xhr) {
	       $(".progress").hide();
	        $( "#dialog-form" ).clearForm();
	        var percentVal = '0%';
            bar.width(percentVal)
            percent.html(percentVal);
            var obj = jQuery.parseJSON( xhr.responseText );
            $("#fname").val(obj.fname);
            $("#imagename").html(obj.original_filename);
	        $( "#dialog-form" ).dialog("close");
	        $("#imagediv").html('<img src="'+'/static/tmp/pinthumb'+obj.fname+'.png" alt="">')
		    $( "#addpindialogform" ).dialog("open");
		    $("#comments").focus();
	    }
    });


    var barweb = $('.bar');
    var percentweb = $('.percent');
    $("#gallerynextweb").on("click",(function(){gallery.next();}));
    $("#galleryprevweb").on("click",(function(){gallery.prev();}));

    $('#fetch-images').click(function(){
    $.ajax({
        url:"/preview",
        data:{
        url:$("#url").val(),
        },
        beforeSend: function(xhr, opts) {
            $(".progress").show();
            var percentVal = '0%';
            barweb.width(percentVal)
            percentweb.html(percentVal);
            var percent = 0;
            setInterval(function(){if(percent<100){percent+=10;showprogress(percent);}},50);
        },
        success: function() {
            $(".progress").show();
            var percentVal = '100%';
            barweb.width(percentVal)
            percentweb.html(percentVal);
        },
	    complete: function(xhr) {
	       var data = jQuery.parseJSON(xhr.responseText);
           if(data.status !== "error"){
	            $(".progress").hide();
	            $("#websitelinkweb").val($("#url").val());
	            $( "#web_getlist_form" ).clearForm();
	            $( "#getlist-from-web" ).dialog("close");
	            var percentVal = '100%';
                barweb.width(percentVal)
                percentweb.html(percentVal);
                $( "#addpindialogformweb" ).dialog("open");
                $("#commentsweb").focus();
                initgallery(data);
            }else{
                $("#statusweb").html("please provide a valid image url");
                return false;
            }

	    }
    })});

    function showprogress(percentComplete){
        $(".progress").show();
        var percentVal = percentComplete + '%';
        barweb.width(percentVal)
        percentweb.html(percentVal);
    }

    function initgallery(data){
        gallery.lengthTotal = data["images"].length
        gallery.data = new Array();
        for(i=0; i<data["images"].length;i++){
            getMeta(data["images"][i]);
        }

        gallery.init();

    }

    function getCategories(name){
        var elements = $("input[name="+name+"]");
        var categories = new Array();
        $.each(elements, function(id,v){
            if($(v).prop('checked')){
                categories.push($(v).val());
            }
        });
        return categories.join();

    }

    function getdata(){
        var data = {
            'title':$("#title").val(),
            'weblink':$("#weblink").val(),
            'category':getCategories("category_check"),
            'lists':$("#board").val(),
            'comments':$("#comments").val(),
            'fname':$("#fname").val(),
        }
        return data
    }

    function getdataweb(){
        var data = {
            'title':$("#titleweb").val(),
            'link':$("#weblinkweb").val(),
            'categories':getCategories("category_check_web"),
            'description':$("#commentsweb").val(),
            'image_url':$("#image_urlweb").val(),
            'list':$("#boardweb").val(),
            'price':$("input:radio[name='price_range']:checked").val()||'',
            'websiteurl':$("#websitelinkweb").val(),
            'board_name':''
        }
        return data
    }

    function successcall(data){
        //$( "#addpindialogform" ).dialog("close");
        $(location).attr('href',data);
    }

    $('#cancelfancy').click(function(){
        $( "#addpindialogform" ).dialog("close");
    });

    $('#cancelfancyweb').click(function(){
        $( "#addpindialogformweb" ).dialog("close");
    });


    $('#ajaxpinform').submit(function() {
        // submit the form
        $(this).ajaxSubmit({
        beforeSubmit: validate_from_upload,
        data:getdata(),
        success: successcall});
        // return false to prevent normal browser submit and page navigation
        return false;
    });

    $('#ajaxpinformweb').submit(function() {
        // submit the form
        $(this).ajaxSubmit({
        beforeSubmit: validate_from_web,
        data:getdataweb(),
        success: successcall});
        // return false to prevent normal browser submit and page navigation
        return false;
    });

    function validate_from_upload(formData, jqForm, options) {
        var title = $("#title");
        var weblink = $("#weblink");
        var list = $("#board");
        var cat = getCategories("category_check");
        var category = $("input[name=category_check]");

        var errors = new Array();
        if(cat===""){
            errors.push(category);
        }else{
            $.each(category, function(i,v){
                $(v).attr("style", "");
            });
        }

        if(title.val()===""){
            errors.push(title);
        }else{
            title.attr("style", "");
        }
        if(weblink.val()===""){
            errors.push(weblink);
        }else{
            weblink.attr("style", "");
        }
        if(list.val()===""){
            errors.push(list);
        }else{
            list.attr("style", "");
        }
        if (errors.length>0){
            for (i=0;i<errors.length;i++){
                if(errors[i] instanceof jQuery){
                    $.each(errors[i], function(i,v){
                        $(v).attr("style", "outline:1px solid red;");
                    });
                }else{
                    errors[i].attr("style", "border:1px solid red;");
                }
            }
            return false;
        }
        return true;
    }

    function validate_from_web(formData, jqForm, options) {
        var title = $("#titleweb");
        var list = $("#boardweb");
        var cat = getCategories("category_check_web");
        var category = $("input[name=category_check_web]");

        var errors = new Array();
        if(cat===""){
            errors.push(category);
        }else{
            $.each(category, function(i,v){
                $(v).attr("style", "");
            });
        }
        if(title.val()===""){
            errors.push(title);
        }else{
            title.attr("style", "");
        }
        if(list.val()===""){
            errors.push(list);
        }else{
            list.attr("style", "");
        }
        if (errors.length>0){
            for (i=0;i<errors.length;i++){
                if(errors[i] instanceof jQuery){
                    $.each(errors[i], function(i,v){
                        $(v).attr("style", "outline:1px solid red;");
                    });
                }else{
                    errors[i].attr("style", "border:1px solid red;");
                }

            }
            return false;
        }
        return true;
    }

    var gallery = {
        data: new Array(),
        element: $("#slide-imageweb"),
        setdata: function(data){
            this.lengthTotal = this.lengthTotal - 1;
            if(data.w>200 ||data.h>200){
                this.data.push(data);
            }

            if(this.lengthTotal===0){
                this.len = this.data.length;
                this.showitem();
            }
        },
        next: function(){
            if (this.current<this.len-1){
                this.current += 1;
            }
            this.showitem();
        },
        prev: function(){
            if (this.current>0){
                this.current -= 1;
            }
            this.showitem();
        },
        showitem : function(){
            this.element.attr("src", this.data[this.current].url);
            $("#image_urlweb").attr("value", this.data[this.current].url);
            this.showstatus();
        },
        showstatus : function(){
            $("#status-textweb").html("   "+(this.current+1) + " of "+this.len);
        },
        init: function(){
            this.element = $("#slide-imageweb");
            this.current = 0;
            this.element.attr("src","");
        }

    }

    $('#button_add_board').on('click', function(event) {
    	event.preventDefault();
    	$('#board').val('');
    	$('#board_selection_layer').hide();
    	$('#board_creation_layer').show();
    });

    $('#button_select_board').on('click', function(event) {
    	event.preventDefault();
    	$('#board_name').val('');
    	$('#board_creation_layer').hide();
    	$('#board_selection_layer').show();
    });

    $('#button_add_boardweb').on('click', function(event) {
        event.preventDefault();
        $('#board').val('');
        $('#board_selection_layerweb').hide();
        $('#board_creation_layerweb').show();
    });

    $('#button_select_boardweb').on('click', function(event) {
        event.preventDefault();
        $('#board_name').val('');
        $('#board_creation_layerweb').hide();
        $('#board_selection_layerweb').show();
    });

    });

}).call(this);
