import argparse


class ParseException(Exception): pass


# Edits ArgumentParser to throw exception with message instead of argparse's default handling, which printed to stderr and called sys.exit (raised SystemExit).
#       which is a neater way to forward the message to discord and catching SystemExit is potentially bad if I wanted to use it elsewhere functionality
class PollParser(argparse.ArgumentParser):
    def error(self, message):
        raise ParseException(self.format_usage() + f"\n{self.prog}: error: {message}\n")


# Creates the parser for a poll command, allowing limit and show options
poll_parser = PollParser(prog='!poll', description='Runs an anonymous poll of the given options. Use !close <Poll ID> to end this poll.')
poll_parser.add_argument("title", action="store", type=str, help="Title of the poll")
poll_parser.add_argument("-l", "--limit", dest="limit", action="store", type=int, default=0, help="Maximum amount of choices per user. 0 allows infinite")
# poll_parser.add_argument("-s", "--show", dest="hide", action="store_false", help="Hides reactions once counted", required=False)
opt_arg = poll_parser.add_argument("options", action="store", nargs="*", help="Options in the poll. At least 2 must be given.")

# Creates the parser for a poll command, allowing limit and show options
vis_poll_parser = PollParser(prog='!qpoll', description='Runs a quick poll. Votes are visible to all.')
vis_poll_parser.add_argument("title", action="store", type=str, help="Title of the poll")
vis_opt_arg = vis_poll_parser.add_argument("options", action="store", nargs="*", help="Options in the poll. If no options given, options of 'Yes' and 'No' are assumed.")

# Creates the parser for a poll command, allowing limit and show options
stv_parser = PollParser(prog='!stvpoll', description='Runs an STV poll. Use !close <Poll ID> to end this poll.')
stv_parser.add_argument("title", action="store", type=str, help="Title of the poll")
stv_win_arg = stv_parser.add_argument("-w", "--winners", dest="winners", action="store", type=int, default=1, help="Number of winners to select")
stv_parser.add_argument("-l", "--limit", dest="limit", action="store", type=int, default=0, help="Maximum amount of choices per user. 0 allows infinite. This options should probably not be used with STV.")
# poll_parser.add_argument("-s", "--show", dest="hide", action="store_false", help="Hides reactions once counted", required=False)
stv_opt_arg = stv_parser.add_argument("options", action="store", nargs="*", help="Options in the poll")


def run_parser(parser, options, extra_checks):
    try:  # Attempt to parse results
        args = parser.parse_args(options)
        extra_checks(args)

    except ParseException as e:
        return f"```{str(e)}```"
    except argparse.ArgumentError as e:
        return f"```{str(e)}```"
    return args
