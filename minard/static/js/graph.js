function isNumber(x)
{
    return !isNaN(x) && (x != null);
}

function format_data(values, start, stop, step)
{
    var data = new Array();
    for (var i=0; i < values.length; i++)
    {
        var date = moment(start);
        date.add(step*i, 'seconds');
        data.push({'date': date.toDate(), 'value': values[i]});
    }
    return data;
}

function add_graph(name, start, stop, step)
{
    d3.json($SCRIPT_ROOT + '/metric' + 
            '?expr=' + name +
            '&start=' + start.toISOString() +
            '&stop=' + stop.toISOString() +
            '&now=' + new Date().toISOString() +
            '&step=' + Math.floor(step),
            function(data) {
                if (!data) console.log('unable to load data');

                var values = data.values;
                var chart_data = format_data(values,start,stop,step);
                var dates = chart_data.map(function(d) { return d['date']; });
                var scale = tzscale().domain(dates).zone('America/Toronto');

                var valid = values.filter(isNumber);

                MG.data_graphic({
                    title: name,
                    chart_type: valid.length ? 'line' : 'missing-data',
                    area: false,
                    data: chart_data,
                    interpolate: 'linear',
                    width: $('#main').width(),
                    height: 250,
                    show_secondary_x_label: false,
                    //xax_tick: 0,
		    time_scale: scale,
                    xax_format: scale.tickFormat(data.length),
                    y_extended_ticks: true,
                    target: "#main",
                    x_accessor:'date',
                    y_accessor:'value',
                });

                var width = $('#hist').width();

                MG.data_graphic({
                    data: valid,
                    chart_type: valid.length ? 'histogram' : 'missing-data',
                    width: width,
                    height: width/1.6,
                    bins: 50,
                    bar_margin: 1,
                    target: '#hist',
                });

                // log
                MG.data_graphic({
                    data: valid,
                    y_scale_type: 'log',
                    chart_type: valid.length ? 'histogram' : 'missing-data',
                    width: width,
                    height: width/1.6,
                    bins: 50,
                    bar_margin: 1,
                    target: '#hist-log',
                });
            });
}
