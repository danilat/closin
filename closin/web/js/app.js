var Geolocation = {
  rad: function(x) { return x * Math.PI / 180 },

  // Distance in kilometers between two points using the Haversine algo.
  distance: function(p1, p2) {
    var R = 6371
    var dLat  = this.rad(p2.latitude - p1.latitude)
    var dLong = this.rad(p2.longitude - p1.longitude)

    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(this.rad(p1.latitude)) * Math.cos(this.rad(p2.latitude)) * Math.sin(dLong/2) * Math.sin(dLong/2)
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    var d = R * c

    return Math.round(d)
  }
}


var map = null;
var markers = [];
var infowindow = new google.maps.InfoWindow();
var coordenates;
var insertValues;
var loading;
var center = new google.maps.LatLng(41.641184, -0.894032);

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
		if(cat == "bus" || cat == "bizi"){
			var onclick = "showDetail("+id+", '"+ cat +"')";
			content += ' <a href="#detail" data-icon="info" onclick="'+onclick+'">Ver</a>';
		}
		if(cat == "tram"){
			content += ' <a href="#complaint-page" data-icon="info">Ver</a>';
		}
		infowindow.setContent(content);
		infowindow.open(map, marker);
	});
	markers.push(marker);
}
$('.loading').live('pageshow',function(event, ui){
	if(loading){
		$.mobile.loading('show', {
			text: 'Cargando datos...',
			textVisible: true
		});
	}
});
$('#map-page').live('pageshow',function(event, ui){
	google.maps.event.trigger(map, "resize");
});
function showMap(cat) {
	loading = true;
	removeMarkers();
	$.getJSON('http://api.dndzgz.com/services/'+ cat +'?callback=?', function(data) {
			locations = data.locations
			var n = locations.length;
			for(i=0; i<n; i++) {
				var place = locations[i];
				var lat = place['lat'];
				var lon = place['lon'];
				var title = place['title'];
				var subtitle = place['subtitle'];
				var id = place['id'];
				addMarker(lat, lon, title, subtitle, cat, id);
			}
			$.mobile.loading('hide');
			loading = false;
	});
}

function showDetail(id, cat) {
	loading = true;
	$("#detail-list").html("");
	$.ajax({ url: '/point?service='+cat+'&id='+id,
		dataType: 'json',
		success: function(data) {
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
			$.mobile.loading('hide');
			loading = false;
		},
		error: function() {
			alert("Error en la conexión");
		}
	});
}
function changeMapName(name){
	$('.service-type').text(name);
}
function geolocalize(first){
	if(navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
			var location = new google.maps.LatLng(
				position.coords.latitude,
				position.coords.longitude);
			coordenates = position.coords;
			var distance = Geolocation.distance(position.coords, {'latitude':center.lat(), 'longitude': center.lng()});
			if(distance > 15){
				alert('Ups! Estás muy lejos de Zaragoza')
				location = center;
			}
			if(first){
				var marker = new google.maps.Marker({
					position: location,
					map: map,
					icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
				});
			}
			map.setCenter(location);
		});
	}
}
function initMap() {
	var zoom = 16;
	
	var myOptions = {
		zoom: zoom,
		center: center,
		zoomControl: true,
		disableDefaultUI: true,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};
	map = new google.maps.Map(document.getElementById("map-container"), myOptions);
	geolocalize(true);
}
initMap();