import types
import unittest
from unittest.mock import Mock, patch
from goals.sensors import Sensors
from goals.contracts import INPUT_SIZES, ACK_INPUT


class SensorTests(unittest.TestCase):
    def test_camera_six_sensor_channels_and_zero_collision(self):
        raw = {'proximity_left':250, 'proximity_right':500,
               'proximity_left_side':750, 'proximity_right_side':1000,
               'light_left':0.25, 'light_right':0.75}
        devices = {name:Mock() for name in ('camera', *raw)}
        for name, value in raw.items(): devices[name].getValue.return_value = value
        camera = devices['camera']
        camera.getImage.return_value = b'frame'
        camera.getWidth.return_value = camera.getHeight.return_value = 64
        robot = Mock()
        robot.getDevice.side_effect = devices.__getitem__
        rgb = types.SimpleNamespace(imageGetRed=lambda *args:255,
                                    imageGetGreen=lambda *args:0, imageGetBlue=lambda *args:0)
        with patch.dict('sys.modules', {'controller':types.SimpleNamespace(Camera=rgb)}):
            frame, observations = Sensors(robot,32).capture({'proximity_full_scale':1000})
        self.assertEqual(set(frame), set(INPUT_SIZES)-{ACK_INPUT})
        for name, values in frame.items(): self.assertEqual(len(values), INPUT_SIZES[name])
        for name, active in (('FRONT_LEFT',4),('FRONT_RIGHT',8),('SIDE_LEFT',12),
                             ('SIDE_RIGHT',16),('LIGHT_LEFT',4),('LIGHT_RIGHT',12)):
            self.assertEqual(frame[name], [1.0]*active+[0.0]*(16-active))
        self.assertEqual(frame['COLLISION'], [0])
        self.assertEqual(frame['CAMERA'], [1/3]*64)
        for name,value in raw.items(): self.assertEqual(observations[name],value)
        for device in devices.values(): device.enable.assert_called_once_with(32)

    def test_missing_device_fails_before_running(self):
        robot = Mock()
        robot.getDevice.return_value = None
        with self.assertRaisesRegex(RuntimeError,'missing a required sensor'):
            Sensors(robot,32)
