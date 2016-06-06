QuickStart
==========

Hello World
-----------

The simplest thing we can do is add a new url to the web app which returns a
string. Edit the file `views.py` in the minard source directory and add the
following function::

    @app.route('/hello_world')
    def hello_world():
        return 'Hello World!'

That's it! Now, just reinstall the minard package and restart the server::

    $ cd $VIRTUAL_ENV/src
    $ pip uninstall minard
    $ pip install ./minard
    $ gunicorn -b 127.0.0.1:5000 minard:app

and navigate your browser to `http://localhost:5000/hello_world <http://localhost:5000/hello_world>`_. To learn more about how this example worked see the `Flask Quickstart <http://flask.pocoo.org/docs/quickstart/>`_

Creating a Template
-------------------

The next step is to create a template so that we can return a real HTML page from our `hello_world` function. Create a file that looks like this::

    {% extends "layout.html" %}
    {% block title %}Hello World{% endblock %}
    {% block head %}
        {{ super() }}
    {% endblock %}
    {% block body %}
        {{ super() }}
        <h1>Hello World!</h1>
    {% endblock %}

and save it as `hello_world.html` in the `minard/templates` directory.

Now edit `views.py` again and change the `hello_world` function to look like this::

    @app.route('/hello_world')
    def hello_world():
        return render_template('hello_world.html')

Now, reinstall minard, and restart the web server and navigate to `http://localhost:5000/hello_world <http://localhost:5000/hello_world>`_ again, and you should see `Hello World` displayed below the navigation bar.

Adding a Histogram
------------------

Our page is pretty boring, so let's add a histogram! Edit `hello_world.html` to look like this::

    {% extends "layout.html" %}
    {% block title %}Hello World{% endblock %}
    {% block head %}
        {{ super() }}
        <script src="{{ url_for('static', filename='js/d3.js') }}"></script>
        <script src="{{ url_for('static', filename='js/histogram.js') }}"></script>
    {% endblock %}
    {% block body %}
        {{ super() }}
        <div class="container">
            <h1>Hello World!</h1>
            <div id="hist" />
        </div>
        <script>
            var chart = histogram();

            setInterval(function() {
                $.getJSON($SCRIPT_ROOT + '/hello_world_hist', function(reply) {
                    d3.select('#hist').datum(reply.value).call(chart);
                });
            },1000);
        </script>
    {% endblock %}

Now we need to edit `views.py` again and add a function which will return the histogram data::

    import random

    @app.route('/hello_world_hist')
    def hello_world_hist():
        return jsonify(value=[random.gauss(0,1) for i in range(100)])

Reinstall minard, restart the web server and navigate to `http://localhost:5000/hello_world <http://localhost:5000/hello_world>`_, and you should see your beautiful histogram updating every second.

Monitoring CPU Usage
--------------------

For this example, we'll use the redis database to log the current CPU usage and
display it using a d3 plugin called `cubism <http://square.github.io/cubism/>`_.

Script
^^^^^^

First, we need to set up a script that will write to the redis database. We'll
monitor the cpu usage and memory in intervals of one second, and one minute. I
will use a design pattern found `here <http://flask.pocoo.org/snippets/71>`_,
where we use the unix timestamp to keep track of keys. For more details on how
redis works see the tutorial on creating a `twitter clone
<http://redis.io/topics/twitter-clone>`_.

.. literalinclude:: system_monitor
    :language: python

To use this script, you'll need to install the psutil python package::

$ pip install psutil

Template
^^^^^^^^

Now, we need to create a template to display the time series. Create a file in
the templates directory called `system_monitor.html`.

.. literalinclude:: system_monitor.html

View
^^^^

Finally, we need to add the following to views.py::

    @app.route('/system_monitor')
    def system_monitor():
        if not request.args.get('step'):
            return redirect(url_for('system_monitor',step=1,height=20,_external=True))
        step = request.args.get('step',1,type=int)
        height = request.args.get('height',40,type=int)
        return render_template('system_monitor.html',step=step,height=height)

    @app.route('/hello_world_metric')
    def hello_world_metric():
        args = request.args

        expr = args.get('expr',type=str)
        start = args.get('start',type=parseiso)
        stop = args.get('stop',type=parseiso)
        now_client = args.get('now',type=parseiso)
        # convert ms -> sec
        step = args.get('step',type=int)//1000

        now = int(time.time())

        # adjust for clock skew
        dt = now_client - now
        start -= dt
        stop -= dt

        if step > 60:
            t = 60
        else:
            t = 1

        p = redis.pipeline()
        for i in range(start,stop,step):
            p.get('stream/%i:%i:%s' % (t,i//t,expr))
        result = [float(x) if x else 0 for x in p.execute()]

        if t == 60:
            p = redis.pipeline()
            for i in range(start,stop,step):
                p.get('stream/60:%i:count' % (i//t))
            counts = [int(x) if x else 0 for x in p.execute()]
            result = [a/b for a, b in zip(result,counts)]

        return jsonify(values=result)

Now, run the script, reinstall minard, and restart the web server and you should
see the time series at `localhost:5000/system_monitor
<http://localhost:5000/system_monitor>`_.
