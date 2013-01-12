$(function(){
    // render table
    var source = $('#stats-template').html();
    var template = Handlebars.compile(source);
    $('#stats').append(template({stats:STATS_DATA}));

    // render graph
    (function bars_stacked(container) {
        var js = [], html = [], ticks = [], graph;

        var tick = 0;
        $.each(STATS_DATA, function(i, v){
            if (!v.routing){
                // do not show incomplete apps in graph
                // TODO: should check version also
                return true;
            }
            ticks.push([tick, v.name]);
            js.push([tick, v.total.code]);
            html.push([tick, v.html.code]);
            tick += 1;
        });

        graph = Flotr.draw(container,[
            { data : js, label : 'js' },
            { data : html, label : 'HTML' },
        ], {
            title: "LOC Graph",
            bars : {
                show : true,
                stacked : true,
                barWidth : 0.6,
                lineWidth : 1,
                shadowSize : 0
            },
            xaxis : {
                ticks: ticks
            },
            // yaxis : {max : 300 },
            grid : {
                verticalLines : false
            }
        });
    })(document.getElementById("graph"));
});
