# Linear CLI

[![asciicast](https://asciinema.org/a/619030.png)](https://asciinema.org/a/619030)

## Install

Requires `LINEAR_API_KEY`
https://linear.app/tibber/settings/api

```bash
pipx install git+https://github.com/kaar/linear-cli
```

## Usage

```bash
li issue list
li issue view TRA-383
li team
li team --state backlog
```

## Development

See [Makefile](./Makefile)

## Documentation

* [Working with the GraphQL API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
* [Schema](https://github.com/linear/linear/blob/master/packages/sdk/src/schema.graphql)
* [GraphQL CLI](https://www.graphql-cli.com/introduction/)
* [Linear API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
