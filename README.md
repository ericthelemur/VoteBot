# VoteBot

Discord voting bot capable of standard polls, as found in many other bots; anonymous polls, where votes are hidden and totals are only displayed at the end; 
and STV (Single Transferable Vote) polls, where users rank their choices, which is combined to find your set of winning options. This all supports up to **256 options**, 
though due to Discord's message and API restrictions, large numbers of options are discouraged due to the time it will take to post the messages and add the reactions.

I plan to support other voting methods (including STV variants) in the future. Currently, the STV ruleset supported is taken from Scottish Local Elections. 
I also plan to improve handling of reaction counting, as multiple simultaneous votes can lead to some being ignored.



