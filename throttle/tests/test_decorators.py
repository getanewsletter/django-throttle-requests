# -*- coding: utf-8 -*-
from __future__ import with_statement  # Python 2.5
from django.test import TestCase
from django.http import HttpResponse

from throttle.decorators import throttle
from throttle.exceptions import ThrottleZoneNotDefined


def callback_function(request):
    callback_function.is_called = True
    return HttpResponse('OK')
callback_function.is_called = False


@throttle
def _test_view(request):
    return HttpResponse('OK')


@throttle(zone='test3', callback=callback_function)
def _test_view_with_callback(request):
    return HttpResponse('OK')


@throttle
@throttle(zone='test2')
def _test_multiple_throttles(request):
    return HttpResponse("Photos")


def _test_view_with_parameters(request, id):
    return HttpResponse(str(id))


def _test_view_not_throttled(request):
    return HttpResponse("Go ahead and DoS me!")


try:
    from django.conf.urls import patterns, url
except ImportError: # django < 1.4
    from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(r'^test/$', _test_view),
    url(r'^test/(\d+)/$', _test_view_with_parameters),
    url(r'^test-with-callback/$', _test_view_with_callback),
)


class test_throttle(TestCase):
    urls = __module__

    def test_view_marked(self):
        '''
        @throttle adds an attribute 'throttle_zone' to views it decorates.
        '''
        self.assertFalse(hasattr(_test_view_not_throttled, 'throttle_zone'))
        self.assertTrue(hasattr(_test_view, 'throttle_zone'))
        self.assertEqual(_test_view.throttle_zone.vary.__class__.__name__, 'RemoteIP')

    def test_with_invalid_zone(self):
        '''
        @throttle throws an exception if an invalid zone is specified
        '''
        with self.assertRaises(ThrottleZoneNotDefined):
            _throttled_view = throttle(_test_view_not_throttled, zone='oœuf')
            _throttled_view(object)

    def test_marked_view_returns(self):
        response = self.client.get('/test/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OK")

    def test_marked_view_with_params(self):
        response = self.client.get('/test/99/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "99")

    def test_returns_403_if_exceeded(self):
        for iteration in range(10):
            _test_view.throttle_zone.get_timestamp = lambda: iteration

            # THROTTLE_ZONE 'default' allows 5 requests/second
            for i in range(5):
                response = self.client.get('/test/', REMOTE_ADDR='test_returns_403_if_exceeded')
                self.assertEqual(response.status_code, 200, '%ith iteration' % (iteration))

            # Now the next request should fail
            response = self.client.get('/test/', REMOTE_ADDR='test_returns_403_if_exceeded')
            self.assertEqual(response.status_code, 403)

    def test_returns_403_if_exceeded(self):
        for iteration in range(10):
            _test_view.throttle_zone.get_timestamp = lambda: iteration

            # THROTTLE_ZONE 'default' allows 5 requests/second
            for i in range(5):
                response = self.client.get('/test/', REMOTE_ADDR='test_returns_403_if_exceeded')
                self.assertEqual(response.status_code, 200, '%ith iteration' % (iteration))

            # Now the next request should fail
            response = self.client.get('/test/', REMOTE_ADDR='test_returns_403_if_exceeded')
            self.assertEqual(response.status_code, 403)

    def test_calls_callback_if_exceeded(self):
        # THROTTLE_ZONE 'default' allows 5 requests/second
        for i in range(5):
            response = self.client.get('/test-with-callback/', REMOTE_ADDR='test_returns_403_if_exceeded')
            self.assertEqual(response.status_code, 200)

        # Now the next request should fail
        self.assertFalse(callback_function.is_called)
        response = self.client.get('/test-with-callback/', REMOTE_ADDR='test_returns_403_if_exceeded')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(callback_function.is_called)
