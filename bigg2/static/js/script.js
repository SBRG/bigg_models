$( document ).ready(function() {
      $("#submit").click(function(){
    $.post("hey",
    {
      name:"Donald Duck",
      city:"Duckburg"
    },
    function(data,status){
      alert("Data: " + data + "\nStatus: " + status);
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
	
});


			