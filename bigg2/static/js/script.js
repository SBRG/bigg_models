$( document ).ready(function() {
    // clickable table rows
    $(".clickable-row").click(function() {
	window.document.location = $(this).attr("href");
    });
    
    // submit buttons
    $("#submit").click(function(){
	$.post("/submiterror",
	       {
		   email: $.trim($("input[name='email']").val()),
		   comments:$.trim($("textarea[name='comments']").val()),
		   type:$.trim($("select[name='type']").val())
	       },
	       function(data,status){
		   alert("email sent");
	       });
    });
    
    // navbar position
    var navPos = $('.navbar').offset().top;

    // fixed nav on scroll
    $(window).scroll(function(){
	var checkScrollPosition = $(this).scrollTop() >= navPos;
	var setPos = checkScrollPosition ? 'fixed' : 'relative' ;
	$('.navbar').css({position: setPos});
    });
    
    // carousel start
    // $('.carousel').carousel({interval: 9000});
    
    // model buttons
    // $( "#showmodels" ).click(function () {
	
    // 	if ( $( ".btn-group-vertical" ).is( ":hidden" ) ) {
    // 	    $( ".btn-group-vertical" ).slideDown( "slow" );
    // 	} else {
    // 	    $( ".btn-group-vertical" ).hide();
    // 	}
    // });
    // $('.mlist').slideUp("fast");
    // $('.met_button').click(function(event){
    // 	event.preventDefault();
    // 	$(this).next().slideToggle("slow", function(){
	    
    // 	});
    // });
    //  $('#metabolite_c_table').slideUp("fast");
    //  $('#metabolite_p_table').slideUp("fast");
    //  $('#metabolite_e_table').slideUp("fast");
    //  $('#metabolitelist_c').click(function(){
    //  $('#metabolite_c_table').slideToggle("slow", function(){
     
    //  });
    //  });
    //  $('#metabolitelist_p').click(function(){
    //  $('#metabolite_p_table').slideToggle("slow", function(){
     
    //  });
    //  });
    //  $('#metabolitelist_e').click(function(){
    //  $('#metabolite_e_table').slideToggle("slow", function(){
     
    //  });
    //  });
});



