## Overview

```SQL Server```

All SQL queries, executions, etc. are ran on a local PostgreSQL server.  Connection information is stored on a hidden .ini file.
** **

## Battle Objects
```For the purposes of Sprocket Bot, anything that can be used to win a battle is counted as a "battle object."  This includes tanks, planes, boats, blimps, bunkers, etc.  A full list of these will be added eventually.```

Sprocket Bot stores all battle objects in a dedicated "battle object" table.  Campaigns can have many different types of battle objects, while contests are limited to just tanks.  Each battle object will include the following attached data:
**Server:** determines what server the battle object was registered into
**HostType:** determines the type of competition that the battle object was registered under (campaign or contest)
**Domain:** a multi-use term.  For contests, it determines the name of the contest that the tank was registered under.  For campaigns, it determines the faction that the battle object was registerd to.
**Class:** determines the type of battle object.  This can be defined as any valid vehicle class, such as a tank destroyer, blimp, airplane, heavy tank, etc.

Included in the table are a couple dozen additional properties about each vehicle.  Battle objects can be added through manual methods, or through the automated blueprint checkers installed for contests and campaigns.