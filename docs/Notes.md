

This file just contains all notes that I don't really want in any of the official documentation.
The content in here may be old and obsolete.



Removed from README:
--------------------

This is my experimentation with creating a more powerful API.

I've previously created a basic `todoist` module, with basic examples on how to use the Todoist API,
including notes and discussions.

This is my attempt at making a more extensive CLI.

The goal is to have something where I can make a long list of actions, e.g.:

    $ todoist -filter <filter_name> -print "\nBEFORE RESCHEDULING:" -reschedule "today" -print "\nAFTER RESCHEDULING:"

Note how this has an order. It is more like `find` CLI than traditional ArgParser or Click CLI.
I therefore don't think we can create it with argparse or click, but it should be easy to roll manually.




Basic Todoist API usage, for reference:
---------------------------------------

```python
import todoist
api = todoist.TodoistAPI('<YOUR-API-KEY-HERE>')
api.sync()
```

Reading your token file, stored in e.g. `~/.todoist_token.txt`:

```python
import todoist
from pathlib import Path
token_file = Path("~").expanduser() / ".todoist_token.txt"
token = token_file.read_text().strip()
api = todoist.TodoistAPI(token)
res = api.sync()
```

Task items are stored in `api.state['items']`:

```python
import todoist; api = todoist.TodoistAPI('<YOUR-API-KEY-HERE>'); api.sync()

items = api.state['items']  # List of todoist.model.Item objects.
item = items[0]
# Data is stored in Item.data property:
print("{content}  (due: {due[date]})".format(**item.data))
# Data is mapped as a dict using __getitem__ and __setitem__:
item['id']
item['due']
```

To add or update items, you either use the item directly, or use the ItemsManager (`api.items`):

```python
import todoist; api = todoist.TodoistAPI('<YOUR-API-KEY-HERE>'); api.sync()

item = api.items.add("This is a newly added task", due={'date': '2019-09-01', 'string': 'yesterday', 'lang': 'en'})
api.commit()
item.close()  # equivalent to using api.items.close(item['id'])

```

In theory you can update item data as much as you would like, it doesn't make much difference on
the server, the only difference is your local data copy - which is persisted when writing the cache
to disk during `sync()` and `commit()`.

This means you can modify `item.data` as much as you would like.

However, in practice, it is probably better to use a dedicated `item._custom_data`
to store any "non-official", temporary runtime data.

Note that the `Item` class is not itself a dict (and does not inherit from dict).
It is also not readily serializable with `json.dumps(item)`. However, the `TodoistAPI`
class uses the `default` argument to `json.dumps(api.state)`, which is a function that
simply returns `obj.data` for any object.



Complex Filtering:
------------------

Regarding complex filtering operations with more than one expression,
e.g. "-filter (due_date_utc gt 2017-12-24 and due_date_utc lt 2017-12-13) or priority eq 1".

Why would we want to do this?
* The "and" is equivalent to applying two sequential filters.
* So it is only useful to implement "or",
* which is just a join of two separate queries.
* I really don't think it is worth the complexity to achieve this!

This probably requires a proper parser, e.g:
* recursive descent parser. ("The hard way")
* s-expression (sexp) parser in Python
* pyparsing
* PLY
* YACC / Bison / ANTLR

Which makes for rather complicated code:
* https://gist.github.com/adamnew123456/0f45c75c805aa371fa92 - Pratt-style parser, 700+ LOCs for a simple calculator.
* https://github.com/louisfisch/Mathematical-Expressions-Parser/

Although maybe this can be done easily with a parser generator based on parsing expression grammars (PEGs):
* https://github.com/orlandohill/waxeye
* https://github.com/scottfrazer/hermes

See also:
* Dragon Book
* Boost Spirit (C++)
* https://en.wikipedia.org/wiki/Operator-precedence_parser
* https://en.wikipedia.org/wiki/S-expression
*




Dealing with dates and times:
------------------------------



Note: Python datetime libraries:
* datetime stdlib
* maya - By Kenneth Reitz
* arrow (not to be confused with apache-arrow) - by Chris Smith.
* moment - port of moment.js


Python modules for *parsing* dates from strings:

* dateutil.parser
* dateparser
* parsedatetime
* django.utils.dateparse
*


Refs:

* https://stackabuse.com/converting-strings-to-datetime-in-python/
	* dateutil, maya, arrow,
* https://stackoverflow.com/questions/127803/how-do-i-parse-an-iso-8601-formatted-date
* https://blog.scrapinghub.com/2015/11/09/parse-natural-language-dates-with-dateparser


## Datetime objects and timezones:

There is a few pitfalls when working with timezones and datetime objects,
particularly the built-in datetime.datetime objects.
This is mostly because the built-in datetime objects have really poor support
(read: almost no support) for timezones.
The built-in datetime.datetime objects have a `.tzinfo` field.
But the objects don't behave as you would expect when invoking e.g. `.astimezone(tzone)`:

```python
import datetime, pytz
dt = datetime.datetime(2019, 9, 3, 12, 31, tzinfo=None)
pytz.timezone("Europe/Copenhagen").localize(dt)
```

Modules that provide well-behaving datetime objects:

* pytz
* dateutil - provides `dateutil.tz` and `dateutil.parser` modules.
* pendulum
* maya
* arrow
* delorean
* udatetime (performance focused).







