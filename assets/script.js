$( document ).ready(function() {

	var navPos = $('.navbar').offset().top;

	$(window).scroll(function(){
		var checkScrollPosition = $(this).scrollTop() >= navPos;
		var setPos = checkScrollPosition ? 'fixed' : 'relative' ;
		$('.navbar').css({position: setPos});
	});
	
	$('.carousel').carousel({interval: 8000});
		
	$( "#showmodels" ).click(function () {
			
		if ( $( ".btn-group-vertical" ).is( ":hidden" ) ) {
			$( ".btn-group-vertical" ).slideDown( "slow" );
		} else {
			$( ".btn-group-vertical" ).hide();
		}
	});
	
});


			