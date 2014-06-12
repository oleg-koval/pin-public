
(function() {
  $("#switch1").mouseover(function() {
    return $("#menu1").show();
  });
  $("#switch1").mouseout(function() {
    return $("#menu1").hide();
  });
  $("#switch2").mouseover(function() {
    return $("#menu2").show();
  });
  $("#switch2").mouseout(function() {
    return $("#menu2").hide();
  });
  $("#switch3").mouseover(function() {
    return $("#menu3").show();
  });
  $("#switch3").mouseout(function() {
    return $("#menu3").hide();
  });
}).call(this);

$(document).ready(function() {
  var id;
  $("#remove_photo, #remove_photo1").click(function(e) {
    var result;
    result = window.confirm("Are you sure you want to remove this picture ?");
    if (!result) {
      e.preventDefault();
      e.event.stopPropagation();
      return false;
    }
    e.event.stopPropagation();
  });
  $("#pin-feed").click(function() {
      hide_all();
      show_feeds();
  });
  $("#pin-not-added").click(function() {
        show_pins_not_added();
  });
  $("#pin-added").click(function() {
      show_pins_not_added();
        hide_pins_date();
  });
  id = $(".carousel2").find(".active").attr("photoid");
  $("#remove_photo").attr("href", "/photo/" + id + "/remove");
  $(".album_item").click(function() {
    id = $(this).attr("data-photoid");
    $("#remove_photo").attr("href", "/photo/" + id + "/remove");
  });
  $(".carousel1").carousel({
    interval: false
  });
  $(".carousel2").carousel({
    interval: false
  }).on("slid.bs.carousel", function(e) {
    var xx;
    xx = $(this);
    id = xx.find(".active").attr("photoid");
    $("#remove_photo").attr("href", "/photo/" + id + "/remove");
  });
  show_feeds(); 
});

function hide_pins_date() {
  $(".dateWrap").each(function() {
    if($('.dwContent .dwItem:not(.pin-not-added)', this).length == 0) {
      $(this).hide();
    }
  });
}

function show_pins_date() {
  $(".dateWrap").each(function() {
    $(this).show();
  });
}

function hide_all() {
//   $("#pin-buf").hide();
   $("#feed-buf").hide();
}

function show_feeds() {
    hide_all();
    $("#feed-buf").show();
    $(".pin-added").each(function() {
      $(this).show();
    });
    $(".pin-not-added").each(function() {
      $(this).show();
    });
}

function show_pins_not_added() {
    hide_all();
    show_pins_date();
    $(".pin-added").each(function() {
      $(this).hide();
    });
    $(".pin-not-added").each(function() {
      $(this).show();
    });

    $("#pin-buf").show();
}
