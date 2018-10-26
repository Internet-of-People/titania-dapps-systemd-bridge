# titania-dapps-systemd-bridge has been [merged](https://github.com/libertaria-project/titania-os) to libertaria_project/titania-os repo

You can find the latest version of source code inside the [titania-os](https://github.com/libertaria-project/titania-os/tree/develop/meta-titania/recipes-titania/dapp) repo.

## dapp-systemd-bridge

Demonstrator for generating dApp Hub to FUSE filesystem bindings. Written in Python for prototyping, intended to be rendered in Rust at later time.

## Principle of operation

SystemD allows 'drop-in' configuration to be attached in snippets to the units it runs. There are several folders for this. We use the `/run` one (see systemd documentation for detailed paths), which is rendered online via FUSE by the running python script.

TODO: if it turns out per testing that systemd needs to write in `/run` drop-in folder, intercept the calls and memorize.

## Running

For demonstration, run as:
```
./dapp-systemd-bridge.py path/to/dapphub.json /mount/directory
```
