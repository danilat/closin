var map = null;
var markers = [];
var infowindow = new google.maps.InfoWindow();
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
		icon: '/cache/markers/marker-'+cat+'.png'
	});
	google.maps.event.addListener(marker, 'click', function() {
		var content = '<strong>' + title + '</strong>';
		if (subtitle){
			content += '<br/><br/>'+ subtitle;
		}
		infowindow.setContent(content);
		infowindow.open(map, marker);
	});
	markers.push(marker);
}

function showMap(cat) {	
	deleteMarkers();
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

function initMap() {
	var center = new google.maps.LatLng(41.641184, -0.894032);
	var zoom = 16;
	
	var myOptions = {
		zoom: zoom,
		center: center,
		zoomControl: true,
		disableDefaultUI: true,
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
				icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
			});
		});
	}
}
function deleteMarkers(){
	for (var i = 0; i < markers.length; i++) {
		markers[i].setMap(null);
	}
	markers = [];
}
initMap()