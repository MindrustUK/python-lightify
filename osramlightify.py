"""
Support for Osram Lightify.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.osramlightify/
"""
import logging
import socket
import random
from datetime import timedelta

import voluptuous as vol

from homeassistant import util
from homeassistant.const import CONF_HOST
from homeassistant.components.light import (
    Light, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_EFFECT, ATTR_RGB_COLOR,
    ATTR_TRANSITION, EFFECT_RANDOM, SUPPORT_BRIGHTNESS, SUPPORT_EFFECT,
    SUPPORT_COLOR_TEMP, SUPPORT_RGB_COLOR, SUPPORT_TRANSITION, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/tfriedel/python-lightify/archive/master.zip#lightify==0.0.4']

_LOGGER = logging.getLogger(__name__)

TEMP_MIN = 2000  # lightify minimum temperature
TEMP_MAX = 6500  # lightify maximum temperature
TEMP_MIN_HASS = 154  # home assistant minimum temperature
TEMP_MAX_HASS = 500  # home assistant maximum temperature
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(milliseconds=100)

SUPPORT_OSRAMLIGHTIFY = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP |
                         SUPPORT_EFFECT | SUPPORT_RGB_COLOR |
                         SUPPORT_TRANSITION)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Osram Lightify lights."""
    import lightify
    host = config.get(CONF_HOST)
    if host:
        try:
            bridge = lightify.Lightify(host)
        except socket.error as err:
            msg = 'Error connecting to bridge: {} due to: {}'.format(host,
                                                                     str(err))
            _LOGGER.exception(msg)
            return False
        setup_bridge(bridge, add_devices)
    else:
        _LOGGER.error('No host found in configuration')
        return False


def setup_bridge(bridge, add_devices_callback):
    """Setup the Lightify bridge."""
    lights = {}

    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update_lights():
        """Update the lights objects with latest info from bridge."""
        bridge.update_all_light_status()

        new_lights = []

        for (light_id, light) in bridge.lights().items():
            if light_id not in lights:
                osram_light = OsramLightifyLight(light_id, light,
                                                 update_lights)

                lights[light_id] = osram_light
                new_lights.append(osram_light)
            else:
                lights[light_id].light = light

        if new_lights:
            add_devices_callback(new_lights)

    update_lights()


class OsramLightifyLight(Light):
    """Representation of an Osram Lightify Light."""

    def __init__(self, light_id, light, update_lights):
        """Initialize the light."""
        self._light = light
        self._light_id = light_id
        self.update_lights = update_lights
        self._brightness = int(self._light.lum() * 2.55)

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._light.name()

    @property
    def rgb_color(self):
        """Last RGB color value set."""
        _LOGGER.debug("rgb_color light state for light: %s is: %s %s %s ",
                      self._light.name(), self._light.red(),
                      self._light.green(), self._light.blue())
        return self._light.rgb()

    @property
    def color_temp(self):
        """Return the color temperature."""
        o_temp = self._light.temp()
        temperature = int(TEMP_MIN_HASS + (TEMP_MAX_HASS - TEMP_MIN_HASS) *
                          (o_temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN))
        return temperature

    @property
    def brightness(self):
        """Brightness of this light between 0..255."""
        self._light.brightness = (self._light.lum() * 2.55)
        _LOGGER.debug("brightness for light %s is: %s",
                      self._light.name(), self._light.brightness)
        return self._light.brightness

    @property
    def is_on(self):
        """Update Status to True if device is on."""
        self.update_lights()
        _LOGGER.debug("is_on light state for light: %s is: %s",
                      self._light.name(), self._light.on())
        return self._light.on()

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OSRAMLIGHTIFY

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.debug("turn_on Attempting to turn on light: %s ",
                      self._light.name())

        self._light.set_onoff(1)
        self._state = self._light.on()

        if ATTR_TRANSITION in kwargs:
            transition = kwargs[ATTR_TRANSITION] * 10
            _LOGGER.debug("turn_on requested transition time for light: %s is: %s ",
                          self._light.name(), transition)
        else:
            transition = 0
            _LOGGER.debug("turn_on requested transition time for light: %s is: %s ",
                          self._light.name(), transition)

        if ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            _LOGGER.debug("turn_on requested ATTR_RGB_COLOR for light: %s is: %s %s %s ",
                          self._light.name, red, green, blue)
            self._light.set_rgb(red, green, blue, transition)

        if ATTR_COLOR_TEMP in kwargs:
            color_t = kwargs[ATTR_COLOR_TEMP]
            kelvin = int(((TEMP_MAX - TEMP_MIN) * (color_t - TEMP_MIN_HASS) / (TEMP_MAX_HASS - TEMP_MIN_HASS)) + TEMP_MIN)
            _LOGGER.debug("turn_on requested set_temperature for light: %s: %s ",
                          self._light.name, kelvin)
            self._light.set_temperature(kelvin, transition)

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on requested brightness for light: %s is: %s ",
                          self._light.name, self._brightness)
            self._brightness = self._light.set_luminance(int(self._brightness / 2.55), transition)

        if ATTR_EFFECT in kwargs:
            effect = kwargs.get(ATTR_EFFECT)
            if effect == EFFECT_RANDOM:
                self._light.set_rgb(random.randrange(0, 255),
                                    random.randrange(0, 255),
                                    random.randrange(0, 255),
                                    transition)
                _LOGGER.debug("turn_on requested random effect for light: %s with transition %s ",
                              self._light.name, transition)

        self.update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug("turn_off Attempting to turn off light: %s ",
                      self._light.name)
        if ATTR_TRANSITION in kwargs:
            transition = kwargs[ATTR_TRANSITION] * 10
            _LOGGER.debug("turn_off requested transition time for light: %s is: %s ",
                          self._light.name, transition)
            self._light.set_luminance(0, transition)
        else:
            transition = 0
            _LOGGER.debug("turn_off requested transition time for light: %s is: %s ",
                          self._light.name, transition)
            self._light.set_onoff(0)
            self._state = self._light.on()

        self.update_ha_state()

    def update(self):
        """Synchronize state with bridge."""
        self.update_lights(no_throttle=True)
