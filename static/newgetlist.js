(function() {
var imagedata = new Array();
$(document).ready(function() {
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

    $( "#addpindialogform" ).dialog({
	        autoOpen: false,
	        height:500,
	        width: 700,
	        modal: true
	        });
	$( "#addpindialogformweb" ).dialog({
	        autoOpen: false,
	        height:500,
	        width: 700,
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
	            $( "#web_getlist_form" ).clearForm();
	            $( "#getlist-from-web" ).dialog("close");
	            var percentVal = '100%';	        
                barweb.width(percentVal)
                percentweb.html(percentVal);            
                $( "#addpindialogformweb" ).dialog("open");
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
        var imagedata=new Array();
        for(i=0; i<data["images"].length;i++){
            imagedata.push({"url":data["images"][i], 'caption':i});
        }
        gallery.init(imagedata);
       
    }

    function getdata(){
        var data = {
            'title':$("#title").val(),
            'weblink':$("#weblink").val(),
            'category':$("#category").val(),
            'lists':$("#lists").val(),
            'comments':$("#comments").val(),
            'fname':$("#fname").val(),
        }
        return data
    }
    
    function getdataweb(){
        var data = {
            'title':$("#titleweb").val(),
            'link':$("#weblinkweb").val(),
            'categories':$("#categoryweb").val(),
            'description':$("#commentsweb").val(),
            'image_url':$("#image_urlweb").val(),
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
        data:getdata(),
        success: successcall});
        // return false to prevent normal browser submit and page navigation
        return false;
    });
    
    $('#ajaxpinformweb').submit(function() {
        // submit the form
        $(this).ajaxSubmit({
        data:getdataweb(),
        success: successcall});
        // return false to prevent normal browser submit and page navigation
        return false;
    });
    
    var gallery = {
        element: $("#slide-imageweb"),
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
        init: function(data){
            this.data = data;
            this.len = data.length;
            this.element = $("#slide-imageweb");
            this.current = 0;
            this.showitem();
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

    });

}).call(this);
