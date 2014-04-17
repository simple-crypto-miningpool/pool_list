$(document).ready(function() {
    if (window.networkData != undefined) {
        // graph for donut chart
        nv.addGraph(function() {
          var chart = nv.models.pieChart()
              .margin({right: 0, left: 0})
              .x(function(d) { return d.label })
              .y(function(d) { return d.value })
              .showLabels(true)     //Display pie labels
              .labelThreshold(.05)  //Configure the minimum slice size for labels to show up
              .labelType("percent") //Configure what type of data to show in the label. Can be "key", "value" or "percent"
              .donut(true)          //Turn on Donut mode. Makes pie chart look tasty!
              .donutRatio(0.35)     //Configure how big you want the donut hole size to be.
              ;

            d3.select("#chart2 svg")
                .datum(networkData())
                .transition().duration(350)
                .call(chart);

            nv.utils.windowResize(chart.update);


          return chart;
        });        
    }

    // graph for pool hashrate

    nv.addGraph(function() {
    var chart = nv.models.stackedAreaChart()
                  .x(function(d) { return d[0] })   //We can modify the data accessor functions...
                  .y(function(d) { return d[1] })   //...in case your data is formatted differently.
                  .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
                  .transitionDuration(500)
                  .showControls(false)       //Allow user to choose 'Stacked', 'Stream', 'Expanded' mode.
                  .clipEdge(true);

    //Format x-axis labels with custom function.
    chart.xAxis
        .tickFormat(function(d) {
          return d3.time.format('%H:%M %p')(new Date(d))
    });

    chart.yAxis
        .axisLabel('MHash/sec')
        .axisLabelDistance(30)
        .tickFormat(d3.format(',.2f'));

    d3.select('#chart svg')
      .datum(hashrate_data())
      .call(chart);

    nv.utils.windowResize(chart.update);

    return chart;
    });

    // graph for pool workers
    nv.addGraph(function() {
    var chart = nv.models.stackedAreaChart()
                  .x(function(d) { return d[0] })   //We can modify the data accessor functions...
                  .y(function(d) { return d[1] })   //...in case your data is formatted differently.
                  .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
                  .transitionDuration(500)
                  .showControls(false)       //Allow user to choose 'Stacked', 'Stream', 'Expanded' mode.
                  .clipEdge(true);

    //Format x-axis labels with custom function.
    chart.xAxis
        .tickFormat(function(d) {
          return d3.time.format('%H:%M %p')(new Date(d))
    });

    chart.yAxis
        .axisLabel('Workers')
        .axisLabelDistance(30)
        .tickFormat(d3.format(',.2f'));

    d3.select('#chart3 svg')
      .datum(worker_data())
      .call(chart);

    nv.utils.windowResize(chart.update);

    return chart;
    });
});
