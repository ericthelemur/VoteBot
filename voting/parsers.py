import argparse


class ParseException(Exception): pass


# Edits ArgumentParser to throw exception with message instead of argparse's default handling, which printed to stderr and called sys.exit (raised SystemExit).
#       which is a neater way to forward the message to discord and catching SystemExit is potentially bad if I wanted to use it elsewhere functionality
class PollParser(argparse.ArgumentParser):
    def error(self, message):
        raise ParseException(self.format_usage() + f"\n{self.prog}: error: {message}\n")


# Creates the parser for a poll command, allowing limit and show options
poll_parser = PollParser(prog='+poll', description='Runs an anonymous poll of the given options. Use +close <Poll ID> to end this poll.')
poll_parser.add_argument("title", action="store", type=str, help="Title of the poll")
win_arg = poll_parser.add_argument("-w", "--winners", dest="winners", action="store", type=int, default=1, help="Number of winners to select")
lim_arg = poll_parser.add_argument("-l", "--limit", dest="limit", action="store", type=int, default=0, help="Maximum amount of choices per user. 0 allows infinite")
opt_arg = poll_parser.add_argument("options", action="store", nargs="*", help="Options in the poll. At least 2 must be given.")

# Creates the parser for a poll command, allowing limit and show options
vis_poll_parser = PollParser(prog='+vpoll', description='Runs a non-anonymous poll. Votes are visible to all. Use +close <Poll ID> to end this poll.')
vis_poll_parser.add_argument("title", action="store", type=str, help="Title of the poll")
vis_poll_parser.add_argument("-w", "--winners", dest="winners", action="store", type=int, default=1, help="Number of winners to select")
vis_poll_parser.add_argument("-l", "--limit", dest="limit", action="store", type=int, default=0, help="Maximum amount of choices per user. 0 allows infinite")
vis_poll_parser.add_argument("options", action="store", nargs="*", help="Options in the poll. At least 2 must be given.")

# Creates the parser for a poll command, allowing limit and show options
stv_parser = PollParser(prog='+stvpoll', description='Runs an STV poll. Use +close <Poll ID> to end this poll.')
stv_parser.add_argument("title", action="store", type=str, help="Title of the poll")
stv_parser.add_argument("-w", "--winners", dest="winners", action="store", type=int, default=1, help="Number of winners to select")
stv_parser.add_argument("-l", "--limit", dest="limit", action="store", type=int, default=0, help="Maximum amount of choices per user. 0 allows infinite. This options should probably not be used with STV.")
stv_parser.add_argument("options", action="store", nargs="*", help="Options in the poll")


def run_parser(parser, options, extra_checks):
    try:  # Attempt to parse results
        args = parser.parse_args(options)
        extra_checks(args)

    except ParseException as e:
        return f"```{str(e)}```"
    except argparse.ArgumentError as e:
        return f"```{str(e)}```"
    return args
