#
# In Python, "privacy" depends on "consenting adults" levels of agreement - you can't force it.
# A single leading underscore means you're not supposed to access it "from the outside"
# Two leading underscores (w/o trailing underscores) carry the message even more forcefully...
# but, in the end, it still depends on social convention and consensus: Python's introspection is forceful enough
# that you can't handcuff every other programmer in the world to respect your wishes.
#
def my_function(name):
    print("This is my function : " + name)

def another_function(name):
    print("This is another function : " + name)

def _not_suppose_to_call_me():
    print("Don't call me!")

def __really_not_suppose_to_call_me():
    print("Really, don't call me!")

print("I'm a module")
_not_suppose_to_call_me()
__really_not_suppose_to_call_me()
