$( document ).ready(function() {
      $("#submit").click(function(){
    $.post("/submiterror",
    {
      email: $.trim($("input[name='email']").val()),
      comments:$.trim($("textarea[name='comments']").val())
    },
    function(data,status){
      alert(data);
    });
  });
	var navPos = $('.navbar').offset().top;

	$(window).scroll(function(){
		var checkScrollPosition = $(this).scrollTop() >= navPos;
		var setPos = checkScrollPosition ? 'fixed' : 'relative' ;
		$('.navbar').css({position: setPos});
	});
	
	$('.carousel').carousel({interval: 9000});
		
	$( "#showmodels" ).click(function () {
			
		if ( $( ".btn-group-vertical" ).is( ":hidden" ) ) {
			$( ".btn-group-vertical" ).slideDown( "slow" );
		} else {
			$( ".btn-group-vertical" ).hide();
		}
	});
	$('#metabolite_c_table').slideUp("fast");
	$('#metabolite_p_table').slideUp("fast");
	$('#metabolite_e_table').slideUp("fast");
	$('#metabolitelist_c').click(function(){
	    $('#metabolite_c_table').slideToggle("slow", function(){
	    
	    });
	});
		$('#metabolitelist_p').click(function(){
	    $('#metabolite_p_table').slideToggle("slow", function(){
	    
	    });
	});
		$('#metabolitelist_e').click(function(){
	    $('#metabolite_e_table').slideToggle("slow", function(){
	    
	    });
	});
});


			
