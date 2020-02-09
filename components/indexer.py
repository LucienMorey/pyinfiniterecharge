from magicbot import feedback
import ctre


class Indexer:
    indexer_motors: list

    def setup(self):
        for motor in self.indexer_motors:
            motor.setInverted(False)
            motor.setNeutralMode(ctre.NeutralMode.Brake)
            motor.configForwardLimitSwitchSource(
                ctre.LimitSwitchSource.FeedbackConnector,
                ctre.LimitSwitchNormal.NormallyOpen,
            )
        # Motor on the injector needs reversing
        self.indexer_motors[-1].setInverted(True)

        self.indexer_speed = 0.6
        self.injector_speed = 1.0

        # We have a delay because the distance between the second last
        # stage of the indexer and the injector is longer than others
        # and the injector motors are slower
        self.transfer_to_injector = False

    def on_enable(self) -> None:
        self.intaking = True

    def execute(self) -> None:
        if self.intaking:
            injector = self.indexer_motors[-1]
            feeder = self.indexer_motors[-2]
            if (
                not injector.isFwdLimitSwitchClosed()
                and feeder.isFwdLimitSwitchClosed()
            ):
                # Transferring
                self.transfer_to_injector = True
            if injector.isFwdLimitSwitchClosed():
                self.transfer_to_injector = False

            # Turn on all motors and let the limit switches stop it
            for motor in self.indexer_motors:
                motor.set(self.indexer_speed)
            self.indexer_motors[-1].set(self.injector_speed)

            # Override any limit switches where the next cell is vacant
            for first, second in zip(self.indexer_motors, self.indexer_motors[1:]):
                at_limit = second.isFwdLimitSwitchClosed()
                if second == feeder and self.transfer_to_injector:
                    at_limit = True  # Pretend the ball is still in the feeder
                if not at_limit:
                    first.overrideLimitSwitchesEnable(False)
                else:
                    first.overrideLimitSwitchesEnable(True)
        else:
            # Move balls through if we have them, but don't take in more
            ball_in_previous = False
            for motor in self.indexer_motors:
                if not motor.isFwdLimitSwitchClosed():
                    # We don't have a ball in this cell
                    # Test this first so the previous ball flag works
                    if not ball_in_previous:
                        motor.stopMotor()
                else:
                    ball_in_previous = True

    def enable_intaking(self) -> None:
        self.intaking = True

    def disable_intaking(self) -> None:
        self.intaking = False

    @feedback
    def balls_loaded(self) -> int:
        balls = sum(motor.isFwdLimitSwitchClosed() for motor in self.indexer_motors)
        return balls

    @feedback
    def is_ready(self) -> bool:
        return self.indexer_motors[-1].isFwdLimitSwitchClosed()
