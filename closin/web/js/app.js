var map = null;
var markers = [];
var infowindow;
var coordenates;
var insertValues;

function removeMarkers() {
	while(markers.length > 0) {
		markers.pop().setMap(null);
	}
}

function addMarker(lat, lon, title, subtitle, cat, id) {
	var marker = new google.maps.Marker({
		position: new google.maps.LatLng(lat, lon),
		map: map,
		title: title,
		icon: '/cache/images-004/icono.png'
	});
	if(id.length > 0) {
		google.maps.event.addListener(marker, 'click', function() {
			showDetail(id, cat, title, subtitle, lat, lon);
		});
	} else {
		google.maps.event.addListener(marker, 'click', function() {
			infowindow = new google.maps.InfoWindow({
				content: subtitle + ' - <strong>' + title + '</strong>'
			});
			infowindow.open(map, marker);
		});
	}
	markers.push(marker);
}

function showMap(cat) {
	$('#categories').hide();
	$('#map-wrapper').show();
	$('#detail').hide();
	$(".service-type").html(cat);
	
	if(!map) {
		initMap();
	}
	
	$.ajax({ url: '/fetch?service='+cat,
		dataType: 'json',
		success: function(data) {
			var n = data.length;
			for(i=0; i<n; i++) {
				var place = data[i];
				var lat = place['lat'];
				var lon = place['lon'];
				var title = place['title'];
				var subtitle = place['subtitle'];
				var id = place['id'];
				addMarker(lat, lon, title, subtitle, cat, id);
			}
		}
	});
}

function showDetail(id, service, title, subtitle, lat, lon) {
	$("#detail-list").html("<li>Cargando...</li>");
	$("#detail-title").html(title+"<br/>"+subtitle);
	$('#categories').hide();
	$('#map-wrapper').hide();
	$('#detail').show();
	if(coordenates){
		$('#how-to-go').attr('href', 'http://maps.google.com/maps?saddr='+coordenates.latitude+','+coordenates.longitude+'&daddr='+lat+','+lon+'&dirflg=w');
		$('#how-to-go').show();
	}
	
	insertValues = { "id": id, "name": title, "latitude": lat, "longitude": lon, "service": service}
	
	$.ajax({ url: '/point?service='+service+'&id='+id,
		dataType: 'json',
		success: function(data) {
			$("#detail-list").html("");
			var items = data["items"];
			var n = items.length;
			for(i=0; i<n; i++) {
				var lines = items[i];
				if(lines.length == 1) {
					$("#detail-list").append("<li>"+items[i][0]+"</li>");
				} else {
					$("#detail-list").append("<li>"+items[i][0]+"<br/>"+items[i][1]+"</li>");
				}
			}
		},
		error: function() {
			alert("Error en la conexión");
		}
	});
}

function backToMap() {
	$('#categories').hide();
	$('#detail').hide();
	$('#map-wrapper').show();
}

function showHome() {
	$('#categories').show();
	$('#map-wrapper').hide();
	$('#detail').hide();
	removeMarkers();
}

function initMap() {
	var center = new google.maps.LatLng(41.641184, -0.894032);
	var zoom = 16;
	
	var disableDefaultUI = true;
	var navigationControl = false;
	if(!jQuery.browser.mobile){
		$("#map-container").addClass("desktop-map-container");
		$("#map-container").removeClass("mobile-map-container");
		disableDefaultUI = false;
		navigationControl = true;
	}
	var myOptions = {
		zoom: zoom,
		center: center,
		navigationControl: navigationControl,
		disableDefaultUI: disableDefaultUI,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};
	
	
	map = new google.maps.Map(document.getElementById("map-container"), myOptions);

	if(navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
			var location = new google.maps.LatLng(
				position.coords.latitude,
				position.coords.longitude);
			map.setCenter(location);
			coordenates = position.coords;
				
			var marker = new google.maps.Marker({
				position: location,
				map: map,
				icon: '/cache/images-004/ico_localizacion.png'
			});
		});
	}
}

/**
 * jQuery.browser.mobile (http://detectmobilebrowser.com/)
 *
 * jQuery.browser.mobile will be true if the browser is a mobile device
 *
 **/
(function(a){jQuery.browser.mobile=/android.+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|e\-|e\/|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(di|rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|xda(\-|2|g)|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))})(navigator.userAgent||navigator.vendor||window.opera);