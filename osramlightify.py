"""
homeassistant.components.light.osramlightify
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Osram Lightify platform that implements lights. Largely built off the demo example.
Uses: https://github.com/mikma/python-lightify for the Osram light interface.

Todo:
Need to add support for Non RGBW lights.
Need to add polling support (If lights are switched on from Android App etc).

"""

import logging
import lightify

from homeassistant.const import CONF_HOST
from homeassistant.components.light import (
    Light,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR
)
from homeassistant.util.color import color_RGB_to_xy

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """ Find and return lights. """
    host = config.get(CONF_HOST, None)
    conn = lightify.Lightify(host)
    conn.update_all_light_status()

    lights = []

    _LOGGER.debug("Listing Light Info")
    for (addr, light) in conn.lights().items():
        _LOGGER.debug("Address: %s" % addr)
        _LOGGER.debug("Light: %s" % light)
        _LOGGER.debug("Light Name: %s " % light.name())
        _LOGGER.debug("Light State: %s " % light.on())
        _LOGGER.debug("Light Lum: %s " % light.lum())
        _LOGGER.debug("Light Temp: %s " % light.temp())
        _LOGGER.debug("Light RGB: %s %s %s" % light.rgb())

        name = light.name()
        state = light.on()

        # Needs handling in here for NON-RGBW Lights, I've only got RGBW Lights to test with
        rgb_color = light.rgb()

        brightness = (light.lum() * 2.55)
        lights.append(OsramLightifyLight(addr, light, name, state, rgb_color, brightness))

    _LOGGER.info("Adding Lights: %s " % lights)
    add_devices_callback(lights)


class OsramLightifyLight(Light):
    """ Defines an Osram Lightify Light """
    def __init__(self, addr, light, name, state, rgb_color, brightness, xy=None):
        self._light = light
        self._addr = addr
        self._name = name
        self._state = state
        self._rgb_color = rgb_color
        r = self._rgb_color[0]
        g = self._rgb_color[1]
        b = self._rgb_color[2]
        self._xy = color_RGB_to_xy(r, g, b)
        self._brightness = brightness

    @property
    def should_poll(self):
        """ No polling needed for a demo light. """
        return False

    @property
    def name(self):
        """ Returns the name of the device if any. """
        self._name = self._light.name()
        return self._name

    @property
    def color_xy(self):
        """ XY color value. """
        self._rgb_color = self._light.rgb()
        r = self._rgb_color[0]
        g = self._rgb_color[1]
        b = self._rgb_color[2]
        self._xy = color_RGB_to_xy(r, g, b)
        return self._xy

    @property
    def rgb_color(self):
        """ Last RGB color value set. """
        return self._rgb_color

    @property
    def brightness(self):
        """ Brightness of this light between 0..255. """
        self._brightness = (self._light.lum() * 2.55)
        return self._brightness

    @property
    def is_on(self):
        """ Update Status to True if device is on. """
        self._state = self._light.on()
        _LOGGER.debug("is_on light state for light: %s is: %s " % (self._name, self._state))
        return self._state

    def turn_on(self, **kwargs):
        """ Turn the device on. """
        _LOGGER.info("turn_on Attempting to turn on light: %s " % self._name)
        self._light.set_onoff(1)
        self._state = self._light.on()
        _LOGGER.debug("turn_on Light state for light: %s is: %s " % (self._name, self._state))

        if ATTR_RGB_COLOR in kwargs:
            self._rgb_color = kwargs[ATTR_RGB_COLOR]
            r = self._rgb_color[0]
            g = self._rgb_color[1]
            b = self._rgb_color[2]
            self._rgb_color = self._light.set_rgb(r, g, b, 0)
            _LOGGER.debug("turn_on Light set_rgb for light: %s is: %s %s %s " % (self._name, r, g, b))

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            self._brightness = self._light.set_luminance(int(self._brightness / 2.55), 0)
            _LOGGER.debug("turn_on Light set_luminance for light: %s is: %s " % (self._name, self._brightness))
        self.update_ha_state()

    def turn_off(self, **kwargs):
        """ Turn the device off. """
        _LOGGER.info("turn_off Attempting to turn off light: %s " % self._name)
        self._light.set_onoff(0)
        self._state = self._light.on()
        _LOGGER.debug("turn_off Light state for light: %s is: %s " % (self._name, self._state))
        self.update_ha_state()
