import signal


async def _signal_handler(signum, frame, SIGINT=None):
    match (signum):
        case 2:
            if SIGINT:
                SIGINT()
                # exit(0)
            else:
                print("nothing happeneds")
                exit(0)


async def init_signals(SIGINT, loop):
    # signal.signal(
    #     signal.SIGINT,
    #     lambda signum, frame: _signal_handler(
    #         signum=signum, frame=frame, SIGINT=SIGINT
    #     ),
    # )

    loop.add_signal_handler(
        signal.SIGINT,
        lambda signum, frame: _signal_handler(
            signum=signum, frame=frame, SIGINT=SIGINT
        ),
    )
