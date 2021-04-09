# VoteBot

Discord voting bot capable of standard polls, as found in many other bots; anonymous polls, where votes are hidden and totals are only displayed at the end; 
and STV (Single Transferable Vote) polls, where users rank their choices, which is combined to find your set of winning options. This all supports up to **256 options**, 
though due to Discord's message and API restrictions, large numbers of options are discouraged due to the time it will take to post the messages and add the reactions.
This bot also supports limiting votes per user and a variable number of winners for STV. 

I plan to support other voting methods (including STV variants) in the future. Currently, the STV ruleset supported is taken from Scottish Local Elections. 
I also plan to improve handling of reaction counting, as multiple simultaneous votes can lead to some being ignored.


**Quick Poll Example**

![image](https://user-images.githubusercontent.com/8903016/114238390-6f770e80-997c-11eb-8176-cb1f3e0eb111.png)

**Anonymous Poll Example**

![image](https://user-images.githubusercontent.com/8903016/114238757-0d6ad900-997d-11eb-9bd8-85b2a89f2106.png)

![image](https://user-images.githubusercontent.com/8903016/114238819-21163f80-997d-11eb-826f-25d025159669.png)

**STV Poll Example**

![image](https://user-images.githubusercontent.com/8903016/114240445-6a678e80-997f-11eb-8a6a-5072b26d7a7c.png)

![image](https://user-images.githubusercontent.com/8903016/114240575-a3076800-997f-11eb-9239-4a25078fc9c6.png)
