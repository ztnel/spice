
import logging
import contextlib
import argparse
import numpy as np
from dataclasses import dataclass



# ----- duty modulation plugin -------
@dataclass
class Modulation:
    ...

@dataclass
class Linear(Modulation):
    start: float # x 
    stop: float # x
    rate: float # x / second

@dataclass
class Fixed(Modulation):
    value: float

# control topology
@dataclass
class PWMEngine:
    modulation: Modulation
    v_initial: float = 0.0 # V
    v_on: float = 5.0 # V
    v_off: float = 5.0 # V
    t_rise: float = 1e-8 # s
    t_fall: float = 1e-8 # s
    f_sw: float = 1.0 # Hz
    f_clk: float = 100e6 # Hz -> MCU speed dictates resultion of switching
    deadtime: float = 0.0
    duty: float = 0.5 # %
    phase_offset: float = 0.0 # ˚ 
    channels: int = 1

@dataclass
class PWLConfig:
    name: str
    duration: float # s
    pwm: PWMEngine

def pwl_run(pwl_config: PWLConfig):
    # init channels
    t_sw = 1 / pwl_config.pwm.f_sw
    t_on = t_sw * pwl_config.pwm.duty
    t_off = t_sw * (1 - pwl_config.pwm.duty)
    t_on_a = t_on - pwl_config.pwm.t_fall
    t_off_a = t_off - pwl_config.pwm.t_rise
    wave_segments = [t_on_a, pwl_config.pwm.t_fall, t_off_a, pwl_config.pwm.t_rise]
    _logger.info("Wave Segments: %s", wave_segments)
    timesteps = int(pwl_config.duration / t_sw)
    for channel in range(pwl_config.pwm.channels):
        pwl_out = np.array(np.zeros(shape=[timesteps, 2]), dtype=np.float32)
        pwl_out[0][0] = 0.0
        pwl_out[0][1] = pwl_config.pwm.v_initial
        cumulative = 0
        _logger.info("Timesteps: %s", timesteps)
        for i in range(1, timesteps, 4):
            # build waveform segments
            for j, segment in enumerate(wave_segments):
                if j == 0:
                    v = pwl_config.pwm.v_on
                elif j == 1:
                    v = pwl_config.pwm.v_off
                elif j == 2:
                    v = pwl_config.pwm.v_off
                else:
                    v = pwl_config.pwm.v_on
                # accumulate time count
                cumulative += segment 
                if i+j > timesteps -1:
                    break
                # populate entry
                pwl_out[i+j][0] = round(cumulative, 9)
                pwl_out[i+j][1] = round(v, 2)
                _logger.info(f"{pwl_out[i+j][0]},{pwl_out[i+j][1]}")
        # write to channels
        np.savetxt(f'{pwl_config.name}_ch{channel}.pwl', pwl_out, delimiter=",")

# 1. control type -> interleaved
# 2. control points -> contingent on 1.
# 3. V on V off
# 4. period
# 5. ramp rate duty start duty end
# 6. duty cycle (fixed)
# 7. deadtime? depends on control mode
# 8. filename(s)

# UC1: 2 channels, fixed duty modulation @ 50%, Von 5V Voff 0V Vstart 5V, switching frequency 100kHz
# UC2: 2 channels, linear duty modulation 1% -> 90% @ 1% / 1ms , Von 5V Voff 0V Vstart 5V, switching frequency 10kHz

if __name__ == '__main__':
    _logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    argparse.ArgumentParser(__name__.split('.py')[0])
    config = PWLConfig(
        name="test",
        duration=1.0,
        pwm=PWMEngine(
            modulation=Fixed(
                value=0.5
            ),
            v_initial=0,
            v_on=5,
            v_off=0,
            f_sw=1e5,
            f_clk=1e6
        )
    )
    pwl_run(config)

