$(function(){
    // render table
    var source = $('#stats-template').html();
    var template = Handlebars.compile(source);
    $('#stats').append(template({stats:STATS_DATA}));

    // render graph
    (function bars_stacked(container) {
        var js = [], html = [], ticks = [], graph;

        $.each(STATS_DATA, function(i, v){
            ticks.push([i, v.name]);
            js.push([i, v.total.code]);
            html.push([i, v.html.code]);
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
