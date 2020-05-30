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
