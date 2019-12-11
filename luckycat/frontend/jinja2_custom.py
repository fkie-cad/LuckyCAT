COLORS = {'EXPLOITABLE': 'red',
          'PROBABLY_EXPLOITABLE': 'orange',
          'PROBABLY_NOT_EXPLOITABLE': 'green'}


def exploitable_color(s):
    if s is None:
        return 'black'
    s = s.upper()
    if s in COLORS:
        return COLORS[s]
    else:
        return 'black'


def map_signal_to_string(signal):
    if type(signal) is int:
        signal = str(signal)
    signal_mapping = {
        '129': 'SIGHUP(129)',
        '132': 'SIGILL(132)',
        '134': 'SIGABRT(134)',
        '136': 'SIGFPE(136)',
        '137': 'SIGKILL(137)',
        '139': 'SIGSEGV(139)',
        '140': 'SIGSYS(140)',
        '143': 'SIGTERM(143)',
        '146': 'SIGCONT/SIGSTOP/SIGCHILD(146)',
        '159': 'SIGSYS(159)'
    }
    if signal in signal_mapping:
        signal = signal_mapping[signal]
    return signal
