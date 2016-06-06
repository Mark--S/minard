function flattenArray(arr) {
    return [].concat.apply([],arr);
}
function display_crate_view(key,crates_data,sizeinfo,node)
{
    var d = crates_data.map(function(crate,i) {
    if(crate) {
            MBs =  crate.map(function(mb,i) {
                if(mb) {
                    return mb[key];
                }
                else {
                   return Array.apply(null,Array(32)).map(function(x,i){return null;})
                }
            });
            return  flattenArray(MBs)
        }
        else {
            return Array.apply(null,Array(512)).map(function(x,i){return null;})
        }
    });
    d = flattenArray(d)

    var coloringFunc = function(data) {
        return function(k,i) {
        var v = data[k];
        if (v === null || typeof v === 'undefined')
            return 'background-color:#e0e0e0';
        else if (v===0) {
            return 'background-color:grey';
        }
        else
            return 'background-color:green';
    };}
    var crate = crate_view()
        .caption(true)
        .height(height)
        .width(width)
        .coloringFunction(coloringFunc);
        var g = node.append('div')
                .attr('id','crate')
                .attr('width',width)
                .attr('height',height)
                .attr('class',"col-md-10 col-md-offset-1");
        g.datum(d).call(crate);
}
function display_detector_control(detector_control_info) {
    var det_cont = d3.select("#detector_control");
    var bounds = det_cont.node().parentElement.parentElement.clientWidth
    var height = 100;
    var width = bounds;
    var step_size = width/15;
    radius = step_size/4.0;
    var xpos_func = function(d,i) { return step_size+i*step_size; }
    var ypos_func = function(d,i) { return height/2.0; }
    var svg = det_cont.append("svg")
        .attr("width",width)
        .attr("height",height)
        .attr("viewBox","0 0 "+width.toString()+" "+height.toString())
        .attr("class","rack_mask");
    var arr = [];
    arr.push(["T",detector_control_info["timing_rack"]]);
    for(var i=1;i<12;i++) {
        arr.push([i.toString(),detector_control_info["rack"+i.toString()]]);
    }
    svg.selectAll('circle')
        .data(arr)
        .enter()
        .append('circle')
        .attr("cx",xpos_func)
        .attr("cy",ypos_func)
        .attr("r",radius)
        .attr("fill",function(d) { return d[1]==1 ? 'green' : 'red'; })
        .attr("class",function(d) { return d[1]==1 ? 'on' : 'off'; });
    svg.selectAll('text')
        .data(arr)
        .enter()
        .append('text')
        .text(function(d){return d[0];})
        .attr("text-anchor","middle")
        .attr("font-size","16px")
        .attr("fill","white")
        .attr("x",xpos_func)
        .attr("y",function(d,i) { return ypos_func(d,i)+5;});
}
function display_triggers(wordlist) {
    var mtc = d3.select('#mtc');
    mtc.append("h3").text("Enabled Triggers");
    var trig_list = d3.select('#mtc').append('ul');
    trig_list.selectAll('li')
             .data(wordlist)
             .enter()
             .append('li')
             .text(function(d){ return d;});
};
function display_ped_delay(delay) {
    var mtc = d3.select('#mtc')
    mtc.append("h3").text("Pedestal Delay = "+ delay.toString());

};
function display_lockout_width(lockout) {
    var mtc = d3.select('#mtc')
    mtc.append("h3").text("Lockout Width = "+ lockout.toString());
};
function display_control_reg(wordlist) {
    var mtc = d3.select('#mtc')
    mtc.append('h3').text("Control Register Values");
    var list = mtc.append('ul');
    list.selectAll('li')
             .data(wordlist)
             .enter()
             .append('li')
             .text(function(d){ return d;});
};
function display_crates(title,crates) {
    var mtc = d3.select('#mtc');
    mtc.append('h3').text(title);
    var crate_list = mtc.append('ul');
    crate_list.selectAll('li')
        .data(crates)
        .enter()
        .append('li')
        .text(function(d) { return d;});
};
function display_prescale(prescale) {
    var mtc = d3.select('#mtc');
    mtc.append('h3').text('Prescale = '+prescale.toString());
};
function display_caen(caen_info) {
    var caen = d3.select("#CAEN");
    caen.append('h4').text("Acquisition Mode = "+caen_info.acquisition_mode);
}
function display_crate_mask(mask,dom_node,title,size_info) {
    var width = size_info.width;
    var height =size_info.height;
    dv = dom_node.append("div");
    dv.append("h4").text(title).attr("float","left");
    var svg = dv.append("svg")
        .attr("width",width)
        .attr("height",height)
        .attr("viewBox","0 0 "+width.toString()+" "+height.toString())
        .attr("class","crate_mask");
    var title_percent = 0.10;
    var title_width = title_percent*width;
    width=(1- title_percent)*width;
    var step_size = width/21;
    var xpos_func = function(d,i) { return title_width+i*step_size; }
    var ypos_func = function(d,i) { return height/2.0; }
    svg.selectAll("circle")
        .data(mask)
        .enter()
        .append("circle")
        .attr("cx",xpos_func)
        .attr("cy",ypos_func)
        .attr("r",height/2.0)
        .attr("class",function(d) { return d ? 'on' : 'off'; })
    svg.selectAll('text')
        .data(mask)
        .enter()
        .append('text')
        .text(function(d,i){return i.toString();})
        .attr("text-anchor","middle")
        .attr("font-size","10px")
        .attr("fill","white")
        .attr("x",xpos_func)
        .attr("y",function(d,i) { return ypos_func(d,i)+3;});
};
function display_run_type(run_type,time_stamp) {
    var run_type_translation = {
    0:"Maintenance",
    1:"Transition",
    2:"Physics",
    3:"Deployed Source",
    4:"External Source",
    5:"ECA",
    6:"Diagnostic",
    7:"Experimental",
    };
    var calib_translation = {
    11:"TELLIE",
    12:"SMELLIE",
    13:"AMELLIE",
    14:"PCA",
    15:"ECA Pedestal",
    16:"ECA Time Slope"
    };
    var detector_state_translation = {
    21:"DCR Activity",
    22:"Compensation Coils Off",
    23:"PMTS Off",
    24:"Bubblers On",
    25:"Recirculation",
    26:"SL Assay",
    27:"Unusual Activity"
    };
    var flag = false;
    var translator = function(low_bit,high_bit,trans_map){
        ret = []
        for(i=low_bit;i<=high_bit;i++)
        {
            if(run_type & (1<<i)) {
                if(i-low_bit >= Object.keys(trans_map).length) {
                   ret.push("SPARE (???)");
                }
                else {
                    ret.push(trans_map[i]);
                }
            }
        }
        return ret;
    };
    var run_desc = translator(0,10,run_type_translation);
    var calib_desc = translator(11,20,calib_translation);
    var det_state_desc = translator(21,31,detector_state_translation);
    if(run_desc.length == 0) {
        run_desc.push("None");
    }
    var title = document.getElementById("run_title");
    var appendToTitle = function(type,desc){
        var thisSubTitle = document.createElement('h2');
        thisSubTitle.appendChild(document.createTextNode(desc.toString()));
        title.appendChild(thisSubTitle);
    }
    appendToTitle('h2',run_desc);
    if(calib_desc.length > 0){
        appendToTitle('h3',calib_desc);
    }
    if(det_state_desc.length > 0){
        appendToTitle('h3',det_state_desc);
    }
    appendToTitle('p',time_stamp);
};
function display_mb(crateNum,cardNum,mb_data) {
    var id ="#Crate"+crateNum+"MB"+cardNum
    var thisCard = d3.select(id)
    var size_info = {}
    size_info['width'] = 200;
    size_info['height'] = 100;
    var width = size_info.width;
    var height =size_info.height;
    dv = thisCard.append("div");
    dv.attr("class","LOOKHERE");
    var svg = dv.append("svg")
        .attr("width",width)
        .attr("height",height)
        .attr("viewBox","0 0 "+width.toString()+" "+height.toString())
        .attr("class","crate_mask");
    var step_size = 10;
    var xpos_func = function(d,i) { return step_size+cardNum*step_size; }
    var ypos_func = function(d,i) { return step_size+i*step_size; }
    svg.selectAll("circle")
        .data(mb_data['n100_triggers'])
        .enter()
        .append("circle")
        .attr("cx",xpos_func)
        .attr("cy",ypos_func)
        .attr("r",5)
        .attr("fill","red");
};
function display_crate_config(svg,crate_data) {
    for (var i=0;i<16;i++) {
        if(crate_data[i]) {
            display_mb(1,i,crate_data[i]);
        }
    }
};
function crate() {
    var width = 780;
    var height = 80;

    function my(){

    }
    my.width = function(value) {
        if(!arguments.length) {
            return width;
        }
        width = value;
        return my;
    }
    my.height = function(value) {
        if(!arguments.length) {
            return height;
        }
        height = value;
        return my;
    }

    return my;
}
function display_all_crates(crates_data,svg) {
    for(var i=0;i<20;i++) {
        if (crates_data[i]) {
            crate = d3.select("#crate"+i)
            var thisSvg = crate.append("svg")
                .attr("width",width)
                .attr("height",height)
                .attr("viewBox","0 0 "+width.toString()+" "+height.toString())
            display_crate_config(svg, crates_data[i]);
        }
    }
};
