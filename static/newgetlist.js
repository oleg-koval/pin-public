(function() {

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

    $("#add_getlist_link").click(function(){
        $( "#dialog-form" ).dialog( "open" );
    });

    $("#upload_cancel").click(function(){
        $( "#dialog-form" ).dialog( "close" );
    });

    $( "#addpindialogform" ).dialog({
	        autoOpen: false,
	        height:450,
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

    function successcall(data){
        //$( "#addpindialogform" ).dialog("close");
        $(location).attr('href',data);
    }

    $('#cancelfancy').click(function(){
        $( "#addpindialogform" ).dialog("close");
    });

    $('#ajaxpinform').submit(function() {
        // submit the form
        $(this).ajaxSubmit({
        data:getdata(),
        success: successcall});
        // return false to prevent normal browser submit and page navigation
        return false;
    });
    
    
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
