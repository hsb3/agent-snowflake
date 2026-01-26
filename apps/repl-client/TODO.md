# Private Project TODO Notes

## Kanban

### **backlog**

- [ ] on startup check if server is accessible with available event loop
- [ ] next query for meta info to store in memory.  could borrow checkpointer or other types of mem caches if want; info to get: list asssistant; detail for assistants (max=?); threads (max=?); thread runs, ..

### **in progress**

## **completed**

---

## Developer Notes


use langgraph-sdk to connect to langgraph server to create two terminal-based clients:
 1. rich/console app
 2. texutal tui app

share significant amount of base classes/methods and functions

### rich/console repl planning
1. how are other similar projects structured?? see [other langgraph cli/repl research](./docs/spec/research/REPL_FILE_STRUCTURE_ANALYSIS.md)


### tui planning:
1. [tui user journeys](./docs/spec/research/tui-user-journeys.md)
2. [tui component inventory](./docs/spec/research/tui-component-inventory.md)



#### beginning with end in mind:
- based on user journeys, we need these interactive elements:
- here's what we already have:
- here's how we're going to style things:
- here's how we're going to make ui elements interact with
  - textual app
  - langgraph server\
  - \

----


### planning how to execute

**these both need to be udpated**

1. [repl product spec](./docs/spec/repl_spec.json)
2. [repl implementation tracker](./docs/spec/repl_components.jsonc)

both above in json format to eliminate ai verbosity. use pretty print and json dumps for more human-readable view
use pretty print



**reference info**
- [langraph sdk reference](./docs/spec/research/langgraph-sdk-reference.md)
- [textual app class](./docs/spec/research/textual-app-class.md)
- [textual app class exploration](../repl-client/scripts/explore_textual_app.py)
- [textual app class cheatsheet](./docs/spec/research/text-app-cheatsheet.md)
- [textual widget cheatsheet](./docs/spec/research/textual-widget-cheatsheet.md)
- or literally just copy [elia](https://github.com/darrenburns/elia)