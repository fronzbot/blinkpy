=======================
Advanced Library Usage
=======================

Usage of this library was designed with the `Home Assistant <https://home-assistant.io>`__ project in mind.  With that said, this library is flexible to be used in other scripts where advanced usage not covered in the Quick Start guide may be required.  This usage guide will attempt to cover as many use cases as possible.

Throttling
--------------
In general, attempting too many requests to the Blink servers will result in your account being throttled.  Where possible, adding a delay between calls is ideal.  For use cases where this is not an acceptable solution, the ``blinkpy.helpers.util`` module contains a ``Throttle`` class that can be used as a decorator for calls.  There are many examples of usage within the ``blinkpy.api`` module.  A simple example of usage is covered below, where the decorated method is prevented from executing again until 10s has passed.  Note that if the method call is throttled by the decorator, the method will return `None`.

.. code:: python
   
   from blinkpy.helpers.util import Throttle

   @Throttle(seconds=10)
   def my_method(*args):
       """Some method to be throttled."""
       return True

Custom Sessions
-----------------
By default, the ``blink.auth.Auth`` class creates its own websession via its ``create_session`` method.  This is done when the class is initialized and is accessible via the ``Auth.session`` property. To override with a custom websession, the following code can accomplish that:

.. code:: python

    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth

    blink = Blink()
    blink.auth = Auth()
    blink.auth.session = YourCustomSession


Custom Retry Logic
--------------------
The built-in auth session via the ``create_session`` method allows for customizable retry intervals and conditions. These parameters are:

- retries
- backoff
- retry_list

``retries`` is the total number of retry attempts that each http request can do before timing out.  ``backoff`` is a parameter that allows for non-linear retry times such that the time between retries is backoff*(2^(retries) - 1).  ``retry_list`` is simply a list of status codes to force a retry.  By default ``retries=3``, ``backoff=1``, and ``retry_list=[429, 500, 502, 503, 504]``. To override them, you need to add you overrides to a dictionary and use that to create a new session with the ``opts`` variable in the ``create_session`` method. The following example can serve as a guide where only the number of retries and backoff factor are overridden:

.. code:: python

    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth

    blink = Blink()
    blink.auth = Auth()

    opts = {"retries": 10, "backoff": 2}
    blink.auth.session = blink.auth.create_session(opts=opts)


Custom HTTP requests
---------------------
In addition to custom sessions, custom blink server requests can be performed.  This give you the ability to bypass the built-in ``Auth.query`` method.  It also allows flexibility by giving you the option to pass your own url, rather than be limited to what is currently implemented in the ``blinkpy.api`` module.

**Send custom url**
This prepares a standard "GET" request.

.. code:: python

    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth

    blink = Blink()
    blink.auth = Auth()
    url = some_api_endpoint_string
    request = blink.auth.prepare_request(url, blink.auth.header, None, "get")
    response = blink.auth.session.send(request)

**Overload query method**
Another option is to create your own ``Auth`` class with a custom ``query`` method to avoid the built-in response checking. This allows you to use the built in ``blinkpy.api`` endpoints, but also gives you flexibility to send your own urls.

.. code:: python
    
    from blinkpy.blinkpy import Blink
    from blinkpy.auth import Auth
    from blinkpy import api

    class CustomAuth(Auth):
        def query(
            self,
            url=None,
            data=None,
            headers=self.header,
            reqtype="get",
            stream=False,
            json_resp=True,
            **kwargs
        ):
            req = self.prepare_request(url, headers, data, reqtype)
            return self.session.send(req, stream=stream)

    blink = blink.Blink()
    blink.auth = CustomAuth()

    # Send custom GET query
    response = blink.auth.query(url=some_custom_url)

    # Call built-in networks api endpoint
    response = api.request_networks(blink)
