
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
    t_rise: float = 0.0 # s
    t_fall: float = 0.0 # s
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

def cycle_update(cumulative: float, high_cycle: bool) -> float:
    order = ['rise', 'on', 'fall', 'off']
    cumulative += t_rise
    pwl_out[idx][0] = round(cumulative, 9)
    pwl_out[idx][1] = round(v_off if alt else v_on, 2)
    cumulative += t_on
    pwl_out[idx+1][0] = round(cumulative, 9)
    pwl_out[idx+1][1] = round(v_on if alt else v_off, 2)
    cumulative += t_fall
    pwl_out[idx+2][0] = round(cumulative, 9)
    pwl_out[idx+2][1] = round(v_on if alt else v_off, 2)
    cumulative += t_off
    pwl_out[idx+3][0] = round(cumulative, 9)
    pwl_out[idx+3][1] = round(v_on if alt else v_off, 2)

def pwl_run(pwl_config: PWLConfig):
    # init channels
    t_sw = 1 / pwl_config.pwm.f_sw
    t_on = t_sw * pwl_config.pwm.duty
    t_off = t_sw * (1 - pwl_config.pwm.duty)
    timesteps = int(pwl_config.duration / t_sw)
    for channel in range(pwl_config.pwm.channels):
        pwl_out = np.array(np.zeros(shape=[timesteps, 2]), dtype=np.float32)
        pwl_out[0][0] = 0.0
        pwl_out[0][1] = pwl_config.pwm.v_initial
        cumulative = 0
        _logger.info("Timesteps: %s", timesteps)
        t_rise = pwl_config.pwm.t_rise if parity else pwl_config.pwm.t_fall
        t_fall = pwl_config.pwm.t_fall if parity else pwl_config.pwm.t_rise
        v_on = pwl_config.pwm.v_on if parity else pwl_config.pwm.v_off
        t_on = t_on if parity else t_off
        v_off = pwl_config.pwm.v_off if parity else pwl_config.pwm.v_on
        t_off = t_off if parity else t_on
        for idx in range(1, timesteps, 4):
            is_high = idx % 2 if pwl_config.pwm.v_initial == pwl_config.pwm.v_off else not idx % 2
            cumulative = update_high_cycle() if is_high else update_low_cycle()

            _logger.info("cumulative: %s", cumulative)
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
            v_initial=5,
            v_on=5,
            v_off=0,
            f_sw=1e5,
            f_clk=1e6
        )
    )
    pwl_run(config)

