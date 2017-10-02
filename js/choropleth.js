var option = 0;



// Need to pad County codes to have 5 values so they can be read properly
// pad(d.id, 5)
// 1001  -->  01001
function pad(n, width, z) {
	z = z || '0';
	n = n + '';
	return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}



function buildMap(n) {
	var filename = "obesity_prevalence.csv";
	var isTSV = false;
	var xDomain = [5, 45];
	var colorDomain = [10, 15, 20, 25, 30, 35, 40];
	var keyText = "Obesity Prevalence rate";

	if (n == 1) {
		console.log("unemployment");
		var filename = "unemployment_data.tsv";
		var isTSV = true;
		var xDomain = [1, 10];
		var colorDomain = d3.range(2, 10);
		var keyText = "Unemployment rate";
	} else if (n == 2) {
		console.log("population");
		var filename = "population.csv";
		var isTSV = false;
		var xDomain = [100, 1000000];
		var colorDomain = [0, 50000, 100000, 200000, 500000, 1000000];
		var keyText = "population rate";
	} 

	var svg = d3.select("svg"),
		width = +svg.attr("width"),
		height = +svg.attr("height");

	var unemployment = d3.map();


	var path = d3.geoPath();

	var x = d3.scaleLinear()
			.domain(xDomain) // sets the pixel length of the key
			.rangeRound([600, 860]);

	// sets the color bar length
	var color = d3.scaleThreshold()
			// .domain(d3.range(2, 10)) // from 2% to 9% < // sets length to 20
			.domain(colorDomain) 
			.range(d3.schemeBlues[colorDomain.length]);

	// sets the location of the key
	// increasing the translate y-value moves it down the screen
	var g = svg.append("g")
			.attr("class", "key")
			.attr("transform", "translate(0,40)");


	g.selectAll("rect")
		.data(color.range().map(function(d) {
				d = color.invertExtent(d);
				if (d[0] == null) d[0] = x.domain()[0];
				if (d[1] == null) d[1] = x.domain()[1];
				return d;
			}))
		.enter().append("rect")
			.attr("height", 8)
			.attr("x", function(d) { return x(d[0]); })
			.attr("width", function(d) { return x(d[1]) - x(d[0]); })
			.attr("fill", function(d) { return color(d[0]); });

	g.append("text")
			.attr("class", "caption")
			.attr("x", x.range()[0])
			.attr("y", -6)
			.attr("fill", "#000")
			.attr("text-anchor", "start")
			.attr("font-weight", "bold")
			.text(keyText);


	g.call(d3.axisBottom(x)
			.tickSize(13)
			.tickFormat(function(x, i) { return i ? x : x + "%"; })
			.tickValues(color.domain()))
		.select(".domain")
			.remove();

	if (isTSV) {
		console.log(filename);

		d3.queue()
			.defer(d3.json, "https://d3js.org/us-10m.v1.json")
			.defer(d3.tsv, "data/" + filename, function(d) { 
				if (d.rate == "No Data") { d.rate = 0.0; }

				// pad the id number so that it is a 5-digit code
				unemployment.set(pad(d.id, 5), +d.rate); 
			})
			.await(ready);
	} else {
		d3.queue()
			.defer(d3.json, "https://d3js.org/us-10m.v1.json")
			.defer(d3.csv, "data/" + filename, function(d) { 
				if (d.rate == "No Data") { d.rate = 0.0; }

				// pad the id number so that it is a 5-digit code
				unemployment.set(pad(d.id, 5), +d.rate); 
			})
			.await(ready);		
	}

	// d3.queue()
	// 		.defer(d3.json, "https://d3js.org/us-10m.v1.json")
	// 		// .defer(d3.tsv, "data/unemployment_data.tsv", function(d) { 
	// 		//  // pad the id number so that it is a 5-digit code
	// 		//  unemployment.set(pad(d.id, 5), +d.rate); 
	// 		// })
	// 		.defer(d3.csv, "data/obesity_prevalence.csv", function(d) { 
	// 			if (d.rate == "No Data") { d.rate = 0.0; }

	// 			// pad the id number so that it is a 5-digit code
	// 			unemployment.set(pad(d.id, 5), +d.rate); 
	// 		})
	// 		.await(ready);

	function ready(error, us) {
		if (error) throw error;

		svg.append("g")
				.attr("class", "counties")
			.selectAll("path")
			.data(topojson.feature(us, us.objects.counties).features)
			.enter().append("path")
				.attr("fill", function(d) { return color(d.rate = unemployment.get(d.id)); })
				.attr("d", path)
			.append("title")
				.text(function(d) { return (d.rate) + "%"; });

		svg.append("path")
				.datum(topojson.mesh(us, us.objects.states, function(a, b) { return a !== b; }))
				.attr("class", "states")
				.attr("d", path);
	}
}






$(".obesity").click(function() {
	console.log("obesity");
	$(".usa").empty();
	buildMap(0);
});

$(".unemployment").click(function() {
	console.log("unemployment");
	$(".usa").empty();
	buildMap(1);
});

$(".population").click(function() {
	console.log("population");
	$(".usa").empty();
	buildMap(2);
});

$(document).ready(function() {
	buildMap(2);
});